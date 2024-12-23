from typing import Dict, Any
from urllib.parse import urlparse

from midp.iam.models import IAMOAuthClient
from midp.models import GrantType
from tests.common.base_feature import GenericAppFeature


class E2ETest(GenericAppFeature):
    def test_happy_path(self):
        client: IAMOAuthClient = self._get_testing_client()

        def handle_activation(context: Dict[str, Any]):
            parsed_url = urlparse(context['verification_uri'])
            activation_uri = f'{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}'
            response = self._http_session.post(activation_uri,
                                               json=dict(user_code=context['user_code'],
                                                         authorized=True),
                                               allow_redirects=False)
            if response.status_code == 307:
                self._authenticate_as('user_a')
                response = self._http_session.post(activation_uri,
                                                   json=dict(user_code=context['user_code'],
                                                             authorized=True),
                                                   allow_redirects=False)
            self.assertEqual(200, response.status_code,
                             f'The activation request failed. (HTTP {response.status_code}: {response.text})')
            self.assertTrue(response.json()['authorized'])

        self._client_output.on('prompt_for_device_authorization', handle_activation)
        self.defer(lambda: self._client_output.off('prompt_for_device_authorization'))

        self._client.initiate_device_code(client.name, 'http://faux.shiroyuki.com/resource-0')

    def _get_testing_client(self):
        return [client for client in self._test_config.clients if GrantType.DEVICE_CODE in client.grant_types][0]
