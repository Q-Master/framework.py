# -*- coding: utf-8 -*-
from typing import Optional, Dict, Union
import sys
import logging
import logging.handlers
from multiprocessing import Queue
from .formatter import LogFormatter, LoggerTaggingAdapter


__all__ = ['set_levels', 'set_handler', 'init_logging', 'get_logger']


_logger_names = ['']
_listener: Optional[logging.handlers.QueueListener] = None


class FWLogger(logging.Logger):
    def __init__(self, name: str, level=logging.NOTSET):
        super().__init__(_logger_names[0] if _logger_names[0] else name, level)


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
    log_level: Union[int, str] = 'DEBUG',
    log_levels: Optional[dict] = None,
    log_rotated_amount: int = 1,
    formatter: Optional[logging.Formatter] = None,
    is_mutliprocessing: bool = False,
    is_master: bool = False,
    queue: Optional[Queue] = None
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
        is_multiprocessing (bool, optional): the logger will be used in multiprocessing environment (must be set explicitly after config loading)
        is_master (bool, optional): the logger must initialize Queue Listener for this process
        queue (Optional[Queue], optional): queue must be created for master process in `Config.init_logging`
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
        if is_mutliprocessing:
            if queue:
                if is_master:
                    qhandler = logging.handlers.TimedRotatingFileHandler(log_filename, when='midnight', backupCount=log_rotated_amount, encoding='utf-8')
                    qhandler.setFormatter(LogFormatter(fmt='%(message)s'))
                    handler = logging.handlers.QueueHandler(queue)
                    _listener = logging.handlers.QueueListener(queue, qhandler)
                    _listener.start()
                else:
                    handler = logging.handlers.QueueHandler(queue)
            else:
                raise RuntimeError(f'Queue must be set for multiprocessing environments.')
        else:
            handler = logging.handlers.TimedRotatingFileHandler(log_filename, when='midnight', backupCount=log_rotated_amount, encoding='utf-8')

    handler.setFormatter(formatter or LogFormatter())

    if log_name:
        _logger_names[0] = log_name
        logging.setLoggerClass(FWLogger)

    set_handler(handler)
    new_loglevels: Dict[Optional[str], Union[int, str]] = {
        None: log_level
    }
    if log_levels is not None:
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
        name = _logger_names[0]

    if name:
        logger = logging.Logger(name)
        if isinstance(parent, logging.Logger):
            logger.parent = parent
        elif isinstance(parent, LoggerTaggingAdapter):
            logger.parent = parent.logger
        else:
            logger.parent = logging.Logger.root

        return logger
    else:
        return logging.Logger.root


def stop_multiprocessing():
    if _listener:
        _listener.stop()
