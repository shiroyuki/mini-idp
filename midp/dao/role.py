from typing import Dict, Any

from imagination.decorator.service import Service

from midp.dao.atomic import AtomicDao
from midp.models import IAMRole
from midp.rds import DataStore


@Service()
class RoleDao(AtomicDao[IAMRole]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, IAMRole.__tbl__)

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

        self._datastore.execute_without_result(query, parameters)

        return obj