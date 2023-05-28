# -*- coding: utf-8 -*-
import asyncio
from typing import List, Any, Callable, Type, Optional
from ..log.log import get_logger
from ..app.service import Service
from ..aio.is_async import is_async
from .connection_base import ConnectionBase


__all__ = ['ServerBase']


class ServerBase(Service):
    """Base class for all servers
    """
    log = get_logger('BaseServer')
    connection_fabric: Callable[[], ConnectionBase]
    client_pool: List[ConnectionBase] = []

    def __init__(self, connection_fabric: Callable[[], ConnectionBase], *args, **kwargs) -> None:
        """Constructor

        Args:
            connection_fabric (Callable): the `ConnectionBase` class fabric
        """
        super().__init__(*args, linear=False, **kwargs)
        self.connection_fabric = connection_fabric
        self.client_pool = []
    
    async def on_client_connected(self, *args, **kwargs):
        """Default callback to call on client connection event
        """
        if is_async(self.connection_fabric):
            client = await self.connection_fabric()
        else:
            client = self.connection_fabric()
        await client.connect(*args, **kwargs)
        self.client_pool.append(client)
        client.on_close_future.add_done_callback(self._on_close)
        asyncio.ensure_future(self.on_accepted(client))

    async def __stop__(self):
        for client in self.client_pool:
            await client.close()
    
    def _on_close(self, client):
        if client in self.client_pool:
            self.client_pool.remove(client)
        asyncio.ensure_future(self.on_closed(client))

    async def on_accepted(self, client: ConnectionBase):
        """On accepted conneciton callback

        Args:
            client (ConnectionBase): accepted client
        """
        pass
    
    async def on_closed(self, client: ConnectionBase):
        """On closed connection callback

        Args:
            client (ConnectionBase): client which conneciton is closed to
        """
        pass
    
