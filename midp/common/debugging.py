from contextlib import contextmanager
from time import time

from midp.log_factory import get_logger_for


@contextmanager
def measure_runtime(label: str, *, enabled: bool = True):
    log = get_logger_for('runtime_watch')
    starting_time = time()
    yield
    log.warning(f'{label} // Finished in {time() - starting_time:.6f}s')


def measure_method_runtime(method):
    def inner_decorator(*args, **kwargs):
        with measure_runtime(f'{method.__name__}'):
            return method(*args, **kwargs)

    return inner_decorator
