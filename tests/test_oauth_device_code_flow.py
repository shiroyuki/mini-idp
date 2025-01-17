from midp.models import GrantType
from tests.common.base_feature import GenericAppFeature


class E2ETest(GenericAppFeature):
    def test_happy_path(self):
        self._initiate_client_with_device_code_flow()

    def _get_testing_client(self):
        return [client for client in self._test_config.clients if GrantType.DEVICE_CODE in client.grant_types][0]
