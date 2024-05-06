# -*- coding:utf-8 -*-
import asyncio
import traceback
from typing import Union, Any, Dict, Optional, Iterable, TypeVar, Generic, Callable, Tuple
from itertools import chain
from logging import Logger
from uuid import uuid4
from packets import json
from .decorator import rpc_methods
from ..aio import check_is_async
from .types import MessageType, Request, Response, RPCSenderStopped, WrongConsumer, RPCDispatcherStopped, RPCException, NotToHandle
from ..net.connection_base import ConnectionBase
from ..log.log import get_logger


__all__ = ['RPC']


T = TypeVar('T')


class RPC(Generic[T]):  # pylint: disable=unsubscriptable-object
    log: Logger = get_logger('RPC')
    wait_response_futures: Dict[str, asyncio.Future] = {}
    receive_request_futures: Dict[str, asyncio.Future] = {}
    methods: Dict[str, Tuple[Callable, Any]] = {}

    def __init__(self, 
        app: T, 
        connection: ConnectionBase, 
        *args, 
        raise_on_unregistered: bool = True, 
        methods: Dict[str, Tuple[Callable, Any]] = rpc_methods, 
        dont_receive=False, 
        **kwargs) -> None:
        """Constructor

        Args:
            app (T): the main application to interface with
            connection (ConnectionBase): the rpc connection
            raise_on_unregistered (bool, optional): raise error if the id is not registered. Defaults to True.
            methods (Dict[str, Tuple[Callable, Any]], optional): mapping of id: method used to dispatch the rpc calls. Defaults to rpc_methods.
            dont_receive (bool, optional): dont receive anything. Defaults to False.
        """
        super().__init__(*args, **kwargs)  # type: ignore
        self.app: T = app
        self.connection = connection
        self.connection.add_callbacks(
            on_message_received=self._message_received,
            on_message_returned=self._message_returned,
            on_connection_lost=self._on_connection_lost,
        )
        self.raise_on_unregistered = raise_on_unregistered
        self.methods = methods
        self.dont_receive = dont_receive
        self.wait_response_futures = {}
        self.receive_request_futures = {}
        self.stopped: bool = False

    @property
    def unclosed_futures(self) -> Iterable:
        """List all unclosed futures (requests and dispatches)

        Returns:
            Iterable: the iterable containing all not done futures
        """
        return filter(lambda f: not f.done(), chain(self.wait_response_futures.values(), self.receive_request_futures.values()))

    async def send(self, request, *args, **kwargs):
        await self.call(request, *args, response_required = True, **kwargs)

    async def call(
            self,
            request,
            *args,
            response_required: bool = True,
            correlation_id: Union[None, str] = None,
            wait_timeout: Union[None, int, float] = None,
            headers: Union[None, Dict[str, Any]] = None,
            app_id: Union[None, str] = None,
            **kwargs
    ) -> Any:
        """Call the remote method

        Args:
            request (Any): serializable (method name or packet)
            response_required (bool, optional): waiting for response or not. Defaults to True.
            correlation_id (Union[None, str], optional): id for request (auto if None). Defaults to None.
            wait_timeout (Union[None, int, float], optional): timeout to wait for response. Defaults to None.
            args: any additional positional arguments for request.
            kwargs: any additional named arguments for request.

        Raises:
            RPCSenderStopped: error if the rpc is stopped by the sender

        Returns:
            Any: the response
        """
        if self.stopped:
            raise RPCSenderStopped(f'RPC is closed')

        assert not (response_required and wait_timeout), 'We are not waiting for result, but `wait_timeout` is set'
        assert isinstance(correlation_id, str) or correlation_id is None, (correlation_id, type(correlation_id))

        correlation_id = correlation_id or self._next_request_id()
        req = Request(message=request, correlation_id=correlation_id, response_required=response_required, headers=headers, app_id=app_id, args=args, kwargs=kwargs)

        self.log.debug(f'Sending RPC request correlation_id: {correlation_id}, need_response: {"True" if response_required else "False"}, request: {request}, args: {args}, kwargs: {kwargs}')
        await self._write(req)
        self.log.debug(f'RPC request sent. correlation_id: {correlation_id}')

        if response_required:
            def _on_done(_):
                del self.wait_response_futures[correlation_id]
            
            future: asyncio.Future = asyncio.Future()
            self.wait_response_futures[correlation_id] = future
            future.add_done_callback(_on_done)
            if wait_timeout:
                try:
                    result = await asyncio.wait_for(future, wait_timeout)
                except asyncio.TimeoutError:
                    self.log.error(f'Timeout waiting for reply. correlation_id: {correlation_id}, timeout: {wait_timeout}')
                    raise
                except asyncio.CancelledError:
                    self.log.error(f'Request cancelled. correlation_id: {correlation_id}')
                    raise
            else:
                result = await future
            self.log.debug(f'RPC completed. correlation_id: {correlation_id}')
            return result

    async def stop(self, wait_timeout: Optional[int] = None):
        self.log.info('Stopping RPC')
        self.stopped = True
        fs = tuple(self.unclosed_futures)
        if fs:
            _, pending = await asyncio.wait(fs, timeout=wait_timeout)
            if pending:
                self.log.error(f'Some tasks are remaining unclosed ({len(pending)}). Cancelling.')
                for future in pending:
                    future.cancel()
        if self.connection.is_connected:
            self.connection.close()
        self.log.info('RPC stopped')

    async def _recv_request(
            self,
            request: Request,
            *args, **kwargs
    ) -> None:
        """Receive the incoming request

        Args:
            request (Request): the incoming request
        """
        def on_done(_):
            del self.receive_request_futures[request.correlation_id]

        self.log.debug(f'Received the request. correlation_id: {request.correlation_id}, request: {request.message}')
        if self.dont_receive:
            self.log.debug('Ignoring the request. dont_receive is True')
            return
        future = asyncio.Task(self._process_request(request, *args, **kwargs))
        self.receive_request_futures[request.correlation_id] = future
        future.add_done_callback(on_done)

        try:
            await future
        except asyncio.CancelledError:
            self.log.error(f'Receiving is cancelled. correlation_id: {request.correlation_id}')

    async def _recv_response(
            self,
            response: Response,
            *args, **kwargs
    ) -> None:
        """Receive the incoming response

        Args:
            response (Response): the incoming response
        """
        future: Optional[asyncio.Future] = self.wait_response_futures.get(response.correlation_id, None)

        if not future:
            if self.raise_on_unregistered:
                self.log.error(f'Future for correlation_id: {response.correlation_id} not found')
        elif future.done():
            self.log.error(f'Request is already complete. correlation_id: {response.correlation_id}')
        else:
            await self._dispatch_response(future, response)

    @staticmethod
    def _next_request_id() -> str:
        """Generate next request id

        Returns:
            str: uuid4 as an request id
        """
        return uuid4().hex

    def _load_message(self, msg: str, **kwargs) -> Union[Request, Response]:
        js: dict = json.loads(msg)
        message_type = js.get('message_type', None)
        if message_type == MessageType.MSG_REQUEST.value:
            result = Request.load(js)
        elif message_type == MessageType.MSG_RESPONSE.value:
            result = Response.load(js)
        else:
            raise Exception(f'Unknown message type received {message_type}')
        if 'correlation_id' in kwargs:
            result.correlation_id = kwargs['correlation_id']
        if 'headers' in kwargs:
            result.headers = kwargs['headers']
        if 'app_id' in kwargs:
            result.app_id = kwargs['app_id']


    async def _message_received(self, instance: ConnectionBase, msg: str, *args, **kwargs):
        """Callback on incoming message from transport

        Args:
            msg (str): the incoming message
        """
        try:
            loaded_msg = self._load_message(msg, **kwargs)
            if loaded_msg.message_type == MessageType.MSG_REQUEST:
                await self._recv_request(loaded_msg, *args, **kwargs)
            elif loaded_msg.message_type == MessageType.MSG_RESPONSE:
                await self._recv_response(loaded_msg, *args, **kwargs)
        except Exception as e:
            self.log.error(f'Error parsing message: {msg}, exception: {e}, traceback: {traceback.format_exc()}')

    async def _message_returned(self, msg: str, *args, **kwargs):
        """Callback on message returned by the transport

        Args:
            msg (str): returned message
        """ 
        try:
            loaded_msg = self._load_message(msg, **kwargs)
            if loaded_msg.message_type == MessageType.MSG_REQUEST:
                await self._recv_response(
                    Response(
                        exception=f'Request not delivered. correlation_id: {loaded_msg.correlation_id}',
                        correlation_id=loaded_msg.correlation_id,
                    )
                )
            elif loaded_msg.message_type == MessageType.MSG_RESPONSE:
                self.log.error(f'Response not delivered. correlation_id: {loaded_msg.correlation_id}, msg: {loaded_msg.message}')
        except Exception as e:
            self.log.error(f'Error parsing the message: {msg}, exception: {e}, traceback: {traceback.format_exc()}')

    async def _on_connection_lost(self, exc, *args, **kwargs):
        """Callback on connection lost from transport

        Args:
            exc (Exception): the exception caught.
        """
        await self.stop()
        #for future in self.unclosed_futures:
        #    future.set_exception(RPCException(f"Connection lost: {exc}"))

    async def _process_request(
            self,
            request: Request,
            *args, **kwargs
    ) -> None:
        """Process the incoming request

        Args:
            request (Request): incoming request
        """
        self.log.debug(f'Request received. correlation_id: {request.correlation_id}, request: {request.message}')
        exception = None
        result = None

        if self.stopped and request.response_required:
            await self._write(Response(exception=RPCDispatcherStopped('RPC is closed'), correlation_id=request.correlation_id), *args, **kwargs)
            return

        try:
            result = await self._dispatch_request(request)
            self.log.debug(f'RPC is complete. correlation_id: {request.correlation_id}, result: {result}', request.correlation_id, result)
        except WrongConsumer as e:
            if self.raise_on_unregistered:
                exception = RPCException(message=e.message)
            else:
                self.log.error(f'RPC request cant be processed. No dispatcher for it: {e}')
                return
        except NotToHandle:
            return
        except RPCException as e:
            exception = e
        except Exception as e:
            exception = RPCException(message=str(e), traceback=traceback.format_exc())

        if exception:
            self.log.error(f'RPC function exception. correlation_id: {request.correlation_id}, exception: {exception}')

        if request.response_required:
            self.log.debug(f'Replying to RPC. correlation_id: {request.correlation_id}')
            response = Response(result=result, exception=exception, correlation_id=request.correlation_id)
            await self._write(response, *args, **kwargs)

    async def _write(self, msg, *args, **kwargs):
        """Send message to transport.
        Might be overloaded to process the message before sending
        """
        await self.connection.write(msg.dumps(), *args, headers=msg.headers, correlation_id=msg.corellation_id, app_id=msg.app_id, **kwargs)
        
    async def _dispatch_request(self, request: Request):
        """Dispatching the received request.
        Will call the corresponding function. Might be overloaded in children to implement own dispatching mechanisms.

        Args:
            request (Request): the incoming request.

        Raises:
            WrongConsumer: raise if can't dispatch the request. The corresponding RPC function is not registered.

        Returns:
            Any: the result of a function
        """
        self.log.debug('Request %s', request)
        if request.message not in self.methods:
            raise WrongConsumer(f'Callable method for {request.message} is not registered')

        method_impl, _ = self.methods[request.message]
        if check_is_async(method_impl):
            return await method_impl(self.app, *request.args, request.correlation_id, request.app_id, request.headers, **request.kwargs)
        else:
            return method_impl(self.app, *request.args, request.correlation_id, request.app_id, request.headers, **request.kwargs)

    async def _dispatch_response(self, future: asyncio.Future, response: Response):
        if response.exception:
            future.set_exception(response.exception)
        else:
            future.set_result(response.result)
