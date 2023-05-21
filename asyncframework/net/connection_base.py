# -*- coding: utf-8 -*-
import asyncio
from typing import Optional, Callable
from abc import ABCMeta, abstractmethod
from ..aio.maybefuture import mayBeFuture


__all__ = ['ConnectionBase']


class ConnectionBase(metaclass=ABCMeta):
    """Base class for all connections
    """
    on_close_future: Optional[asyncio.Future] = None
    __on_connection_made: Optional[Callable] = None
    __on_connection_lost: Optional[Callable] = None
    __on_message_received: Optional[Callable] = None
    __on_message_returned: Optional[Callable] = None
    __connected: bool = False

    @property
    def is_connected(self):
        return self.__connected

    def add_callbacks(
            self,
            *args,
            on_connection_made: Optional[Callable] = None,
            on_connection_lost: Optional[Callable] = None,
            on_message_received: Optional[Callable] = None,
            on_message_returned: Optional[Callable] = None,
            **kwargs
    ):
        """Add callbacks

        Args:
            on_connection_made (Optional[Callable], optional): callback to call on connection made. Defaults to None.
            on_connection_lost (Optional[Callable], optional): callback to call on connection lost. Defaults to None.
            on_message_received (Optional[Callable], optional): callback to call on message received. Defaults to None.
            on_message_returned (Optional[Callable], optional): callback to call on message returned. Defaults to None.
        """
        if callable(on_connection_made):
            self.__on_connection_made = on_connection_made
        if callable(on_connection_lost):
            self.__on_connection_lost = on_connection_lost
        if callable(on_message_received):
            self.__on_message_received = on_message_received
        if callable(on_message_returned):
            self.__on_message_returned = on_message_returned

    def connect(self, *args, **kwargs):
        """Start connecting
        """
        if not self.on_close_future or self.on_close_future.done():
            self.on_close_future = asyncio.Future()

    def close(self, *args, **kwargs):
        """Disconnect
        """
        if self.on_close_future and not self.on_close_future.done():
            self.on_close_future.set_result(self)
        self.on_close_future = None
        self.__connected = False

    @abstractmethod
    async def write(self, msg: str, *args, **kwargs):
        """Write function.
        The children need to reimplement this function.

        Args:
            msg (str): the message to send.
        """
        raise NotImplementedError()

    async def on_connection_made(self, transport, *args, **kwargs):
        self.__connected = True
        if self.__on_connection_made:
            await mayBeFuture(self.__on_connection_made, transport, *args, **kwargs)

    async def on_connection_lost(self, exc, *args, **kwargs):
        if self.__on_connection_lost:
            await mayBeFuture(self.__on_connection_lost, exc, *args, **kwargs)
        self.__connected = False

    async def on_message_received(self, msg: str, *args, **kwargs):
        if self.__on_message_received:
            await mayBeFuture(self.__on_message_received, self, msg, *args, **kwargs)

    async def on_message_returned(self, msg: str, *args, **kwargs):
        if self.__on_message_returned:
            await mayBeFuture(self.__on_message_returned, self, msg, *args, **kwargs)
