from urllib.parse import urljoin

import requests
from imagination import container
from requests import Response

from midp.common.token_manager import TokenManager
from tests.common.base_feature import GenericAppFeature, TestConfig


class E2ETest(GenericAppFeature):
    def test_login(self):
        test_user = self._test_config.users[0]

        for identifier in (test_user.name, test_user.email):
            web_session = requests.Session()
            response: Response = self._authenticate(web_session, identifier, test_user.password)
            self.assertEqual(200, response.status_code)

            data = response.json()

            self.assertIsNotNone(data.get('session_id'))
            self.assertIsNotNone(response.cookies.get('sid'))
            self.assertNotEqual(data.get('session_id'), response.cookies.get('sid'))  # The "sid" cookie is encrypted.

            principle = data.get('principle')
            self.assertIsNotNone(principle)
            self.assertIn('idp.root', principle["roles"])

            access_token = data.get('access_token')
            token_manager: TokenManager = container.get(TokenManager)
            access_claims = token_manager.parse_token(access_token)
            self.assertIn('IAMRole/idp.root', access_claims["psl"])
            scopes = access_claims["scope"].split(' ') if access_claims["scope"] else []
            self.assertTrue(len(scopes) > 0, 'The scope is not defined.')
