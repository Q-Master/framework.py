# -*- coding: utf-8 -*-
import asyncio
from typing import Optional, Union, List
from logging import Logger
from ..log.log import get_logger


__all__ = ['ReconnectingStream']


DEFAULT_RECONNECT_TIMEOUTS = [0.5, 0.75, 1, 1.5, 2, 3, 5, 8, 10, 15, 30, 60]


class ReconnectingStream(asyncio.streams.FlowControlMixin):
    """Stream protocol which will reconnect upon connection lost
    """
    log: Logger = get_logger('PersistentConnection')
    reconnect_timeout: Union[float, List[float]] = DEFAULT_RECONNECT_TIMEOUTS  # Время ожидания при неудачной попытке подключения

    def __init__(self, host=None, port=None, loop=None, **create_conn_kwargs) -> None:
        super().__init__(loop=loop)
        self.host = host
        self.port = port
        self.loop = loop or asyncio.get_event_loop()
        self.create_conn_kwargs = create_conn_kwargs
        self._closing: bool = False
        self.transport: Optional[asyncio.BaseTransport] = None
        self._closing_future: Union[None, asyncio.Future, asyncio.Task] = None
        self._connect_future: Union[None, asyncio.Future, asyncio.Task] = None

    @classmethod
    async def create_connection(cls, host=None, port=None, loop=None, **create_conn_kwargs):
        conn = cls(host=host, port=port, loop=loop, **create_conn_kwargs)
        await conn.connect()
        return conn

    async def connect(self):
        self.log.debug('Устанавливаем подключение')
        if not self._connect_future or self._connect_future.done():
            self._connect_future = asyncio.Task(self._connect(), loop=self.loop)
        return await self._connect_future

    async def _connect(self) -> bool:
        try:
            idx: int = 0
            timeout: float
            while True:
                try:
                    await self.loop.create_connection(
                        protocol_factory=lambda: self,
                        host=self.host,
                        port=self.port,
                        **self.create_conn_kwargs
                    )
                except ConnectionError as e:
                    self.log.error(f'Connection error {e}')
                    if isinstance(self.reconnect_timeout, list):
                        timeout = self.reconnect_timeout[idx]
                        if idx < len(self.reconnect_timeout):
                            idx += 1
                    else:
                        timeout = self.reconnect_timeout
                    await asyncio.sleep(timeout)
                else:
                    return True
        except asyncio.CancelledError:
            self.log.warning('Connection is cancelled')
            return False

    async def drain(self):
        if self._closing:
            raise ConnectionResetError('Connection is closing')
        await self._drain_helper()

    def connection_made(self, transport: asyncio.BaseTransport):
        self.log.debug(f'Connected succesfully to "{self.host}":{self.port}')
        super().connection_made(transport)
        self._connection_lost = False
        self.transport = transport

    def connection_lost(self, exc: Optional[Exception]):
        super().connection_lost(exc)
        if not self._closing:
            self.log.warning(f'Connection lost ({exc})')
            asyncio.ensure_future(self.connect(), loop=self.loop)
        elif self._closing_future:
            self.log.debug(f'Connection closed')
            self._closing_future.set_result(None)

    async def close(self):
        self.log.debug('Closing the connection')
        self._closing = True
        if self._connect_future and not self._connect_future.done():
            self._connect_future.cancel()

        if self.transport and not self.transport.is_closing():
            self._closing_future = asyncio.Future(loop=self.loop)
            self.transport.close()
            return await self._closing_future
        return None
