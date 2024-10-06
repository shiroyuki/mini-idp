from typing import Dict, Any
from urllib.parse import urlparse

import requests

from midp.iam.models import IAMOAuthClient
from midp.models import Realm, GrantType
from tests.common.base_feature import GenericAppFeature, TestConfig


class E2ETest(GenericAppFeature):
    def test_happy_path(self):
        realm: Realm = self._test_realm
        client: IAMOAuthClient = self._get_testing_client()

        def handle_activation(context: Dict[str, Any]):
            parsed_url = urlparse(context['verification_uri'])
            activation_uri = f'{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}'
            response = requests.post(activation_uri, json=dict(user_code=context['user_code'], authorized=True))
            self.assertEqual(200, response.status_code,
                             f'The activation request failed. (HTTP {response.status_code}: {response.text})')
            self.assertTrue(response.json()['authorized'])

        self._client_output.on('prompt_for_device_authorization', handle_activation)
        self.defer(lambda: self._client_output.off('prompt_for_device_authorization'))

        realm_oauth = self._client.realm(realm.name)
        realm_oauth.initiate_device_code(client.name)

    def _get_testing_client(self):
        realm: Realm = self._test_realm
        return [client for client in realm.clients if GrantType.DEVICE_CODE in client.grant_types][0]
