# -*- coding: utf-8 -*-
import sys
import os
import logging
import logging.handlers
from typing import Optional, Dict, Union
from .formatter import LogFormatter

__all__ = ['set_levels', 'set_handler', 'init_logging', 'get_logger']


__active_loggers = []
__logger_names = ['']


class FWLogger(logging.Logger):
    def __init__(self, name: str, level=logging.NOTSET):
        super().__init__(__logger_names[0] if __logger_names[0] else name, level)


def set_levels(levels: Dict[Optional[str], Union[int, str]]):
    """Set log levels to all mentioned loggers

    Args:
        levels (Dict[Optional[str], Union[int, str]]): pairs of 'logger name': log level
    """
    for name, level in levels.items():
        logging.getLogger(name).setLevel(level)


def set_handler(handler: logging.Handler):
    """Globally replace the logging handler to the provided one in all loggers

    Args:
        handler (logging.Handler): new logging handler
    """
    for old_handler in logging.root.handlers[:]:
        logging.root.removeHandler(old_handler)
    logging.root.addHandler(handler)


def init_logging(
    stdout: bool = True,
    log_filename: Optional[str] = None,
    syslog: bool = False,
    syslog_host: Optional[str] = 'localhost',
    syslog_port: Optional[int] = 514,
    log_name: Optional[str] = None,
    log_level: str = 'DEBUG',
    log_levels: Optional[dict] = None,
    log_rotated_amount: int = 1,
    formatter: Optional[logging.Formatter] = None
):
    """Initialize logging

    Args:
        stdout (bool, optional): use stdout for output. Defaults to True.
        log_filename (Optional[str], optional): log file name. Defaults to None.
        syslog (bool, optional): use rsyslog for output. Defaults to False.
        syslog_host (Optional[str], optional): rsyslog host. Defaults to None.
        syslog_port (Optional[int], optional): rsyslog port. Defaults to None.
        log_name (Optional[str], optional): logger name. Defaults to None.
        log_level (str, optional): log level. Defaults to 'DEBUG'.
        log_levels (Optional[dict], optional): pairs of 'logger name': log level. Defaults to None.
        log_rotated_amount (int, optional): amount of rotated logs (days to keep log files). Defaults to 1.
        formatter (Optional[logging.Formatter], optional): the formatter used to format log strings. Defaults to None.
    """
    handler: Optional[logging.Handler] = None

    if stdout:
        handler = logging.StreamHandler(sys.stdout)
    elif syslog:
        if syslog_host is None:
            raise RuntimeError(f'rsyslog host address is not set') 
        if syslog_port is None:
            raise RuntimeError(f'rsyslog port is not set')
        if not log_name:
            raise RuntimeError(f'Logger name is not set')
        handler = logging.handlers.SysLogHandler(address=(syslog_host, syslog_port))
    else:
        if not log_filename:
            raise RuntimeError(f'Log filename is not set')
        handler = logging.handlers.TimedRotatingFileHandler(log_filename, when='midnight', backupCount=log_rotated_amount, encoding='utf-8')

    handler.setFormatter(formatter or LogFormatter())

    if log_name:
        set_local_top_logger_name(log_name)
        change_active_logger_names(log_name)
        logging.setLoggerClass(FWLogger)
        change_all_logger_names(log_name)

    set_handler(handler)
    new_loglevels: Dict[Optional[str], Union[int, str]] = {
        None: log_level
    }
    if log_levels is None:
        log_levels = {}
    new_loglevels.update(log_levels)
    set_levels(new_loglevels)


def get_logger(name: Optional[str] = None, parent: Optional[logging.Logger] = None):
    """Get logger

    Args:
        name (str, optional): name of the logger. Defaults to None.
        parent (logging.Logger, optional): parent logger. Defaults to None.

    Returns:
        logging.Logger: logger
    """
    if not name:
        name = sys.modules['__main__'].__file__
        if name:
            name = os.path.split(name)[-1]

    if name:
        if __logger_names[0]:
            name = __logger_names[0]

        logger = logging.Logger(name)
        if isinstance(parent, logging.Logger):
            logger.parent = parent
        else:
            logger.parent = logging.getLogger(parent) if parent else logging.Logger.root  # type: ignore

        __active_loggers.append(logger)

        return logger
    else:
        return logging.Logger.root  # type: ignore


def set_local_top_logger_name(name: str):
    __logger_names[0] = name


def change_active_logger_names(name: str):
    for l in __active_loggers:
        setattr(l, 'name', name)


def change_all_logger_names(name: str):
    logger_dict = logging.Logger.manager.loggerDict
    for v in logger_dict.values():
        if hasattr(v, 'name'):
            v.name = name # type: ignore
