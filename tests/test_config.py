from tests.common.base_feature import GenericAppFeature


class ConfigTest(GenericAppFeature):
    def test_restore_from_files(self):
        exported_config = self._client.export(self._test_realm.name)

        realm = exported_config.realms[0]
        scopes = [s.name for s in realm.scopes]

        self.assertIn('scope_1', scopes)
