from urllib.parse import urljoin

import requests
from requests import Response

from tests.common.base_feature import GenericAppFeature, TestConfig


class E2ETest(GenericAppFeature):
    def test_realm_login(self):
        realm = self._test_realm
        test_user = realm.users[0]

        web_session = requests.Session()
        response: Response = web_session.post(urljoin(TestConfig.TEST_BASE_URL, f'realms/{realm.name}/login'),
                                              headers={'Accept': 'application/json'},
                                              data={'username': test_user.name, 'password': test_user.password})
        self.assertEqual(200, response.status_code)
        data = response.json()
        self.assertIsNotNone(data.get('session_id'))
        self.assertIsNotNone(response.cookies.get('sid'))
        self.assertNotEqual(data.get('session_id'), response.cookies.get('sid'))  # The "sid" cookie is encrypted.
        self.assertIsNotNone(data.get('principle'))