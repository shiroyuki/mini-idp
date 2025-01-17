from tests.common.base_feature import GenericAppFeature


class E2ETest(GenericAppFeature):
    def test_happy_path(self):
        self._initiate_client_with_device_code_flow()

        session = self._local_storage_manager.load_session()

        assert session is not None
