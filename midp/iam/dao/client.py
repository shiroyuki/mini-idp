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

        self.column('id')\
            .column('realm_id')\
            .column('name')\
            .column('secret', 'encrypted_secret',
                    convert_to_sql_data=lambda v: self._enigma.encrypt(v).decode(),
                    convert_to_property_data=lambda v: self._enigma.decrypt(v).decode())\
            .column('audience')\
            .column_as_json('grant_types')\
            .column_as_json('response_types')\
            .column_as_json('scopes')\
            .column_as_json('extras')\
            .column('description')

    def get(self, realm_id: str, id: str) -> IAMOAuthClient:
        return self.select_one('realm_id = :realm_id AND (id = :id OR name = :id)', dict(realm_id=realm_id, id=id))
