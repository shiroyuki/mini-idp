import logging
import os

from imagination.debug import get_logger


def get_log_level():
    return getattr(logging, (os.getenv('MIDP_LOG_LEVEL') or 'INFO').upper())


def get_logger_for(name: str) -> logging.Logger:
    log_level = get_log_level()
    return get_logger(name, log_level)


def get_logger_for_object(reference_obj: object) -> logging.Logger:
    cls = type(reference_obj)
    return get_logger_for(f'{cls.__module__}.{cls.__name__}')
