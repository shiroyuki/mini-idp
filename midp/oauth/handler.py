import asyncio
import hashlib
import re
from time import time
from typing import Annotated, Optional
from urllib.parse import urljoin
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Form, Depends
from imagination import container
from starlette.requests import Request
from starlette.responses import Response

from midp.common.key_storage import KeyStorage
from midp.common.session_manager import Session
from midp.common.token_manager import RealmTokenManager, TokenSet, RealmTokenGenerationError
from midp.common.web_helpers import respond_html, get_basic_template_variables, restore_session, web_path_get_realm
from midp.iam.dao.realm import RealmDao
from midp.iam.models import OpenIDConfiguration, GrantType, PredefinedScope, IAMPolicySubject, Realm
from midp.oauth.access_evaluator import AccessEvaluator
from midp.oauth.models import DeviceVerificationCodeResponse, TokenExchangeResponse, \
    DeviceAuthorizationRequest, DeviceAuthorizationResponse
from midp.oauth.user_authenticator import UserAuthenticator, AuthenticationResult, AuthenticationError
from midp.static_info import verification_ttl

oauth_router = APIRouter(
    prefix=r'/realms',
    tags=['oauth'],
    responses={
        401: dict(error='not-authenticated'),
        403: dict(error='access-denied'),
        404: dict(error='not-found'),
        405: dict(error='method-not-allowed'),
    },
)


@oauth_router.get(r'/{realm_id}/login')
async def prompt_for_signing_in(request: Request,
                                realm_id: str,
                                session: Annotated[Session, Depends(restore_session)],
                                realm: Annotated[Realm, Depends(web_path_get_realm)]):
    session_user = session.data.get('user')

    context = get_basic_template_variables(request)
    context.update({'realm_id': realm.name, 'session_user': session_user})

    response = respond_html('realm_login.html', context)
    response.set_cookie('sid', session.encrypted_id)

    return response


@oauth_router.post(r'/{realm_id}/login')
async def sign_in(request: Request,
                  realm_id: str,
                  username: Annotated[str, Form()],
                  password: Annotated[str, Form()],
                  session: Annotated[Session, Depends(restore_session)],
                  realm: Annotated[Realm, Depends(web_path_get_realm)]):
    if request.headers.get("accept") == 'application/json':
        session_user = session.data.get('user')

        response_body = {
            'error': None,
            'error_description': None,
            'session_id': session.id,
            'user': session_user,
            'already_exists': session_user is not None,
        }

        print(realm)

        if not session_user:
            user_auth: UserAuthenticator = container.get(UserAuthenticator)

            try:
                result: AuthenticationResult = await asyncio.to_thread(user_auth.authenticate,
                                                                       username,
                                                                       password,
                                                                       realm=realm)

                session.data['realm_user'] = result.principle.model_dump(mode='python')
                session.data['realm_access_token'] = result.access_token
                session.data['realm_refresh_token'] = result.refresh_token
                await asyncio.to_thread(session.save)

                response_body['principle'] = result.principle
            except AuthenticationError as e:
                response_body['error'] = e.code
                response_body['error_description'] = e.description

        return response_body
    else:
        raise HTTPException(400)


@oauth_router.get(r'/{realm_id}/.well-known/openid-configuration', response_model_exclude_defaults=True)
async def get_openid_configuration(realm_id: str, request: Request) -> OpenIDConfiguration:
    base_url = str(request.base_url)

    realm_dao: RealmDao = container.get(RealmDao)
    realm = await asyncio.to_thread(realm_dao.select_one, 'id = :id OR name = :id', dict(id=realm_id))
    if realm:
        return OpenIDConfiguration.make(base_url, realm)
    else:
        raise HTTPException(404)


@oauth_router.post(r'/{realm_id}/device')
async def initiate_device_authorization(realm_id: str,
                                        client_id: Annotated[str, Form()],
                                        scope: Annotated[str, Form()],
                                        request: Request,
                                        resource: Optional[str] = None,
                                        ):
    access_evaluator: AccessEvaluator = container.get(AccessEvaluator)

    realm_base_url = urljoin(str(request.base_url), f'/realms/{realm_id}/')
    resource_url = resource or realm_base_url

    requested_scopes = re.split(r'\s+', scope)

    known_minimum_scopes = {PredefinedScope.OPENID.name, PredefinedScope.OFFLINE_ACCESS.name}.intersection(
        requested_scopes)
    if not known_minimum_scopes:
        return DeviceVerificationCodeResponse(error='invalid_scope')

    error_code = await access_evaluator.check_if_client_is_allowed(realm_id, client_id, GrantType.DEVICE_CODE)
    if error_code:
        return DeviceVerificationCodeResponse(error=error_code)

    device_code = str(uuid4())
    hasher = hashlib.new('sha1')
    hasher.update(device_code.encode())
    user_code = hasher.hexdigest()[:8].upper()

    key_storage: KeyStorage = container.get(KeyStorage)
    realm_kv = key_storage.realm(realm_id)
    expiry_timestamp = time() + verification_ttl

    await realm_kv.async_set(f'user-code:{user_code}/device-code',
                             device_code,
                             expiry_timestamp)
    await realm_kv.async_set(f'device-code:{device_code}/state',
                             'authorization_pending',
                             expiry_timestamp)
    await realm_kv.async_set(f'device-code:{device_code}/user-code',
                             user_code,
                             expiry_timestamp)
    await realm_kv.async_set(f'device-code:{device_code}/info',
                             {
                                 'sub': 'user_a',
                                 'scopes': requested_scopes,
                                 'resource_url': resource_url,
                             },
                             expiry_timestamp)

    return DeviceVerificationCodeResponse.make(
        base_url=realm_base_url,
        device_code=device_code,
        user_code=user_code,
        expires_in=verification_ttl,
    )


@oauth_router.post(r'/{realm_id}/token')
async def exchange_token(realm_id: str,
                         client_id: Annotated[str, Form()],
                         grant_type: Annotated[str, Form()],
                         device_code: Annotated[str, Form()],
                         request: Request,
                         response: Response) -> TokenExchangeResponse:
    access_evaluator: AccessEvaluator = container.get(AccessEvaluator)
    realm_token_manager: RealmTokenManager = container.get(RealmTokenManager)
    realm_dao: RealmDao = container.get(RealmDao)

    if grant_type == GrantType.DEVICE_CODE:
        await access_evaluator.check_if_client_is_allowed(realm_id, client_id, GrantType.DEVICE_CODE)

        realm = realm_dao.get(realm_id)

        key_storage: KeyStorage = container.get(KeyStorage)
        realm_kv = key_storage.realm(realm.id)
        verification_state = await realm_kv.async_get(f'device-code:{device_code}/state')

        if verification_state == 'ok':
            verified_info = await realm_kv.async_get(f'device-code:{device_code}/info')
            resource_url = verified_info['resource_url']
            subject = verified_info['sub']
            requested_scopes = verified_info['scopes']
            try:
                token_set: TokenSet = await asyncio.to_thread(realm_token_manager.generate,
                                                              realm,
                                                              IAMPolicySubject(subject=subject, kind='user'),
                                                              resource_url,
                                                              requested_scopes)
                return TokenExchangeResponse(access_token=token_set.access_token,
                                             expires_in=token_set.access_claims['exp'] - time(),
                                             refresh_token=token_set.refresh_token)
            except RealmTokenGenerationError as e:
                return TokenExchangeResponse(error=e.args[0])
        else:
            response.status_code = 400
            return TokenExchangeResponse(error=verification_state or 'unexpected_state')
    else:
        raise HTTPException(501)


@oauth_router.post(r'/{realm_id}/device-activation')
async def confirm_for_device_activation(realm_id: str,
                                        data: DeviceAuthorizationRequest,
                                        response: Response) -> DeviceAuthorizationResponse:
    # TODO Enforce user authentication

    key_storage: KeyStorage = container.get(KeyStorage)
    realm_kv = key_storage.realm(realm_id)

    device_code: str = await realm_kv.async_get(f'user-code:{data.user_code}/device-code')
    if not device_code:
        response.status_code = 400
        return DeviceAuthorizationResponse(error='expired_token', error_description='device_code.not_found')

    expected_user_code: str = await realm_kv.async_get(f'device-code:{device_code}/user-code')
    if not expected_user_code:
        response.status_code = 400
        return DeviceAuthorizationResponse(error='expired_token', error_description='stored-user-code.not_found')

    if data.user_code == expected_user_code:
        await realm_kv.async_set(f'device-code:{device_code}/state',
                                 'ok' if data.authorized else 'access_denied',
                                 time() + verification_ttl)
        return DeviceAuthorizationResponse(device_code=device_code, authorized=data.authorized)
    else:
        # Not updating the state
        response.status_code = 403
        return DeviceAuthorizationResponse(error='wrong_user_code')
