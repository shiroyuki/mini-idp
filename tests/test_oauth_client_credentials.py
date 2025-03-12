from tests.common.base_feature import GenericAppFeature


class E2ETest(GenericAppFeature):
    def test_login(self):
        self._authenticate_with_client_credentials()
