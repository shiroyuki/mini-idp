from contextlib import contextmanager
from time import time

from midp.log_factory import midp_logger


@contextmanager
def measure_runtime(label: str, *, enabled: bool = True):
    log = midp_logger('runtime_watch')
    starting_time = time()
    yield
    log.warning(f'{label} // Finished in {time() - starting_time:.6f}s')


def measure_method_runtime(method):
    def inner_decorator(*args, **kwargs):
        with measure_runtime(f'{method.__name__}'):
            return method(*args, **kwargs)

    return inner_decorator
