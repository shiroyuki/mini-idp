from typing import Dict, Any

from imagination.decorator.service import Service

from midp.iam.dao.atomic import AtomicDao, InsertError
from midp.iam.models import IAMRole
from midp.rds import DataStore


@Service()
class RoleDao(AtomicDao[IAMRole]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, IAMRole.__tbl__)

    def get(self, realm_id: str, id: str) -> IAMRole:
        return self.select_one('realm_id = :realm_id AND (id = :id OR name = :id)', dict(realm_id=realm_id, id=id))

    def map_row(self, row: Dict[str, Any]) -> IAMRole:
        return IAMRole(**row)

    # @override # for Python 3.12
    def add(self, obj: IAMRole) -> IAMRole:
        query = f"""
                INSERT INTO {self._table_name} (id, realm_id, name, description)
                VALUES (:id, :realm_id, :name, :description)
                """.strip()

        parameters = {
            "id": obj.id,
            "realm_id": obj.realm_id,
            "name": obj.name,
            "description": obj.description,
        }

        if self._datastore.execute_without_result(query, parameters) == 0:
            raise InsertError(obj)

        return obj