import asyncio
import json
from abc import ABC
from time import time
from typing import Any, Optional, Dict, List, Union

from imagination.decorator.service import Service
from pydantic import BaseModel
from sqlalchemy import text

from midp.log_factory import midp_logger
from midp.rds import DataStore


class Entry(BaseModel):
    key: str
    value: Any
    expiry_timestamp: Optional[Union[int, float]] = None


@Service()
class KeyStorage(ABC):
    def __init__(self, datastore: DataStore):
        self._log = midp_logger(f'KV')
        self._datastore = datastore
        self._table_name = 'kv'

    def get_pk_columns(self) -> List[str]:
        return ['k']

    def get_pk_condition(self) -> str:
        return ' AND '.join([
            f'{c_name} = :{c_name}'
            for c_name in self.get_pk_columns()
        ])

    def get_pk_params(self, key: str) -> Dict[str, Any]:
        return dict(k=key)

    async def async_get(self, key: str) -> Any:
        return await asyncio.to_thread(self.get, key)

    def get(self, key: str) -> Any:
        params = self.get_pk_params(key)
        params.update(dict(current_time=int(time())))

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
        params.update(dict(current_time=int(time())))

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

    def batch_set(self, *entries: Entry):
        with self._datastore.connect() as c:
            for entry in entries:
                serialized_value = json.dumps(entry.value)

                params = self.get_pk_params(entry.key)
                params.update(dict(v=serialized_value, current_time=int(time()), expiry_timestamp=entry.expiry_timestamp))

                insert_ok = c.execute(
                    text(
                        f"""
                            INSERT INTO {self._table_name} ({', '.join(self.get_pk_columns())}, v, expiry_timestamp)
                            VALUES ({', '.join([f':{c_name}' for c_name in self.get_pk_columns()])}, (:v)::jsonb, :expiry_timestamp)
                            ON CONFLICT DO NOTHING
                            """),
                    params
                ).rowcount == 1

                if not insert_ok:
                    self._log.debug(
                        f'{self._table_name}: Unable to ADD {self.get_pk_params(entry.key)} = {serialized_value} '
                        + (f'with expiry on {entry.expiry_timestamp}' if entry.expiry_timestamp else ''))

                    update_ok = c.execute(
                        text(
                            f"""
                                UPDATE {self._table_name}
                                SET v = (:v)::jsonb,
                                    expiry_timestamp = :expiry_timestamp
                                WHERE ({self.get_pk_condition()})
                                """
                        ),
                        params
                    ).rowcount > 0

                    if not update_ok:
                        raise RuntimeError(
                            f'{self._table_name}: Unable to UPDATE {self.get_pk_params(entry.key)} = {serialized_value} '
                            + (f'with expiry on {entry.expiry_timestamp}' if entry.expiry_timestamp else ''))
            c.commit()

    def set(self, key: str, value: Any, expiry_timestamp: Optional[int] = None):
        self.batch_set(Entry(key=key, value=value, expiry_timestamp=int(expiry_timestamp) if expiry_timestamp else None))
