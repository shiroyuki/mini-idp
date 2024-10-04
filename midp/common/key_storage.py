import asyncio
import json
from abc import ABC
from time import time
from typing import Any, Optional, Dict, List

from imagination.decorator.service import Service

from midp.iam.dao.realm import RealmDao
from midp.log_factory import get_logger_for
from midp.iam.models import Realm
from midp.rds import DataStore


class BaseKeyStorage(ABC):
    def __init__(self, datastore: DataStore, namespace: str, table_name: str):
        self._log = get_logger_for(f'KV({namespace})')
        self._datastore = datastore
        self._table_name = table_name

    def get_pk_columns(self) -> List[str]:
        raise NotImplementedError()

    def get_pk_condition(self) -> str:
        return ' AND '.join([
            f'{c_name} = :{c_name}'
            for c_name in self.get_pk_columns()
        ])

    def get_pk_params(self, key: str) -> Dict[str, Any]:
        raise NotImplementedError()

    async def async_get(self, key: str) -> Any:
        return await asyncio.to_thread(self.get, key)

    def get(self, key: str) -> Any:
        params = self.get_pk_params(key)
        params.update(dict(current_time=time()))

        values = [
            row.v
            for row in self._datastore.execute(
                f"""
                SELECT v
                FROM {self._table_name}
                WHERE ({self.get_pk_condition()})
                    AND (
                        expiry_timestamp IS NULL
                        OR expiry_timestamp > :current_time
                    )
                LIMIT 1
                """,
                params
            )
        ]

        return values[0] if values else None

    async def async_delete(self, key: str):
        await asyncio.to_thread(self.delete, key)

    def delete(self, key: str):
        """ Delete the given key or the expired keys """
        params = self.get_pk_params(key)
        params.update(dict(current_time=time()))

        self._datastore.execute_without_result(
            f"""
            DELETE FROM {self._table_name}
            WHERE ({self.get_pk_condition()})
                OR expiry_timestamp <= :current_time
            """,
            params
        )

    async def async_set(self, key: str, value: Any, expiry_timestamp: Optional[int] = None):
        await asyncio.to_thread(self.set, key, value, expiry_timestamp)

    def set(self, key: str, value: Any, expiry_timestamp: Optional[int] = None):
        serialized_value = json.dumps(value)

        params = self.get_pk_params(key)
        params.update(dict(v=serialized_value, current_time=time(), expiry_timestamp=expiry_timestamp))

        insert_ok = self._datastore.execute_without_result(
            f"""
            INSERT INTO {self._table_name} ({', '.join(self.get_pk_columns())}, v, expiry_timestamp)
            VALUES ({', '.join([f':{c_name}' for c_name in self.get_pk_columns()])}, (:v)::jsonb, :expiry_timestamp)
            ON CONFLICT DO NOTHING
            """,
            params
        ) == 1

        if not insert_ok:
            self._log.debug(f'{self._table_name}: Unable to ADD {self.get_pk_params(key)} = {serialized_value} '
                            + (f'with expiry on {expiry_timestamp})' if expiry_timestamp else ''))

            update_ok = self._datastore.execute_without_result(
                f"""
                UPDATE {self._table_name}
                SET v = (:v)::jsonb,
                    expiry_timestamp = :expiry_timestamp
                WHERE ({self.get_pk_condition()})
                """,
                params
            ) > 0

            if not update_ok:
                raise RuntimeError(f'{self._table_name}: Unable to SET {self.get_pk_params(key)} = {serialized_value} '
                                   + (f'with expiry on {expiry_timestamp})' if expiry_timestamp else ''))


class RealmKeyStorage(BaseKeyStorage):
    def __init__(self, datastore: DataStore, realm: Realm):
        super().__init__(datastore, realm.name, 'realm_kv')
        self._realm = realm

    def get_pk_columns(self) -> List[str]:
        return ['realm_id', 'k']

    def get_pk_params(self, key: str) -> Dict[str, Any]:
        return dict(realm_id=self._realm.id, k=key)


@Service()
class KeyStorage(BaseKeyStorage):
    def __init__(self, datastore: DataStore, realm_dao: RealmDao):
        super().__init__(datastore, 'root', 'root_kv')
        self._realm_dao = realm_dao

    def realm(self, realm_id: str) -> RealmKeyStorage:
        realm = self._realm_dao.get(realm_id)

        if not realm:
            raise ValueError(f'Realm {realm_id} not found')

        return RealmKeyStorage(self._datastore, realm)

    def get_pk_columns(self) -> List[str]:
        return ['k']

    def get_pk_params(self, key: str) -> Dict[str, Any]:
        return dict(k=key)
