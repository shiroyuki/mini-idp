import sys
from time import sleep, time
from typing import TypeVar, Generic, List, Type, Dict, Any, Optional
from urllib.parse import urljoin, quote_plus

import requests
from requests import Response

from midp.config import MainConfig
from midp.log_factory import get_logger_for, get_logger_for_object
from midp.iam.models import PredefinedScope
from midp.models import Realm, GrantType
from midp.oauth.models import DeviceVerificationCodeResponse, TokenExchangeResponse, OpenIDConfiguration

T = TypeVar('T')


def _assert_response(response: Response, status_codes: List[int]):
    assert response.status_code in status_codes, f'HTTP {response.status_code}: {response.text}'


class RestAPIClient(Generic[T]):
    def __init__(self, base_url: str, model_class: Type[T]):
        self._log = get_logger_for(f'REST:{model_class.__name__}')
        self._base_url = base_url
        self._model_class = model_class

        if not self._base_url.endswith(r'/'):
            self._base_url += '/'

    def list(self) -> List[T]:
        response = requests.get(self._base_url)

        _assert_response(response, [200])

        return [self._model_class(**i) for i in response.json()]

    def delete(self, id: str) -> bool:
        response = requests.delete(urljoin(self._base_url, id))
        status_code = response.status_code

        _assert_response(response, [200, 410])

        return status_code == 200


class DeviceAuthorizationTerminated(RuntimeError):
    pass


class DeviceAccessDenied(DeviceAuthorizationTerminated):
    pass


class DeviceInvalidClientError(DeviceAuthorizationTerminated):
    pass


_DEVICE_CODE_TERMINATION_ERROR_CODES: Dict[str, Type[Exception]] = {
    'invalid_request': DeviceAuthorizationTerminated,
    'invalid_client': DeviceInvalidClientError,
    'invalid_grant': DeviceInvalidClientError,
    'unauthorized_client': DeviceInvalidClientError,
    'unsupported_grant_type': DeviceInvalidClientError,
    'invalid_scope': DeviceInvalidClientError,
    'access_denied': DeviceAccessDenied,
    'expired_token': DeviceAuthorizationTerminated,
    # Non-standard Code: Microsoft's equivalent of "access_denied"
    'authorization_declined': DeviceAccessDenied,
}


class ClientOutput:
    def write(self, event: str, template: str, context: Dict[str, Any]):
        sys.stderr.write(template.format(**context) + '\n')


class RealmOAuthClient:
    def __init__(self, name: str, base_url: str, output: Optional[ClientOutput] = None):
        self._log = get_logger_for(f'Realm:{name}')
        self._name = name
        self._base_url = base_url
        self._output = output

        if not self._base_url.endswith(r'/'):
            self._base_url += '/'

    def get_openid_configuration(self) -> OpenIDConfiguration:
        response = requests.get(urljoin(self._base_url, '.well-known/openid-configuration'))

        _assert_response(response, [200])

        return OpenIDConfiguration(**response.json())

    def initiate_device_code(self, client_id: str, resource_url: Optional[str] = None):
        query_string = ''
        if resource_url:
            query_string = f'?resource={quote_plus(resource_url)}'

        verification_code_response = requests.post(urljoin(self._base_url, 'device') + query_string,
                                                   data=dict(client_id=client_id,
                                                             scope=' '.join([PredefinedScope.OPENID.name,
                                                                             PredefinedScope.PROFILE.name,
                                                                             PredefinedScope.OFFLINE_ACCESS.name]))
                                                   )

        _assert_response(verification_code_response, [200])

        verification = DeviceVerificationCodeResponse(**verification_code_response.json())

        start_time = time()
        verification_interval = verification.interval

        if verification.error:
            if verification.error in _DEVICE_CODE_TERMINATION_ERROR_CODES:
                raise _DEVICE_CODE_TERMINATION_ERROR_CODES[verification.error](verification.error)
            else:
                raise DeviceAuthorizationTerminated(
                    f'UNEXPECTED: HTTP {verification_code_response.status_code} {verification_code_response.text}'
                )

        self._output.write(
            'prompt_for_device_authorization',
            '\nPlease visit {verification_uri} and enter or confirm the code is "{user_code}".\n',
            dict(verification_uri=verification.verification_uri_complete or verification.verification_uri,
                 user_code=verification.user_code)
        )

        while time() - start_time < verification.expires_in:
            sleep(verification_interval)

            token_exchange_response = requests.post(urljoin(self._base_url, 'token'),
                                                    data=dict(client_id=client_id,
                                                              grant_type=GrantType.DEVICE_CODE,
                                                              device_code=verification.device_code)
                                                    )

            token_exchange = TokenExchangeResponse(**token_exchange_response.json())

            if token_exchange_response.status_code == 200:
                self._log.warning(f'DEBUG: HTTP {token_exchange_response.status_code}: {token_exchange_response.text}')
                raise NotImplementedError('Handle when the user code is verified')
            elif token_exchange_response.status_code == 400:
                if token_exchange.error == 'authorization_pending':
                    continue
                elif token_exchange.error == 'slow_down':
                    verification_interval += 5
                elif token_exchange.error in _DEVICE_CODE_TERMINATION_ERROR_CODES:
                    raise _DEVICE_CODE_TERMINATION_ERROR_CODES[token_exchange.error](token_exchange.error)
                else:
                    raise DeviceAuthorizationTerminated(
                        f'UNEXPECTED: HTTP {token_exchange_response.status_code} {token_exchange_response.text}'
                    )
            else:
                raise DeviceAuthorizationTerminated(
                    f'UNEXPECTED: HTTP {token_exchange_response.status_code} {token_exchange_response.text}'
                )


class MiniIDP:
    def __init__(self, base_url: str, output: Optional[ClientOutput] = None):
        self._log = get_logger_for_object(self)
        self._base_url = base_url.strip()
        self._output = output or ClientOutput()

        assert self._output, 'No output'

        assert self._base_url, 'The base URL must be defined.'

        if not self._base_url.endswith(r'/'):
            self._base_url += '/'

        # REST API Client
        self.rest_realms = RestAPIClient(urljoin(self._base_url, 'rest/realms'), Realm)

    def restore(self, config: MainConfig):
        response = requests.post(urljoin(self._base_url, 'rpc/recovery/import'),
                                 json=config.model_dump(mode='python'))

        _assert_response(response, [200])

    def export(self, *realm_ids_or_names: str) -> MainConfig:
        response = requests.post(urljoin(self._base_url, 'rpc/recovery/export'),
                                 json={'realms': realm_ids_or_names})

        _assert_response(response, [200])

        return MainConfig(**response.json())

    def realm(self, id: str) -> RealmOAuthClient:
        return RealmOAuthClient(id, urljoin(self._base_url, f'realms/{id}'), self._output)
