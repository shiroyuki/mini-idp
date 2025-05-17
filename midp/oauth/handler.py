import asyncio
import hashlib
import re
from math import floor
from time import time
from typing import Annotated, Optional, Union
from urllib.parse import urljoin
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Form, Depends, Query
from imagination import container
from pydantic import BaseModel
from sqlalchemy.sql.functions import session_user
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse

from midp.common.key_storage import KeyStorage, Entry
from midp.common.session_manager import Session
from midp.common.token_manager import TokenManager, TokenSet, TokenGenerationError
from midp.common.web_helpers import restore_session
from midp.iam.models import PredefinedScope, IAMPolicySubject, GrantType
from midp.log_factory import midp_logger
from midp.oauth.access_evaluator import ClientAuthenticator, ClientAuthenticationError
from midp.oauth.models import DeviceVerificationCodeResponse, TokenExchangeResponse, \
    DeviceAuthorizationRequest, DeviceAuthorizationResponse, LoginResponse
from midp.oauth.user_authenticator import UserAuthenticator, AuthenticationResult, AuthenticationError
from midp.static_info import VERIFICATION_TTL

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

SERVICE_TO_SERVICE_URI_PREFIX = r'client://'


@oauth_router.post(r'/login')
async def sign_in(request: Request,
                  response: Response,
                  username: Annotated[str, Form()],
                  password: Annotated[str, Form()],
                  session: Annotated[Session, Depends(restore_session)]) -> LoginResponse:
    # TODO Prevent the brute-force/DOS attack with implementing the rate limit.
    if request.headers.get("accept") == 'application/json':
        session_user = None  # session.data.get('user')

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
                response_body.access_token = result.access_token
                response_body.refresh_token = result.refresh_token
            except ClientAuthenticationError as e:
                response.status_code = 400
                response_body.error = e.code
                response_body.error_description = e.description

        return response_body
    else:
        raise HTTPException(400)


@oauth_router.get(r'/logout')
async def sign_out(session: Annotated[Session, Depends(restore_session)]):
    response = Response(status_code=200)

    if 'user' in session.data:
        del session.data['user']
        session.save()

        response.delete_cookie('sid')

        # TODO Deactivate the access and refresh tokens.

    return response


@oauth_router.get(r'/me/token')
async def check_token(response: Response, session: Annotated[Session, Depends(restore_session)]):
    session_user = session.data.get('user')

    if session_user:
        return session_user
    else:
        response.status_code = 401
        return None


@oauth_router.get(r'/me/session')
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
                                        session: Annotated[Session, Depends(restore_session)],
                                        scope: Annotated[str, Form()],
                                        request: Request,
                                        response: Response,
                                        resource: Optional[str] = None,
                                        ):
    access_evaluator: ClientAuthenticator = container.get(ClientAuthenticator)

    oauth_base_url = urljoin(str(request.base_url), 'oauth')
    resource_url = resource

    requested_scopes = re.split(r'\s+', scope)

    known_minimum_scopes = {
        PredefinedScope.OPENID.name,
        PredefinedScope.OFFLINE_ACCESS.name
    }.intersection(requested_scopes)
    if not known_minimum_scopes:
        response.status_code = 400
        return DeviceVerificationCodeResponse(error='invalid_scope')

    try:
        await access_evaluator.authenticate(client_id=client_id, grant_type=GrantType.DEVICE_CODE)
    except ClientAuthenticationError as e:
        response.status_code = 400
        return DeviceVerificationCodeResponse(error=e.reason)

    device_code = str(uuid4())
    hasher = hashlib.new('sha1')
    hasher.update(device_code.encode())
    user_code = hasher.hexdigest()[:8].upper()

    key_storage: KeyStorage = container.get(KeyStorage)
    expiry_timestamp = floor(time() + VERIFICATION_TTL)

    await asyncio.to_thread(
        key_storage.batch_set,
        Entry(
            key=f'user-code:{user_code}/device-code',
            value=device_code,
            expiry_timestamp=expiry_timestamp,
        ),
        Entry(
            key=f'device-code:{device_code}/state',
            value='authorization_pending',
            expiry_timestamp=expiry_timestamp,
        ),
        Entry(
            key=f'device-code:{device_code}/user-code',
            value=user_code,
            expiry_timestamp=expiry_timestamp,
        ),
        Entry(
            key=f'device-code:{device_code}/info',
            value={
                'sub': 'user_a',
                'scopes': requested_scopes,
                'resource_url': resource_url,
            },
            expiry_timestamp=expiry_timestamp,
        ),
    )

    return DeviceVerificationCodeResponse.make(
        base_url=oauth_base_url,
        device_code=device_code,
        user_code=user_code,
        expires_in=VERIFICATION_TTL,
    )


class TokenExchangeRequest(BaseModel):
    client_id: str
    client_secret: Optional[str] = None
    grant_type: str
    device_code: Optional[str] = None
    audience: Optional[str] = None  # non-standard
    resource: Optional[str] = None  # non-standard
    scope: str = None


@oauth_router.post(r'/token')
async def exchange_token(data: Annotated[TokenExchangeRequest, Form()],
                         request: Request,
                         response: Response) -> TokenExchangeResponse:
    # Based on https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow

    log = midp_logger('/oauth/token')

    access_evaluator: ClientAuthenticator = container.get(ClientAuthenticator)
    token_manager: TokenManager = container.get(TokenManager)

    # Authenticate the client.
    try:
        client = await access_evaluator.authenticate(
            client_id=data.client_id,
            client_secret=data.client_secret,
            grant_type=data.grant_type,
        )
    except ClientAuthenticationError as e:
        log.warning(f"Detected token exchange attempt with Client/{data.client_id} (REJECTED: {e.reason})")
        response.status_code = 401
        return TokenExchangeResponse(error=e.reason)

    if data.grant_type == GrantType.CLIENT_CREDENTIALS:
        ######################################
        # Handle the client credentials flow #
        ######################################
        resource_url = data.resource or data.audience
        iam_policy_subject = IAMPolicySubject(subject=client.name, kind="client")

        try:
            token_set: TokenSet = token_manager.create_token_set(
                subject=iam_policy_subject,
                resource_url=resource_url,
                requested_scopes=re.split(r'\s+', data.scope) if data.scope else [],
            )
            return TokenExchangeResponse(access_token=token_set.access_token,
                                         expires_in=floor(token_set.access_claims['exp'] - time()),
                                         refresh_token=token_set.refresh_token)
        except TokenGenerationError as e:
            response.status_code = 401
            return TokenExchangeResponse(error=e.args[0])
    elif data.grant_type == GrantType.DEVICE_CODE:
        ###############################
        # Handle the device code flow #
        ###############################
        key_storage: KeyStorage = container.get(KeyStorage)
        verification_state = await key_storage.async_get(f'device-code:{data.device_code}/state')

        if verification_state == 'ok':
            verified_info = await key_storage.async_get(f'device-code:{data.device_code}/info')
            resource_url = verified_info['resource_url']
            subject: str = verified_info['sub']
            requested_scopes = verified_info['scopes']

            if subject.startswith(SERVICE_TO_SERVICE_URI_PREFIX):
                # FIXME This part does not seem to be used anywhere. REMOVE this.
                iam_policy_subject = IAMPolicySubject(subject=subject[len(SERVICE_TO_SERVICE_URI_PREFIX):],
                                                      kind='service')
            else:
                iam_policy_subject = IAMPolicySubject(subject=subject,
                                                      kind='user')

            try:
                token_set: TokenSet = await asyncio.to_thread(token_manager.create_token_set,
                                                              iam_policy_subject,
                                                              resource_url,
                                                              requested_scopes)
                return TokenExchangeResponse(access_token=token_set.access_token,
                                             expires_in=floor(token_set.access_claims['exp'] - time()),
                                             refresh_token=token_set.refresh_token)
            except TokenGenerationError as e:
                response.status_code = 401
                return TokenExchangeResponse(error=e.args[0])
        else:
            response.status_code = 400
            return TokenExchangeResponse(error=verification_state or 'unexpected_state')
    else:
        raise HTTPException(501)


@oauth_router.get(r'/device-activation')
def redirect_to_device_code_confirmation_page(request: Request, user_code: Annotated[Optional[str], Query()]):
    return RedirectResponse(f'/#/oauth/device-activation?user_code={user_code}&origin={request.url}')


@oauth_router.post(r'/device-activation')
async def confirm_for_device_activation(request: Request,
                                        session: Annotated[Session, Depends(restore_session)],
                                        data: DeviceAuthorizationRequest,
                                        response: Response):
    log = midp_logger('initiate_device_authorization')

    json_activation = request.headers.get('accept') == 'application/json'

    if session.is_unset:
        return (
            DeviceAuthorizationResponse(error='not_authenticated', error_description='invalid_session')
            if json_activation
            else RedirectResponse(f'/#/login?next_url=/oauth/device-activation')
        )

    key_storage: KeyStorage = container.get(KeyStorage)

    device_code: str = await key_storage.async_get(f'user-code:{data.user_code}/device-code')
    if not device_code:
        response.status_code = 400
        return (
            DeviceAuthorizationResponse(error='expired_token', error_description='device_code.not_found')
            if json_activation
            else RedirectResponse(f'/#/error?code=expired_token&description=device_code.not_found')
        )

    expected_user_code: str = await key_storage.async_get(f'device-code:{device_code}/user-code')
    if not expected_user_code:
        response.status_code = 400
        return (
            DeviceAuthorizationResponse(error='expired_token', error_description='stored-user-code.not_found')
            if json_activation
            else RedirectResponse(f'/#/error?code=expired_token&description=stored-user-code.not_found')
        )

    if data.user_code == expected_user_code:
        await key_storage.async_set(f'device-code:{device_code}/state',
                                    'ok' if data.authorized else 'access_denied',
                                    time() + VERIFICATION_TTL)
        return DeviceAuthorizationResponse(device_code=device_code, authorized=data.authorized)
    else:
        # Not updating the state
        response.status_code = 403
        return (
            DeviceAuthorizationResponse(error='wrong_user_code')
            if json_activation
            else RedirectResponse(f'/#/error?code=wrong_user_code')
        )
