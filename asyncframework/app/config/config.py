# -*- coding: utf-8 -*-
from typing import Dict, Optional
from platform import node
from packets import makeField
from packets.processors import Hash
from packets.typedef.loglevel_t import loglevel_t
from packets.typedef.int_t import int_t
from packets.typedef.string_t import string_t
from packets.typedef.bool_t import bool_t
from .base import ConfigReader
from ...log import log
from ...log.formatter import LogFormatter


__all__ = ['Config']


class Config(ConfigReader):
    pid_file: Optional[str] = makeField(string_t)

    #logging options
    stdout: bool = makeField(bool_t, default=True)
    syslog: bool = makeField(bool_t, default=False)
    syslog_host: Optional[str] = makeField(string_t)
    syslog_port: Optional[int] = makeField(int_t)
    log_name: str = makeField(string_t, default='')
    log_level: int = makeField(loglevel_t, default='DEBUG')
    log_levels: Dict[str, int] = makeField(Hash(string_t, loglevel_t), default={})
    log_filename: str = makeField(string_t, default='')
    log_format: str = makeField(string_t, default='%(asctime)s.%(msecs)03d %(name)s <%(levelname).1s> %(module)s:%(lineno)d] %(tags)s %(message)s')
    log_format_rsyslog: str = makeField(string_t, default=node() + ' %(name)s:<%(levelname).1s> %(module)s:%(lineno)d] %(tags)s %(message)s')
    log_date_format: str = makeField(string_t, default='%Y-%m-%d %H:%M:%S')     
    log_rotated_amount: int = makeField(int_t, default=1)

    def init_logging(self):
        """Initialize logging using the parameters from config file or defaults
        """
        log.init_logging(
            stdout=self.stdout,
            log_filename=self.log_filename,
            log_name=self.log_name,
            syslog=self.syslog,
            syslog_host=self.syslog_host,
            syslog_port=self.syslog_port,
            log_level=self.log_level,
            log_levels=self.log_levels,
            log_rotated_amount=self.log_rotated_amount,
            formatter=LogFormatter(self.log_format if not self.syslog else self.log_format_rsyslog, self.log_date_format)
        )
