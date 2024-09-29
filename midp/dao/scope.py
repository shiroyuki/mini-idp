from typing import Any, Dict

from imagination.decorator.service import Service
from sqlalchemy import text

from midp.dao.atomic import AtomicDao, T
from midp.models import IAMScope
from midp.rds import DataStore


@Service()
class ScopeDao(AtomicDao[IAMScope]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, IAMScope.__tbl__)

    def map_row(self, row: Dict[str, Any]) -> IAMScope:
        return IAMScope(**row)

    # @override # for Python 3.12
    def add(self, obj: IAMScope) -> IAMScope:
        query = f"""
                INSERT INTO {self._table_name} (id, realm_id, name, description, sensitive)
                VALUES (:id, :realm_id, :name, :description, :sensitive)
                """.strip()

        parameters = {
            "id": obj.id,
            "realm_id": obj.realm_id,
            "name": obj.name,
            "description": obj.description,
            "sensitive": obj.sensitive,
        }

        self._datastore.execute_without_result(query, parameters)

        return obj
