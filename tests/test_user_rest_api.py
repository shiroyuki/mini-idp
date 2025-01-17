from midp.app.web_client import ClientError
from midp.common.obj_patcher import SimpleJsonPatchOperation
from midp.iam.models import IAMUser
from tests.common.base_feature import GenericAppFeature


class E2ETest(GenericAppFeature):
    def test_get_unknown_user(self):
        try:
            self._client.users.get("faux_user")
        except ClientError as e:
            self.assertEqual(404, e.response_status)

    def test_manage_new_user_as_admin(self):
        self._initiate_client_with_device_code_flow()

        test_user = self._client.users.create(IAMUser(
            name="test_user",
            password="nosecret",
            email="test_user@localhost",
            full_name="Test User",
        ))
        self.defer(lambda: self._client.users.delete('test_user'))

        self.assertIsNotNone(test_user.id)
        self.assertEqual('test_user', test_user.name)
        self.assertEqual('Test User', test_user.full_name)
        self.assertEqual('test_user@localhost', test_user.email)
        self.assertEqual('nosecret', test_user.password)

        self._client.users.patch(
            test_user.id,
            [
                SimpleJsonPatchOperation(op="replace", path="/full_name", value="Test User Modified"),
            ],
        )

        self.assertEqual("Test User Modified", self._client.users.get('test_user').full_name)
        self.assertEqual("Test User Modified", self._client.users.get(test_user.id).full_name)

        self._client.users.patch(
            test_user.id,
            [
                SimpleJsonPatchOperation(op="replace", path="/password", value="Foo Bar"),
            ],
        )

        self.assertEqual("Test User Modified", self._client.users.get('test_user').full_name)
        self.assertEqual("Test User Modified", self._client.users.get(test_user.id).full_name)

        self._client.users.delete(test_user.name)

        try:
            self._client.users.get(test_user.id)
        except ClientError as e:
            self.assertEqual(404, e.response_status)

    def test_modify_existing_user_as_admin(self):
        self._initiate_client_with_device_code_flow()

        users = self._client.users.list()
        self.assertLessEqual(0, len(users), 'Has at least one user')

        user_a = self._client.users.get("user_a")
        self.assertTrue(user_a.id and user_a.id != 'user_a', 'The ID should be randomly generated.')
        self.assertEqual('user_a', user_a.name, 'Match the user name')

        # Update the object by the resource name (alternate ID).
        self._client.users.patch(
            user_a.name,
            [
                SimpleJsonPatchOperation(op="replace", path="/full_name", value="Alpha Alternative"),
            ],
        )

        user_a = self._client.users.get(user_a.id)
        self.assertEqual("Alpha Alternative", user_a.full_name, 'Match the new full name')
