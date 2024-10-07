from typing import Union

from imagination.decorator.service import Service

from midp.common.enigma import Enigma
from midp.iam.dao.atomic import AtomicDao
from midp.iam.models import IAMOAuthClient
from midp.rds import DataStore


@Service()
class ClientDao(AtomicDao[IAMOAuthClient]):
    def __init__(self, datastore: DataStore, enigma: Enigma):
        super().__init__(datastore, IAMOAuthClient, IAMOAuthClient.__tbl__)

        self._enigma = enigma

        self.map_column_with_encryption('secret')\
            .map_column_as_json('grant_types')\
            .map_column_as_json('response_types')\
            .map_column_as_json('scopes')\
            .map_column_as_json('extras')

    def _encrypt_data(self, data: Union[bytes, str]) -> str:
        return self._enigma.encrypt(data).decode()

    def _decrypt_data(self, data: Union[bytes, str]) -> str:
        return self._enigma.decrypt(data).decode()
