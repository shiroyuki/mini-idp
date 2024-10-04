from typing import Optional
from urllib.parse import urljoin

from pydantic import BaseModel, ConfigDict

from midp.static_info import verification_ttl


class GenericOAuthResponse(BaseModel):
    model_config = ConfigDict(extra='ignore')

    error: Optional[str] = None
    error_description: Optional[str] = None


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
