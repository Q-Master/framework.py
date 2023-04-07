# -*- coding: utf-8 -*-
import traceback
import weakref
import signal
import os.path
from typing import Dict, Optional
from itertools import chain
from platform import node
from packets import Field, Packet
from packets._packetbase import PacketMeta
from packets import json
from packets.processors import Hash, log_level_t, int_t, string_t, bool_t
from .base import ConfigProtocolBase, ConfigTableProtocolBase
from ...log import log
from ...log.formatter import LogFormatter
from ...util.ro import ReadOnly


__all__ = ['Config']


class Config(ConfigProtocolBase):
    pid_file: Optional[str] = Field(string_t)  # type: ignore

    #logging options
    stdout: bool = Field(bool_t, default=True)  # type: ignore
    syslog: bool = Field(bool_t, default=False)  # type: ignore
    syslog_host: Optional[str] = Field(string_t)  # type: ignore
    syslog_port: Optional[int] = Field(int_t)  # type: ignore
    log_name: str = Field(string_t, default='')  # type: ignore
    log_level: str = Field(log_level_t, default='debug')  # type: ignore
    log_levels: Dict[str, int] = Field(Hash(string_t, log_level_t), default={})  # type: ignore
    log_filename: str = Field(string_t, default='')  # type: ignore
    log_format: str = Field(string_t, default='%(asctime)s.%(msecs)03d %(name)s <%(levelname).1s> %(module)s:%(lineno)d] %(tags)s %(message)s')  # type: ignore
    log_format_rsyslog: str = Field(string_t, default=node() + ' %(name)s:<%(levelname).1s> %(module)s:%(lineno)d] %(tags)s %(message)s')  # type: ignore
    log_date_format: str = Field(string_t, default='%Y-%m-%d %H:%M:%S')   # type: ignore    
    log_rotated_amount: int = Field(int_t, default=1)  # type: ignore

    def on_reconfigure_signal(self):
        """Callback, which will be run on getting signal from `enable_reconfiguration_signal` (reread configuration) signal"""
        pass

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

    def _on_reload_signal(self):
        self.log.debug('Reloading configuration')
        try:
            self.reload()
            self.on_reconfigure_signal()
        except Exception as e:
            self.log.error(f'Error reloading configuration {traceback.format_exc(e)}')
            os.kill(os.getpid(), signal.SIGTERM)
        self.log.info('Configuration reloaded successfully')

    def enable_reconfiguration_signal(self, signal_no=signal.SIGUSR1):
        """Call this to set the callback on reconfiguration signal

        Args:
            signal_no (signal.Signals, optional): the signal to set the reconfiguration callback on. Defaults to signal.SIGUSR1.
        """        
        signal.signal(signal_no, lambda *_: self._on_reload_signal())
