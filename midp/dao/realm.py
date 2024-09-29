from typing import Dict, Any

from imagination.decorator.service import Service

from midp.dao.atomic import AtomicDao
from midp.models import Realm
from midp.rds import DataStore


@Service()
class RealmDao(AtomicDao[Realm]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, Realm.__tbl__)

    # @override # for Python 3.12
    def map_row(self, row: Dict[str, Any]) -> Realm:
        return Realm(**row)

    # @override # for Python 3.12
    def add(self, obj: Realm) -> Realm:
        query = f"""
                INSERT INTO {self._table_name} (id, name)
                VALUES (:id, :name)
                """.strip()

        parameters = {
            "id": obj.id,
            "name": obj.name,
        }

        self._datastore.execute_without_result(query, parameters)

        return obj
