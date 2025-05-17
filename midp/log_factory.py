import logging
import os

from imagination.debug import get_logger, get_logger_for


def get_log_level():
    return getattr(logging, (os.getenv('MIDP_LOG_LEVEL') or 'INFO').upper())


def midp_logger(name: str) -> logging.Logger:
    return get_logger(name, get_log_level())


def midp_logger_for(reference_obj: object) -> logging.Logger:
    return get_logger_for(reference_obj, get_log_level())
