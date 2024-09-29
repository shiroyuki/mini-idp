from typing import Any, Dict

from midp.dao.atomic import AtomicDao
from midp.models import OAuthClient
from midp.rds import DataStore


@Service()
class RoleDao(AtomicDao[OAuthClient]):
    def __init__(self, datastore: DataStore):
        super().__init__(datastore, OAuthClient.__tbl__)

    def map_row(self, row: Dict[str, Any]) -> OAuthClient:
        return OAuthClient(**row)

    # @override # for Python 3.12
    def add(self, obj: OAuthClient) -> OAuthClient:
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
