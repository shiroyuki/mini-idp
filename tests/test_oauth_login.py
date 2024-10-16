from urllib.parse import urljoin

import requests
from requests import Response

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
            self.assertIsNotNone(data.get('principle'))
