from unittest import TestCase

from imagination.standalone import container

from midp.config import restore_from_files
from midp.dao.user import UserDao
from midp.models import Realm
from midp.rds import DataStore


class ConfigTest(TestCase):
    def tearDown(self):
        user_dao: UserDao = container.get(UserDao)
        for user in user_dao.select():
            print(f'PANDA: user = {user.model_dump_json(indent=2)}')

        datastore: DataStore = container.get(DataStore)
        for row in datastore.execute('SELECT * FROM iam_user_role'):
            print(f'PANDA: row = {row}')
        datastore.execute_without_result(f'DELETE FROM {Realm.__tbl__} WHERE id IS NOT NULL')

    def test_restore_from_files(self):
        restore_from_files(['config-auto-testing.yml'])
