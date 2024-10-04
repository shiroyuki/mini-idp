from typing import Generic, TypeVar, Any, Dict, Optional, Generator

from midp.rds import DataStore

T = TypeVar('T')


class InsertError(RuntimeError):
    pass


class AtomicDao(Generic[T]):
    def __init__(self, datastore: DataStore, table_name: str):
        self._datastore = datastore
        self._table_name = table_name

    def map_row(self, row: Dict[str, Any]) -> T:
        raise NotImplementedError()

    def select(self,
               where: Optional[str] = None,
               parameters: Optional[Dict[str, Any]] = None,
               limit: Optional[int] = None) -> Generator[T, None, None]:
        query = f'SELECT * FROM {self._table_name}'

        if where:
            query = f'{query} WHERE {where}'

        if limit:
            query = f'{query} LIMIT {limit}'

        for row in self._datastore.execute(query, parameters):
            # noinspection PyProtectedMember
            yield self.map_row(row._asdict())

    def select_one(self,
                   where: Optional[str] = None,
                   parameters: Optional[Dict[str, Any]] = None) -> Optional[T]:
        items = [i for i in self.select(where, parameters, limit=1)]
        if items:
            return items[0]
        else:
            return None

    def add(self, obj: T) -> T:
        raise NotImplementedError()

    def delete(self,
               where: Optional[str] = None,
               parameters: Optional[Dict[str, Any]] = None) -> int:
        query = f'DELETE FROM {self._table_name}'

        if where:
            query = f'{query} WHERE {where}'

        return self._datastore.execute_without_result(query, parameters)
