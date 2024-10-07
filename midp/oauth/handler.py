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
from midp.common.token_manager import UserTokenManager, TokenSet, TokenGenerationError
from midp.common.web_helpers import restore_session
from midp.iam.models import PredefinedScope, IAMPolicySubject
from midp.models import GrantType
from midp.oauth.access_evaluator import AccessEvaluator
from midp.oauth.models import DeviceVerificationCodeResponse, TokenExchangeResponse, \
    DeviceAuthorizationRequest, DeviceAuthorizationResponse, LoginResponse
from midp.oauth.user_authenticator import UserAuthenticator, AuthenticationResult, AuthenticationError
from midp.static_info import verification_ttl

oauth_router = APIRouter(
    prefix=r'/oauth',
    tags=['oauth'],
    responses={
        401: dict(error='not-authenticated'),
        403: dict(error='access-denied'),
        404: dict(error='not-found'),
        405: dict(error='method-not-allowed'),
    },
)


@oauth_router.post(r'/login')
async def sign_in(request: Request,
                  response: Response,
                  username: Annotated[str, Form()],
                  password: Annotated[str, Form()],
                  session: Annotated[Session, Depends(restore_session)]) -> LoginResponse:
    if request.headers.get("accept") == 'application/json':
        session_user = session.data.get('user')

        response_body = LoginResponse(already_exists=session_user is not None)

        if not session_user:
            user_auth: UserAuthenticator = container.get(UserAuthenticator)

            try:
                result: AuthenticationResult = await asyncio.to_thread(user_auth.authenticate,
                                                                       username,
                                                                       password)

                session.data['user'] = result.principle.model_dump(mode='python')
                session.data['access_token'] = result.access_token
                session.data['refresh_token'] = result.refresh_token
                await asyncio.to_thread(session.save)

                response.set_cookie('sid', session.encrypted_id)
                response_body.session_id = session.id
                response_body.principle = result.principle
            except AuthenticationError as e:
                response.status_code = 400
                response_body.error = e.code
                response_body.error_description = e.description

        return response_body
    else:
        raise HTTPException(400)


@oauth_router.post(r'/session')
async def check_session_authorization(response: Response,
                  session: Annotated[Session, Depends(restore_session)]):
    session_user = session.data.get('user')

    if session_user:
        return session_user
    else:
        response.status_code = 401
        return None


@oauth_router.post(r'/device')
async def initiate_device_authorization(client_id: Annotated[str, Form()],
                                        scope: Annotated[str, Form()],
                                        request: Request,
                                        resource: Optional[str] = None,
                                        ):
    access_evaluator: AccessEvaluator = container.get(AccessEvaluator)

    oauth_base_url = urljoin(str(request.base_url), 'oauth')
    resource_url = resource

    requested_scopes = re.split(r'\s+', scope)

    known_minimum_scopes = {PredefinedScope.OPENID.name, PredefinedScope.OFFLINE_ACCESS.name}.intersection(
        requested_scopes)
    if not known_minimum_scopes:
        return DeviceVerificationCodeResponse(error='invalid_scope')

    error_code = await access_evaluator.check_if_client_is_allowed(client_id, GrantType.DEVICE_CODE)
    if error_code:
        return DeviceVerificationCodeResponse(error=error_code)

    device_code = str(uuid4())
    hasher = hashlib.new('sha1')
    hasher.update(device_code.encode())
    user_code = hasher.hexdigest()[:8].upper()

    key_storage: KeyStorage = container.get(KeyStorage)
    expiry_timestamp = time() + verification_ttl

    await asyncio.gather(
        key_storage.async_set(
            f'user-code:{user_code}/device-code',
            device_code,
            expiry_timestamp
        ),
        key_storage.async_set(
            f'device-code:{device_code}/state',
            'authorization_pending',
            expiry_timestamp
        ),
        key_storage.async_set(
            f'device-code:{device_code}/user-code',
            user_code,
            expiry_timestamp
        ),
        key_storage.async_set(
            f'device-code:{device_code}/info',
            {
                'sub': 'user_a',
                'scopes': requested_scopes,
                'resource_url': resource_url,
            },
            expiry_timestamp
        ),
    )

    return DeviceVerificationCodeResponse.make(
        base_url=oauth_base_url,
        device_code=device_code,
        user_code=user_code,
        expires_in=verification_ttl,
    )


@oauth_router.post(r'/token')
async def exchange_token(client_id: Annotated[str, Form()],
                         grant_type: Annotated[str, Form()],
                         device_code: Annotated[str, Form()],
                         request: Request,
                         response: Response) -> TokenExchangeResponse:
    access_evaluator: AccessEvaluator = container.get(AccessEvaluator)
    user_token_manager: UserTokenManager = container.get(UserTokenManager)

    if grant_type == GrantType.DEVICE_CODE:
        await access_evaluator.check_if_client_is_allowed(client_id, GrantType.DEVICE_CODE)

        key_storage: KeyStorage = container.get(KeyStorage)
        verification_state = await key_storage.async_get(f'device-code:{device_code}/state')

        if verification_state == 'ok':
            verified_info = await key_storage.async_get(f'device-code:{device_code}/info')
            resource_url = verified_info['resource_url']
            subject = verified_info['sub']
            requested_scopes = verified_info['scopes']
            try:
                token_set: TokenSet = await asyncio.to_thread(user_token_manager.generate,
                                                              IAMPolicySubject(subject=subject, kind='user'),
                                                              resource_url,
                                                              requested_scopes)
                return TokenExchangeResponse(access_token=token_set.access_token,
                                             expires_in=token_set.access_claims['exp'] - time(),
                                             refresh_token=token_set.refresh_token)
            except TokenGenerationError as e:
                return TokenExchangeResponse(error=e.args[0])
        else:
            response.status_code = 400
            return TokenExchangeResponse(error=verification_state or 'unexpected_state')
    else:
        raise HTTPException(501)


@oauth_router.post(r'/device-activation')
async def confirm_for_device_activation(data: DeviceAuthorizationRequest,
                                        response: Response) -> DeviceAuthorizationResponse:
    # TODO Enforce user authentication

    key_storage: KeyStorage = container.get(KeyStorage)

    device_code: str = await key_storage.async_get(f'user-code:{data.user_code}/device-code')
    if not device_code:
        response.status_code = 400
        return DeviceAuthorizationResponse(error='expired_token', error_description='device_code.not_found')

    expected_user_code: str = await key_storage.async_get(f'device-code:{device_code}/user-code')
    if not expected_user_code:
        response.status_code = 400
        return DeviceAuthorizationResponse(error='expired_token', error_description='stored-user-code.not_found')

    if data.user_code == expected_user_code:
        await key_storage.async_set(f'device-code:{device_code}/state',
                                    'ok' if data.authorized else 'access_denied',
                                    time() + verification_ttl)
        return DeviceAuthorizationResponse(device_code=device_code, authorized=data.authorized)
    else:
        # Not updating the state
        response.status_code = 403
        return DeviceAuthorizationResponse(error='wrong_user_code')
