import json
import os
import sys
from pathlib import Path
from time import sleep, time
from typing import TypeVar, Generic, List, Type, Dict, Any, Optional
from urllib.parse import urljoin, quote_plus
from uuid import uuid4

import requests
from jinja2.lexer import OptionalLStrip
from pydantic import BaseModel, Field
from requests import Response

from midp.common.enigma import Enigma
from midp.common.env_helpers import optional_env
from midp.snapshot.models import AppSnapshot
from midp.log_factory import get_logger_for, get_logger_for_object
from midp.iam.models import PredefinedScope, IAMScope, IAMOAuthClient, IAMPolicy, IAMRole, IAMUser
from midp.models import GrantType
from midp.oauth.models import DeviceVerificationCodeResponse, TokenExchangeResponse, OpenIDConfiguration

T = TypeVar('T')


def _assert_response(response: Response, status_codes: List[int]):
    assert response.status_code in status_codes, f'HTTP {response.status_code} from {response.request.method} {response.request.url}: {response.text}'


class WebClientSession(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


class WebClientContextConfig(BaseModel):
    base_url: str
    resource_url: Optional[str] = None


class WebClientConfig(BaseModel):
    release_version: str = '1.0'
    current_context: Optional[str] = None
    contexts: Dict[str, WebClientContextConfig] = Field(default_factory=dict)


class WebClientLocalStorageManager:
    def __init__(self, storage_dir: Optional[str] = None):
        self._enigma = Enigma()
        self._storage_dir = storage_dir or optional_env('MINI_IDP_CLIENT_STORAGE_DIR', str(Path.home() / ".mini_idp"))
        self._config_file_path = os.path.join(self._storage_dir, 'client.json')
        self._session_dir_path = os.path.join(self._storage_dir, 'sessions')

        if not os.path.exists(self._storage_dir):
            os.makedirs(self._storage_dir, exist_ok=True)
            os.makedirs(self._session_dir_path, exist_ok=True)

    def load_config(self) -> WebClientConfig:
        if not os.path.exists(self._config_file_path):
            return WebClientConfig()

        with open(self._config_file_path, 'r') as f:
            config = WebClientConfig(**json.load(f))

        return config

    def save_config(self, config: WebClientConfig) -> None:
        with open(self._config_file_path, 'w') as f:
            json.dump(config.model_dump(), f)

    def set_current_context(self, context: Optional[str]):
        config = self.load_config()
        config.current_context = context
        self.save_config(config)

    def get_current_context(self) -> str:
        config = self.load_config()
        return config.current_context

    def set_context(self, context: WebClientContextConfig, context_name: Optional[str] = None) -> None:
        config = self.load_config()

        current_context_name = context_name or config.current_context or 'default'

        config.contexts[current_context_name] = context
        self.save_config(config)

    def get_context(self, context_name: Optional[str] = None) -> Optional[WebClientContextConfig]:
        config = self.load_config()

        current_context_name = context_name or config.current_context or 'default'

        return config.contexts.get(current_context_name)

    def load_session(self, context_name: Optional[str] = None) -> Optional[WebClientSession]:
        session_path = self._get_session_path(context_name)
        if os.path.exists(session_path):
            with open(session_path, 'r') as f:
                session = WebClientSession(**json.load(f))
            return session
        else:
            return None

    def save_session(self, session: WebClientSession, context_name: Optional[str] = None) -> None:
        with open(self._get_session_path(context_name), 'w') as f:
            json.dump(session.model_dump(), f)

    def _get_session_path(self, context_name: Optional[str] = None) -> str:
        config = self.load_config()
        current_context_name = context_name or config.current_context
        return os.path.join(self._session_dir_path, self._enigma.compute_hash(current_context_name) + '.json')


class RestAPIClient(Generic[T]):
    def __init__(self,
                 base_url: str,
                 model_class: Type[T],
                 local_storage_manager: WebClientLocalStorageManager):
        self._log = get_logger_for(f'REST:{model_class.__name__}')
        self._base_url = base_url
        self._model_class = model_class
        self._local_storage_manager = local_storage_manager

        if not self._base_url.endswith(r'/'):
            self._base_url += '/'

    def list(self) -> List[T]:
        response = requests.get(self._base_url)

        _assert_response(response, [200])

        return [self._model_class(**i) for i in response.json()]

    def get(self, id: str) -> T:
        response = requests.get(self._base_url + id)
        _assert_response(response, [200])
        obj = self._model_class(**response.json())
        return obj

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


class MiniIDPConfigurer:
    def __init__(self, local_storage_manager: WebClientLocalStorageManager):
        self._local_storage_manager = local_storage_manager

    def use(self, context_name: Optional[str] = None) -> WebClientContextConfig:
        self._local_storage_manager.set_current_context(context_name)
        if context_name:
            return self._local_storage_manager.get_context(context_name)
        else:
            return None

    def set_context(self, context: WebClientContextConfig, context_name: Optional[str] = None):
        self._local_storage_manager.set_context(context, context_name)

    def get_context(self, context_name: Optional[str] = None) -> WebClientContextConfig:
        return self._local_storage_manager.get_context(context_name)


class MiniIDP:
    def __init__(self,
                 base_url: str,
                 output: Optional[ClientOutput] = None,
                 local_storage_manager: Optional[WebClientLocalStorageManager] = None,
                 resource_url: Optional[str] = None):
        self._log = get_logger_for_object(self)
        self._enigma = Enigma()
        self._base_url = base_url.strip()
        self._resource_url = resource_url
        self._output = output or ClientOutput()
        self._openid_config: Optional[OpenIDConfiguration] = None
        self._local_storage_manager = local_storage_manager or WebClientLocalStorageManager()

        assert self._output, 'No output'

        assert self._base_url, 'The base URL must be defined.'

        if not self._base_url.endswith(r'/'):
            self._base_url += '/'

        # REST API Clients
        self._clients: RestAPIClient[IAMOAuthClient] = RestAPIClient(
            urljoin(self._base_url, 'rest/clients'),
            IAMOAuthClient,
            self._local_storage_manager
        )
        self._policies: RestAPIClient[IAMPolicy] = RestAPIClient(
            urljoin(self._base_url, 'rest/policies'),
            IAMPolicy,
            self._local_storage_manager
        )
        self._roles: RestAPIClient[IAMRole] = RestAPIClient(
            urljoin(self._base_url, 'rest/roles'),
            IAMRole,
            self._local_storage_manager
        )
        self._scopes: RestAPIClient[IAMScope] = RestAPIClient(
            urljoin(self._base_url, 'rest/scopes'),
            IAMScope,
            self._local_storage_manager
        )
        self._users: RestAPIClient[IAMUser] = RestAPIClient(
            urljoin(self._base_url, 'rest/users'),
            IAMUser,
            self._local_storage_manager
        )

    @property
    def base_url(self):
        return self._base_url

    @property
    def clients(self):
        return self._clients

    @property
    def policies(self):
        return self._policies

    @property
    def roles(self):
        return self._roles

    @property
    def scopes(self):
        return self._scopes

    @property
    def users(self):
        return self._users

    def restore(self, config: AppSnapshot):
        response = requests.post(urljoin(self._base_url, 'rpc/recovery'),
                                 json=config.model_dump(mode='python'))
        _assert_response(response, [200])

    def export(self) -> AppSnapshot:
        response = requests.get(urljoin(self._base_url, 'rpc/recovery'))
        _assert_response(response, [200])

        return AppSnapshot(**response.json())

    def get_openid_configuration(self) -> OpenIDConfiguration:
        if not self._openid_config:
            response = requests.get(urljoin(self._base_url, '.well-known/openid-configuration'))
            _assert_response(response, [200])
            self._openid_config = OpenIDConfiguration(**response.json())
        return self._openid_config

    def initiate_device_code(self, client_id: str, resource_url: Optional[str] = None):
        openid_config = self.get_openid_configuration()

        query_string = ''
        actual_resource_url = resource_url or self._resource_url

        if actual_resource_url:
            query_string = f'?resource={quote_plus(actual_resource_url)}'

        verification_code_response = requests.post(openid_config.device_authorization_endpoint + query_string,
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
            openid_config = self.get_openid_configuration()

            sleep(verification_interval)

            token_exchange_response = requests.post(openid_config.token_endpoint,
                                                    data=dict(client_id=client_id,
                                                              grant_type=GrantType.DEVICE_CODE,
                                                              device_code=verification.device_code)
                                                    )

            if token_exchange_response.status_code == 200:
                token_exchange = TokenExchangeResponse(**token_exchange_response.json())
                context_name = self._enigma.compute_hash(f'base_url={self._base_url};resource_url={self._resource_url}')

                self._local_storage_manager.set_context(
                    context_name=context_name,
                    context=WebClientContextConfig(
                        base_url=self._base_url,
                        resource_url=actual_resource_url,
                    ),
                )

                self._local_storage_manager.save_session(
                    context_name=context_name,
                    session=WebClientSession(
                        access_token=token_exchange.access_token,
                        refresh_token=token_exchange.refresh_token,
                    ),
                )

                break
            elif token_exchange_response.status_code == 400:
                token_exchange = TokenExchangeResponse(**token_exchange_response.json())

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
            # end: if
        # end: while

    @property
    def config(self):
        return MiniIDPConfigurer(self._local_storage_manager)
