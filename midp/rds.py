import traceback
from typing import Dict, Any, Union, List

from imagination.decorator.config import EnvironmentVariable
from imagination.decorator.service import Service
from sqlalchemy import text, Engine, create_engine, Connection

from midp.log_factory import get_logger_for_object


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

    def execute_without_result(self,
                               query: str,
                               parameters: Union[None, List[Dict[str, Any]], Dict[str, Any]] = None) -> int:
        affected_row_count: int = 0
        with self.connect() as c:
            try:
                result = self._execute(c, query, parameters=parameters)
                # noinspection PyTypeChecker
                affected_row_count = result.rowcount
                c.commit()
            except Exception as e:
                traceback.print_exc()
                self._log.warning(f'Initiating the rollback...')
                c.rollback()
                self._log.warning(f'Rollback complete')
        return affected_row_count

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
