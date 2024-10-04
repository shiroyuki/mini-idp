import json
from typing import Dict, Any

from imagination.decorator.service import Service

from midp.iam.dao.atomic import AtomicDao, InsertError
from midp.iam.models import IAMPolicy
from midp.rds import DataStore


@Service()
class PolicyDao(AtomicDao[IAMPolicy]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, IAMPolicy.__tbl__)

    def get(self, realm_id: str, id: str) -> IAMPolicy:
        return self.select_one('realm_id = :realm_id AND (id = :id OR name = :id)', dict(realm_id=realm_id, id=id))

    def map_row(self, row: Dict[str, Any]) -> IAMPolicy:
        return IAMPolicy(**row)

    # @override # for Python 3.12
    def add(self, obj: IAMPolicy) -> IAMPolicy:
        query = f"""
                        INSERT INTO {self._table_name}
                        (
                            id,
                            realm_id,
                            name,
                            subjects,
                            resource,
                            scopes
                        )
                        VALUES (
                            :id,
                            :realm_id,
                            :name,
                            (:subjects)::jsonb,
                            :resource,
                            (:scopes)::jsonb
                        )
                        """.strip()

        parameters = {
            "id": obj.id,
            "realm_id": obj.realm_id,
            "name": obj.name,
            "subjects": json.dumps([s.model_dump(exclude_defaults=True) for s in obj.subjects]),
            "resource": obj.resource,
            "scopes": json.dumps(obj.scopes),
        }

        if self._datastore.execute_without_result(query, parameters) == 0:
            raise InsertError(obj)

        return obj