from typing import Optional, List, Set, Union
from urllib.parse import urljoin

from pydantic import BaseModel, ConfigDict

from midp.iam.models import IAMUserReadOnly
from midp.static_info import VERIFICATION_TTL


class GenericOAuthResponse(BaseModel):
    model_config = ConfigDict(extra='ignore')

    error: Optional[str] = None
    error_description: Optional[str] = None


class LoginResponse(GenericOAuthResponse):
    principle: Optional[IAMUserReadOnly] = None
    session_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
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
             expires_in: int = VERIFICATION_TTL,
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
    token_type: Optional[str] = None
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
    def make(cls, base_url: str):
        return cls(
            issuer=base_url,
            authorization_endpoint=None,  # urljoin(realm_base_url, f'auth'),
            device_authorization_endpoint=urljoin(base_url, f'device'),
            token_endpoint=urljoin(base_url, f'token'),
            introspection_endpoint=None,  # urljoin(realm_base_url, f'introspection'),
            userinfo_endpoint=None,  # urljoin(realm_base_url, f'userinfo'),
            end_session_endpoint=None,  # urljoin(realm_base_url, f'logout'),
            jwks_uri=None,  # urljoin(realm_base_url, f'certs'),
        )
