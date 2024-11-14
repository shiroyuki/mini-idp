import traceback
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Union, List, ContextManager

from imagination.decorator.config import EnvironmentVariable
from imagination.decorator.service import Service
from sqlalchemy import text, Engine, create_engine, Connection

from midp.log_factory import get_logger_for_object, get_logger_for


class DataStoreSession:
    def __init__(self, c: Connection):
        self.__id = str(uuid.uuid4())
        self.__log = get_logger_for(f'db.session.{self.__id}')
        self.__c = c

    def execute_without_result(self,
                               query: str,
                               parameters: Union[None, List[Dict[str, Any]], Dict[str, Any]] = None,
                               suppress_error: bool = True) -> int:
        affected_row_count: int = 0
        try:
            result = self._execute(self.__c, query, parameters=parameters)
            # noinspection PyTypeChecker
            affected_row_count = result.rowcount
        except Exception as e:
            self.__log.warning(f'Initiating the rollback...')
            self.__c.rollback()
            self.__log.warning(f'Rollback complete')

            self.close()

            if suppress_error:
                self.__log.warning(f'ATTENTION: The error is suppressed.')
                traceback.print_exc()
            else:
                raise e

        return affected_row_count

    def execute(self,
                query: str,
                parameters: Union[None, List[Dict[str, Any]], Dict[str, Any]] = None):

        for row in self._execute(self.__c, query, parameters=parameters).fetchall():
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

    def commit(self):
        self.__c.commit()
        self.__log.debug("Committed")

    def close(self):
        if not self.__c.closed:
            self.__c.close()
        self.__log.debug("Connection closed")



@Service(params=[
    EnvironmentVariable('PSQL_BASE_URL'),
    EnvironmentVariable('PSQL_DBNAME'),
    EnvironmentVariable('PSQL_VERBOSE',
                        parse_value=lambda v: (v or '') in ('1', 'true'),
                        default=False,
                        allow_default=True),
])
class DataStore:
    def __init__(self, base_url: str, db_name: str, verbose_enabled: bool):
        self._log = get_logger_for_object(self)
        self._engine: Engine = create_engine(
            base_url + '/' + db_name,
            echo=verbose_enabled,
        )

    def connect(self) -> Connection:
        return self._engine.connect()

    def session(self) -> DataStoreSession:
        return DataStoreSession(self._engine.connect())

    @contextmanager
    def in_session(self) -> ContextManager[DataStoreSession]:
        session = self.session()
        yield session
        session.close()

    def execute_without_result(self,
                               query: str,
                               parameters: Union[None, List[Dict[str, Any]], Dict[str, Any]] = None) -> int:
        with self.connect() as c:
            session = DataStoreSession(c)
            result = session.execute_without_result(query=query, parameters=parameters)
            session.commit()

        return result

    def execute(self,
                query: str,
                parameters: Union[None, List[Dict[str, Any]], Dict[str, Any]] = None):
        with self.connect() as c:
            for row in DataStoreSession(c).execute(query=query, parameters=parameters):
                yield row
