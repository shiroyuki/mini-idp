import json
from copy import deepcopy
from typing import Any, Dict

from imagination.decorator.service import Service

from midp.common.enigma import Enigma
from midp.iam.dao.atomic import AtomicDao, InsertError
from midp.iam.models import OAuthClient
from midp.rds import DataStore


@Service()
class ClientDao(AtomicDao[OAuthClient]):
    def __init__(self, datastore: DataStore, enigma: Enigma):
        super().__init__(datastore, OAuthClient.__tbl__)
        self._enigma = enigma

    def get(self, realm_id: str, id: str) -> OAuthClient:
        return self.select_one('realm_id = :realm_id AND (id = :id OR name = :id)', dict(realm_id=realm_id, id=id))

    def map_row(self, row: Dict[str, Any]) -> OAuthClient:
        data = deepcopy(row)
        data['secret'] = self._enigma.decrypt(data['encrypted_secret']).decode()
        del data['encrypted_secret']
        return OAuthClient(**row)

    # @override # for Python 3.12
    def add(self, obj: OAuthClient) -> OAuthClient:
        query = f"""
                        INSERT INTO {self._table_name}
                        (
                            id,
                            realm_id,
                            name,
                            encrypted_secret,
                            audience,
                            grant_types,
                            response_types,
                            scopes,
                            extras,
                            description
                        )
                        VALUES (
                            :id,
                            :realm_id,
                            :name,
                            :encrypted_secret,
                            :audience,
                            (:grant_types)::jsonb,
                            (:response_types)::jsonb,
                            (:scopes)::jsonb,
                            (:extras)::jsonb,
                            :description
                        )
                        """.strip()

        parameters = {
            "id": obj.id,
            "realm_id": obj.realm_id,
            "name": obj.name,
            "encrypted_secret": self._enigma.encrypt(obj.secret).decode(),
            "audience": obj.audience,
            "grant_types": json.dumps(obj.grant_types),
            "response_types": json.dumps(obj.response_types),
            "scopes": json.dumps(obj.scopes),
            "extras": json.dumps(obj.extras),
            "description": obj.description,
        }

        if self._datastore.execute_without_result(query, parameters) == 0:
            raise InsertError(obj)

        return obj
