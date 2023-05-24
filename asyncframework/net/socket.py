# -*- coding: utf-8 -*-
from typing import Optional, Callable, Tuple
import socket
import asyncio
import traceback
from ssl import SSLContext
from .server_base import ServerBase
from .connection_base import ConnectionBase
from ..log.log import get_logger


__all__ = ['SocketConnection', 'SocketServer', 'new_listen_socket']


_DEFAULT_LIMIT = 2 ** 16  # 64 KiB


def new_listen_socket(host: str, port: int, maxlisten=1024) -> socket.socket:
    """Create new socket which will be set to reuse port and address

    Args:
        host (str): the host address to bind socket to
        port (int): the port to bind socket to
        maxlisten (int, optional): maxlisten option for socket. Defaults to 1024.

    Returns:
        socket.socket: new reused socket
    """
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.set_inheritable(True)
    sock.setblocking(False)
    sock.bind((host, port))
    sock.listen(maxlisten)
    return sock


class SocketConnection(ConnectionBase):
    """Socket connection.
    Used with socket server or as a standalone connection.
    """
    log = get_logger('SocketConnetion')
    __reader: Optional[asyncio.StreamReader] = None
    __writer: Optional[asyncio.StreamWriter] = None
    __consumer_task: Optional[asyncio.Future] = None
    __connection_host: Optional[str] = None
    __connection_port: Optional[int] = None
    __pause_future: Optional[asyncio.Future] = None
    __delimiter: Optional[bytes] = None

    @property
    def host(self) -> Optional[str]:
        return self.__connection_host
    
    @property
    def port(self) -> Optional[int]:
        return self.__connection_port

    def __init__(self, *args, delimiter=None, **kwargs) -> None:
        """Constructor

        Args:
            delimiter (Optional[bytes], optional): optional delimiter to use when receiving data. Defaults to None.
        """
        super().__init__(*args, **kwargs)
        self.__delimiter = delimiter
        self.__reader = None
        self.__writer = None
        self.__consumer_task = None
        self.__connection_host = None
        self.__connection_port = None
        self.__pause_future = None
    
    async def connect_to(self, 
        host: Optional[str] = None, port: Optional[int] = None, limit: int = _DEFAULT_LIMIT, 
        ssl: Optional[SSLContext] = None, ssl_handshake_timeout: Optional[int] = None, 
        family=0, proto=0, flags=0, sock: Optional[socket.socket] = None, 
        local_addr: Optional[Tuple[str, int]] = None, 
        server_hostname: Optional[str] = None):
        """Connect to peer

        Args:
            host (Optional[str], optional): host to connect to. Defaults to None.
            port (Optional[int], optional): port to connect to. Defaults to None.
            limit (int, optional): default stream buffer max size. Defaults to _DEFAULT_LIMIT.
            ssl (Optional[SSLContext], optional): `SSLContext` for the connection if needed. Defaults to None.
            ssl_handshake_timeout (Optional[int], optional): timeout of handshake in seconds. Defaults to None.
            family (int, optional): socket family. Defaults to 0.
            proto (int, optional): socket proto. Defaults to 0.
            flags (int, optional): socket flags. Defaults to 0.
            sock (Optional[socket.socket], optional): already created socket if exists. Defaults to None.
            local_addr (Optional[Tuple[str, int]], optional): tuple of host,port for local connection. Defaults to None.
            server_hostname (Optional[str], optional): if ssl enabled might replace the default hostname. Defaults to None.

        Raises:
            RuntimeError: if ssl not enabled, but server_hostname is given
        """
        if server_hostname and not ssl:
            raise RuntimeError('Server hostname might be set only if ssl context is specified')
        reader, writer = await asyncio.open_connection(
            host=host, port=port, limit=limit, 
            family=family, proto=proto, flags=flags, sock=sock, 
            local_addr=local_addr, server_hostname=server_hostname, 
            ssl_handshake_timeout=ssl_handshake_timeout
            )
        await self.connect(reader, writer)
    
    async def connect(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, *args, **kwargs):
        """Connect with existing `StreamReader` and `StreamWriter`

        Args:
            reader (asyncio.StreamReader): existing `StreamReader`
            writer (asyncio.StreamWriter): existing `StreamWriter`
        """
        super().connect(*args, **kwargs)
        self.__reader = reader
        self.__writer = writer
        ei = self.__writer.get_extra_info('peername')
        self.__connection_host = ei[0]
        self.__connection_port = ei[1]
        self.log.debug(f'Connected to {self.__connection_host}')
        self.__consumer_task = asyncio.ensure_future(self._read_reader())
        await self.on_connection_made(self.__writer.transport)

    async def close(self, *args, is_lost=False, **kwargs):
        """Close the connection

        Args:
            is_lost (bool, optional): the connection is lost. Defaults to False.
        """
        if not self.__pause_future and not is_lost:
            self.pause()
        _, writer, self.__reader, self.__writer = self.__reader, self.__writer, None, None
        if self.__consumer_task and not self.__consumer_task.done():
            self.__consumer_task.cancel()
        writer.close()
        if writer.is_closing() and not is_lost:
            await writer.wait_closed()
        super().close()
        if not is_lost:
            self.log.info(f'Connection to {self.__connection_host}:{self.__connection_port} is closed')
        self.__connection_host = None
        self.__connection_port = None

    async def write(self, msg: str, *args, **kwargs):
        """Wrtite data to stream

        Args:
            msg (str): the message to write to stream

        Raises:
            ConnectionError: if no connection.
        """
        if not self.__writer:
            raise ConnectionError('No connection is made or writer is dead')
        self.__writer.write(msg.encode())
        await self.__writer.drain()
    
    async def _read_reader(self) -> None:
        if not self.__reader:
            raise ConnectionError('No connection is made or reader is dead')
        self.log.debug('Reader started')
        msg: bytes = b''
        try:
            while True:
                if self.__pause_future:
                    await self.__pause_future
                    self.__pause_future = None
                try:
                    if self.__delimiter:
                        msg += await self.__reader.readuntil(self.__delimiter)
                    else:
                        msg += await self.__reader.read(_DEFAULT_LIMIT)
                    self.log.debug(f'Message: {msg.decode()}')
                except asyncio.exceptions.IncompleteReadError:
                    continue
                if not msg:
                    self.log.error(f'Connection from {self.__connection_host}:{self.__connection_port} is lost')
                    await self.on_connection_lost(ConnectionResetError())
                    asyncio.ensure_future(self.close(is_lost=True))
                    break
                await self.on_message_received(msg.decode())
                msg = b''
        except Exception as e:
            self.log.error(f'Reader stopped {traceback.format_exc()}')
            await self.on_connection_lost(e)
        else:
            self.log.debug('Reader stopped.')

    def pause(self):
        """Pause the connection
        """
        if not self.__pause_future or self.__pause_future.done():
            self.__pause_future = asyncio.Future
    
    def resume(self):
        """Resume the connection
        """
        self.__pause_future.set_result(None)


class SocketServer(ServerBase):
    """Socket server
    """
    log = get_logger('SocketServer')
    _host: Optional[str] = None
    _port: Optional[int] = None
    _limit: int = _DEFAULT_LIMIT
    _family = socket.AF_UNSPEC
    _flags = socket.AI_PASSIVE
    _sock: Optional[socket.socket] = None
    _backlog: int = 100
    _reuse_address: Optional[bool] = None
    _reuse_port: Optional[bool] = None
    _ssl: Optional[SSLContext] = None
    _ssl_handshake_timeout: Optional[int] = None
    _server: Optional[asyncio.AbstractServer] = None

    def __init__(
        self, connection_fabric: Callable[[], SocketConnection], *args, 
        host: Optional[str] = None, port: Optional[int] = None, limit: int = _DEFAULT_LIMIT, 
        family = socket.AF_UNSPEC, flags = socket.AI_PASSIVE, sock: Optional[socket.socket] = None, backlog = 100, reuse_address: Optional[bool] = None, reuse_port: Optional[bool] = None,
        ssl: Optional[SSLContext] = None, ssl_handshake_timeout: Optional[int] = None, **kwargs):
        """Constructor

        Args:
            connection_fabric (Callable[[], SocketConnection]): the fabric function that will return new `SocketConnection`.
            host (Optional[str], optional): hostname to serve on. Defaults to None.
            port (Optional[int], optional): port to listen to. Defaults to None.
            limit (int, optional): buffer limit in bytes. Defaults to _DEFAULT_LIMIT.
            family (int, optional): socket family. Defaults to socket.AF_UNSPEC.
            flags (int, optional): socket flags. Defaults to socket.AI_PASSIVE.
            sock (Optional[socket.socket], optional): the already opened socket to listen on. Defaults to None.
            backlog (int, optional): socket backlog. Defaults to 100.
            reuse_address (Optional[bool], optional): if server need to reuse the host address. Defaults to None.
            reuse_port (Optional[bool], optional): if server need to reuse port. Defaults to None.
            ssl (Optional[SSLContext], optional): the `SSLContext` to use with this socket. Defaults to None.
            ssl_handshake_timeout (Optional[int], optional): timeout of ssl handshake. Defaults to None.
        """
        super().__init__(connection_fabric, *args, **kwargs)
        self._host = host
        self._port = port
        self._limit = limit
        self._family = family
        self._flags = flags
        self._sock = sock
        self._backlog = backlog
        self._reuse_address = reuse_address
        self._reuse_port = reuse_port
        self._ssl = ssl
        self._ssl_handshake_timeout = ssl_handshake_timeout
        self._server = None
    
    async def __start__(self, *args, **kwargs):
        self._server = await asyncio.start_server(
            self.on_client_connected,
            host=self._host, port=self._port, limit=self._limit, family=self._family, flags=self._flags, backlog=self._backlog,
            sock=self._sock, reuse_address=self._reuse_address, reuse_port=self._reuse_port,
            ssl=self._ssl, ssl_handshake_timeout=self._ssl_handshake_timeout,
            start_serving=False
        )

    async def __body__(self, *args, **kwargs):
        await self._server.start_serving()  # type: ignore

    async def __stop__(self, *args):
        self._server.close()
        await super().__stop__(*args)
        await self._server.wait_closed()
