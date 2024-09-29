from typing import Optional, Dict, Any, Union, List

from imagination.decorator.config import EnvironmentVariable
from imagination.decorator.service import Service
from sqlalchemy import text, Engine, create_engine, Connection, TextClause, bindparam, Result, CursorResult


@Service(params=[
    EnvironmentVariable('PSQL_BASE_URL'),
    EnvironmentVariable('PSQL_DBNAME'),
])
class DataStore:
    def __init__(self, base_url: str, db_name: str):
        self._engine: Engine = create_engine(base_url + '/' + db_name, echo=False)

    def connect(self) -> Connection:
        return self._engine.connect()

    def execute_without_result(self,
                               query: str,
                               parameters: Union[None, List[Dict[str, Any]], Dict[str, Any]] = None):
        with self.connect() as c:
            self._execute(c, query, parameters=parameters)
            c.commit()

    def execute(self,
                query: str,
                parameters: Union[None, List[Dict[str, Any]], Dict[str, Any]] = None):
        with self.connect() as c:
            for row in self._execute(c, query, parameters=parameters).fetchall():
                yield row

    # noinspection PyMethodMayBeStatic
    def _execute(self,
                 c: Connection,
                 query: str,
                 parameters: Union[None, List[Dict[str, Any]], Dict[str, Any]] = None):
        tc = text(query)
        if parameters:
            if isinstance(parameters, dict):
                for k, v in parameters.items():
                    # SQLAlchemy only expands the list if it is tuple. So, converting all List or Set objects to Tuples.
                    if isinstance(v, (list, set)):
                        parameters[k] = tuple(v)
            elif isinstance(parameters, (list, tuple, set)):
                for pdict in parameters:
                    for k, v in pdict.items():
                        # SQLAlchemy only expands the list if it is tuple. So, converting all List or Set objects to Tuples.
                        if isinstance(v, (list, set)):
                            pdict[k] = tuple(v)
            return c.execute(tc, parameters)
        else:
            return c.execute(tc)