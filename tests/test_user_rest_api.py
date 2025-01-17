from tests.common.base_feature import GenericAppFeature


class TestUserRestApi(GenericAppFeature):
    def happy_path(self):
        self._initiate_client_with_device_code_flow()
        user_a = self._client.users.get("user_a")
        print(user_a)