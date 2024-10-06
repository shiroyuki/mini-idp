from typing import Optional, List, Set, Union
from urllib.parse import urljoin

from pydantic import BaseModel, ConfigDict
from uvicorn import Config

from midp.iam.models import IAMUserReadOnly
from midp.models import Realm
from midp.root.models import RootUserReadOnly
from midp.static_info import verification_ttl


class GenericOAuthResponse(BaseModel):
    model_config = ConfigDict(extra='ignore')

    error: Optional[str] = None
    error_description: Optional[str] = None


class LoginResponse(GenericOAuthResponse):
    principle: Union[RootUserReadOnly, IAMUserReadOnly, None] = None
    session_id: Optional[str] = None
    already_exists: Optional[bool] = None


class DeviceVerificationCodeResponse(GenericOAuthResponse):
    device_code: Optional[str] = None
    user_code: Optional[str] = None
    verification_uri: Optional[str] = None
    verification_uri_complete: Optional[str] = None
    expires_in: Optional[int] = None
    interval: Optional[int] = None

    @classmethod
    def make(cls,
             base_url: str,
             device_code: str,
             user_code: str,
             expires_in: int = verification_ttl,
             check_interval: int = 5):
        if not base_url.endswith('/'):
            base_url += '/'

        return cls(
            device_code=device_code,
            user_code=user_code,
            verification_uri=urljoin(base_url, 'device-activation'),
            verification_uri_complete=urljoin(base_url, 'device-activation') + f'?user_code={user_code}',
            expires_in=expires_in,
            interval=check_interval,
        )


class TokenExchangeResponse(GenericOAuthResponse):
    access_token: Optional[str] = None
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None


class DeviceAuthorizationRequest(BaseModel):
    user_code: str
    authorized: bool


class DeviceAuthorizationResponse(GenericOAuthResponse):
    device_code: Optional[str] = None
    authorized: Optional[bool] = None


class OpenIDConfiguration(BaseModel):
    issuer: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    device_authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    introspection_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    end_session_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    grant_types_supported: Optional[List[str]] = None
    response_types_supported: Optional[List[str]] = None
    scopes_supported: Optional[List[str]] = None

    @classmethod
    def make(cls, base_url: str, realm: Realm):
        realm_base_url = urljoin(base_url, f'realms/{realm.name}/')

        scopes: Set[str] = set()
        for policy in realm.policies:
            scopes.update(policy.scopes)

        return cls(
            issuer=realm_base_url,
            authorization_endpoint=None,  # urljoin(realm_base_url, f'auth'),
            device_authorization_endpoint=urljoin(realm_base_url, f'device'),
            token_endpoint=urljoin(realm_base_url, f'token'),
            introspection_endpoint=None,  # urljoin(realm_base_url, f'introspection'),
            userinfo_endpoint=None,  # urljoin(realm_base_url, f'userinfo'),
            end_session_endpoint=None,  # urljoin(realm_base_url, f'logout'),
            jwks_uri=None,  # urljoin(realm_base_url, f'certs'),
            grant_types_supported=sorted({policy.grant_type for policy in realm.policies}),
            response_types_supported=sorted({policy.response_type for policy in realm.policies}),
            scopes_supported=sorted(scopes),
        )
