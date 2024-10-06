import json
from dataclasses import is_dataclass, asdict
from typing import Generic, TypeVar, Any, Dict, Optional, Generator, Callable, List, Type

from pydantic import BaseModel

from midp.rds import DataStore

T = TypeVar('T')


class InsertError(RuntimeError):
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
        self._datastore = datastore
        self._model_class = model_class
        self._table_name = table_name
        self._column_mappings: Dict[str, _ColumnMapping] = dict()
        self._reverse_column_mappings: Dict[str, str] = dict()

    def column(self,
               property_name: str,
               column_name: Optional[str] = None,
               convert_to_property_data: Optional[Callable[[Any], Any]] = None,
               convert_to_sql_data: Optional[Callable[[Any], Any]] = None,
               cast_to_sql_type: Optional[str] = None):
        """ Define a column mapping for the primary table. """
        column_name = column_name or property_name
        self._column_mappings[property_name] = _ColumnMapping(column_name=column_name or property_name,
                                                              convert_to_property_data=convert_to_property_data,
                                                              convert_to_sql_data=convert_to_sql_data,
                                                              cast_to_sql_type=cast_to_sql_type)
        self._reverse_column_mappings[column_name] = property_name
        return self

    def column_as_json(self, property_name: str, column_name: Optional[str] = None):
        return self.column(property_name=property_name,
                           column_name=column_name,
                           convert_to_sql_data=lambda v: json.dumps(self._convert_to_serializable_obj(v)),
                           cast_to_sql_type='jsonb')

    def _convert_to_serializable_obj(self, given_value: Any) -> Any:
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

    def map_row(self, row: Dict[str, Any]) -> T:
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

    def delete(self,
               where: Optional[str] = None,
               parameters: Optional[Dict[str, Any]] = None) -> int:
        query = f'DELETE FROM {self._table_name}'

        if where:
            query = f'{query} WHERE {where}'

        return self._datastore.execute_without_result(query, parameters)

    def add(self, obj: T) -> T:
        return self.simple_insert(obj)

    def simple_insert(self, obj: T) -> T:
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
        """

        if self._datastore.execute_without_result(insert_query, sql_params) == 0:
            raise InsertError(obj)

        return obj

    def simple_update(self,
                      obj: T,
                      where: Optional[str] = None,
                      where_params: Optional[Dict[str, Any]] = None) -> T:
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

        if self._datastore.execute_without_result(update_query, sql_params) == 0:
            raise InsertError(obj)

        return obj
