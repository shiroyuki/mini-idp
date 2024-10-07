from typing import Any, Dict, List, Union

from imagination.decorator.service import Service

from midp.common.enigma import Enigma
from midp.iam.dao.atomic import AtomicDao, InsertError
from midp.iam.dao.role import RoleDao
from midp.iam.models import IAMUser, IAMRole
from midp.rds import DataStore


@Service()
class UserDao(AtomicDao[IAMUser]):
    def __init__(self, datastore: DataStore, role_dao: RoleDao, enigma: Enigma):
        super().__init__(datastore, IAMUser, IAMUser.__tbl__)
        self._role_dao = role_dao
        self._enigma = enigma

        self.map_column_with_encryption('password')\
            .map_column_as_json('roles')

    def _encrypt_data(self, data: Union[bytes, str]) -> str:
        return self._enigma.encrypt(data).decode()

    def _decrypt_data(self, data: Union[bytes, str]) -> str:
        return self._enigma.decrypt(data).decode()

    def get(self, id: str) -> IAMUser:
        return self.select_one('id = :id OR name = :id OR email = :id', dict(id=id))
