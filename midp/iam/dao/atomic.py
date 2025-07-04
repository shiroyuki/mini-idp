import json
from dataclasses import is_dataclass, asdict
from typing import Generic, TypeVar, Any, Dict, Optional, Generator, Callable, List, Type, Union, Tuple, Iterable

from pydantic import BaseModel

from midp.log_factory import midp_logger_for
from midp.common.rds import DataStore, DataStoreSession

T = TypeVar('T')


class InsertError(RuntimeError):
    pass


class UpdateError(RuntimeError):
    pass


class _ColumnMapping(BaseModel):
    column_name: str

    convert_to_property_data: Optional[Callable[[Any], Any]] = None
    """ Convert the parsed SQL data before setting the property.

        For example:

        ```python
        def callback(sql_data: Any) -> Any:
            ...
        ```
    """

    convert_to_sql_data: Optional[Callable[[Any], Any]] = None
    """ Convert the property data before writing to the datastore.

        For example:

        ```python
        def callback(property_data: Any) -> Any:
            ...
        ```
    """

    cast_to_sql_type: Optional[str] = None
    """ Set the casting type """


class AtomicDao(Generic[T]):
    def __init__(self, datastore: DataStore, model_class: Type[T], table_name: str):
        self._log = midp_logger_for(self)

        self._datastore = datastore
        self._model_class = model_class
        self._table_name = table_name
        self._column_mappings: Dict[str, _ColumnMapping] = dict()
        self._reverse_column_mappings: Dict[str, str] = dict()

        self.map_all_automatically()

    def map_all_automatically(self):
        for property_name in self._model_class.__annotations__.keys():
            self.map_column(property_name)
        return self

    def map_column(self,
                   property_name: str,
                   column_name: Optional[str] = None,
                   convert_to_property_data: Optional[Callable[[Any], Any]] = None,
                   convert_to_sql_data: Optional[Callable[[Any], Any]] = None,
                   cast_to_sql_type: Optional[str] = None):
        """ Map a property to a column for the primary table. """
        column_name = column_name or property_name
        self._column_mappings[property_name] = _ColumnMapping(column_name=column_name or property_name,
                                                              convert_to_property_data=convert_to_property_data,
                                                              convert_to_sql_data=convert_to_sql_data,
                                                              cast_to_sql_type=cast_to_sql_type)
        self._reverse_column_mappings[column_name] = property_name
        return self

    def map_column_as_json(self, property_name: str, column_name: Optional[str] = None):
        """ Map a property to a JSON column for the primary table. """
        return self.map_column(property_name=property_name,
                               column_name=column_name,
                               convert_to_sql_data=lambda v: json.dumps(self._convert_to_serializable_obj(v)),
                               cast_to_sql_type='jsonb')

    def map_column_with_encryption(self, property_name: str, column_name: Optional[str] = None):
        """ Map a property to a column with encryption. """
        return self.map_column(property_name=property_name,
                               column_name=column_name if column_name else f'encrypted_{property_name}',
                               convert_to_sql_data=self._encrypt_data,
                               convert_to_property_data=self._decrypt_data)

    def _encrypt_data(self, data: Union[bytes, str]) -> str:
        raise NotImplementedError()

    def _decrypt_data(self, data: Union[bytes, str]) -> str:
        raise NotImplementedError()

    def _convert_to_serializable_obj(self, given_value: Any) -> Any:
        """ Recursively convert the given value to a serializable object """
        if isinstance(given_value, dict):
            data = dict()
            for k, v in given_value.items():
                data[k] = self._convert_to_serializable_obj(v)
            return data
        elif isinstance(given_value, (list, set, tuple)):
            data = list()
            for i in given_value:
                data.append(self._convert_to_serializable_obj(i))
            return data
        elif isinstance(given_value, BaseModel):
            return given_value.model_dump(mode='python', exclude_defaults=True)
        elif is_dataclass(given_value):
            return asdict(given_value)
        else:
            return given_value

    def from_dict(self, data: Dict[str, Any]) -> T:
        return self._model_class(**data)

    def map_row(self, row: Dict[str, Any]) -> T:
        """ Map a row from the cursor to a model object """
        data = dict()

        for k, v in row.items():
            if k not in self._reverse_column_mappings:
                continue
            property_name = self._reverse_column_mappings[k]
            cm = self._column_mappings.get(property_name)
            data[property_name] = cm.convert_to_property_data(v) if cm.convert_to_property_data else v

        return self._model_class(**data)

    def select(self,
               where: Optional[str] = None,
               parameters: Union[None, Dict[str, Any]] = None,
               order_by: Optional[List[Iterable[str]]] = None,
               limit: Optional[int] = None,
               datastore_session: Optional[DataStoreSession] = None) -> Generator[T, None, None]:
        query = f'SELECT * FROM {self._table_name}'

        if where:
            query = f'{query} WHERE {where}'

        if order_by:
            actual_order_list: List[Tuple[str, str]] = []

            for order in order_by:
                if len(order) > 1:
                    field, direction = order[:2]
                elif len(order) == 1:
                    field = order[0]
                    direction = 'ASC'
                else:
                    raise RuntimeError(f'The order-by parameter is invalid. (given = {order_by})')

                actual_order_list.append((field, direction))

            actual_order_by = ', '.join([f'{field} {direction}' for field, direction in actual_order_list])

            query = f'{query} ORDER BY {actual_order_by}'

        if limit:
            query = f'{query} LIMIT {limit}'

        self._log.debug(f'RUN: {query} (params={parameters})')

        cursor = (
            datastore_session.execute(query, parameters=parameters)
            if datastore_session
            else self._datastore.execute(query, parameters=parameters)
        )

        for row in cursor:
            # noinspection PyProtectedMember
            yield self.map_row(row._asdict())

    def select_one(self,
                   where: Optional[str] = None,
                   parameters: Optional[Dict[str, Any]] = None,
                   datastore_session: Optional[DataStoreSession] = None) -> Optional[T]:
        items = [i for i in self.select(where, parameters, limit=1, datastore_session=datastore_session)]
        if items:
            return items[0]
        else:
            return None

    def delete(self,
               where: Optional[str] = None,
               parameters: Optional[Dict[str, Any]] = None,
               datastore_session: Optional[DataStoreSession] = None) -> int:
        query = f'DELETE FROM {self._table_name}'

        if where:
            query = f'{query} WHERE {where}'

        self._log.debug(f'RUN: {query} (params={parameters})')

        if datastore_session:
            return datastore_session.execute_without_result(query, parameters)
        else:
            return self._datastore.execute_without_result(query, parameters)

    def get(self, id: str,
            datastore_session: Optional[DataStoreSession] = None) -> Optional[T]:
        return self.select_one('id = :id OR name = :id', dict(id=id))

    def add(self, obj: T,
            datastore_session: Optional[DataStoreSession] = None) -> T:
        return self.simple_insert(obj, datastore_session)

    def simple_insert(self, obj: T,
                      datastore_session: Optional[DataStoreSession] = None) -> T:
        sql_column_names: List[str] = list()
        sql_column_value_placeholders: List[str] = list()
        sql_params: Dict[str, Any] = dict()

        for property_name, cm in self._column_mappings.items():
            column_name = cm.column_name
            column_value = getattr(obj, property_name)

            sql_column_names.append(column_name)
            sql_column_value_placeholders.append(f'(:{column_name})::{cm.cast_to_sql_type}'
                                                 if cm.cast_to_sql_type
                                                 else f':{column_name}')
            sql_params[column_name] = (cm.convert_to_sql_data(column_value)
                                       if callable(cm.convert_to_sql_data)
                                       else column_value)

        insert_query = f"""
            INSERT INTO {self._table_name} ({', '.join(sql_column_names)})
            VALUES ({', '.join(sql_column_value_placeholders)}) 
            ON CONFLICT DO NOTHING 
        """

        self._log.debug(f'RUN: {insert_query} (params={sql_params})')

        if datastore_session:
            if datastore_session.execute_without_result(insert_query, sql_params) == 0:
                raise InsertError(obj)
        elif self._datastore.execute_without_result(insert_query, sql_params) == 0:
            raise InsertError(obj)

        return obj

    def simple_update(self,
                      obj: T,
                      where: Optional[str] = None,
                      where_params: Optional[Dict[str, Any]] = None,
                      datastore_session: Optional[DataStoreSession] = None) -> T:
        sql_column_names: List[str] = list()
        sql_column_value_placeholders: List[str] = list()
        sql_params: Dict[str, Any] = dict()
        sql_setters: List[str] = list()

        for property_name, cm in self._column_mappings.items():
            column_name = cm.column_name
            column_value = getattr(obj, property_name)

            set_param_name = f'set_{column_name}'

            sql_column_names.append(column_name)
            sql_column_value_placeholders.append(f'(:{set_param_name})::{cm.cast_to_sql_type}'
                                                 if cm.cast_to_sql_type
                                                 else f':{column_name}')
            sql_params[set_param_name] = (cm.convert_to_sql_data(column_value)
                                          if callable(cm.convert_to_sql_data)
                                          else column_value)
            sql_setters.append(f'{column_name} = :{set_param_name}')

        sql_params.update(where_params)

        update_query = f"""
            UPDATE {self._table_name}
                SET {', '.join(sql_setters)}
                WHERE {where}
        """

        if datastore_session:
            update_count = datastore_session.execute_without_result(update_query, sql_params)
        else:
            update_count = self._datastore.execute_without_result(update_query, sql_params)

        if update_count == 0:
            self._log.info(f'{type(obj).__name__}/{obj.id}: Not updated (where: {where}; params: {sql_params})')
        elif update_count > 1:
            self._log.warning(f'{type(obj).__name__}/{obj.id}: Unexpected multiple updates (where: {where}; params: {sql_params})')

        return obj
