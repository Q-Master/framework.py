# -*- coding: utf-8 -*-
import asyncio
from abc import ABCMeta, abstractmethod
from typing import Optional


__all__ = ['LineProtocol']


class LineProtocol(asyncio.Protocol, metaclass=ABCMeta):
    _bufer: bytes = b''
    delimiter: bytes = b'\n'
    transport: Optional[asyncio.Transport] = None

    def connection_made(self, transport: asyncio.Transport):
        super().connection_made(transport)
        self.transport = transport

    def connection_lost(self, exc: Optional[Exception]):
        super().connection_lost(exc)

    def data_received(self, data: bytes):
        lines = (self._bufer + data).split(self.delimiter)
        self._bufer = lines.pop()
        for line in lines:
            self.on_line_received(line.decode())

    @abstractmethod
    def on_line_received(self, line: str):
        pass

    def send_line(self, line: str):
        if not self.transport:
            raise ConnectionResetError('Has no transport')

        self.transport.write(b''.join((line.encode(), self.delimiter)))
