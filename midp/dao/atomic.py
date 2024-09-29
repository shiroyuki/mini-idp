from contextlib import asynccontextmanager
from typing import Generic, TypeVar, Any, Dict, Optional, Generator, Callable

from pydantic.v1 import BaseModel
from sqlalchemy import text

from midp.rds import DataStore

T = TypeVar('T')


class AtomicDao(Generic[T]):
    def __init__(self, datastore: DataStore, table_name: str):
        self._datastore = datastore
        self._table_name = table_name

    def map_row(self, row: Dict[str, Any]) -> T:
        raise NotImplementedError()

    def select(self,
               where_clause: Optional[str] = None,
               parameters: Optional[Dict[str, Any]] = None) -> Generator[T, None, None]:
        query = f'SELECT * FROM {self._table_name}'
        if where_clause:
            query = f'{query} WHERE {where_clause}'
        for row in self._datastore.execute(query, parameters):
            # noinspection PyProtectedMember
            yield self.map_row(row._asdict())

    def add(self, obj: T) -> T:
        raise NotImplementedError()
