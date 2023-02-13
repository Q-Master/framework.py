# -*- coding:utf-8 -*-
import asyncio
from typing import Any, Iterable, Optional, Dict, Tuple, Callable, TypeVar, Union
from logging import Logger
from packets import PacketWithID
from ..decorator import rpc_methods
from ..rpc import RPC
from ..types import RPCException, Request, Response, WrongConsumer
from ...net.connection_base import ConnectionBase
from ...log.log import get_logger
from ...aio import check_is_async

__all__ = ['RPCPackets']


T = TypeVar('T')


class RPCPackets(RPC[T]):
    log: Logger = get_logger('RPCPackets')
    response_models: Dict[int, PacketWithID] = {}

    def __init__(self, 
        app: T, 
        connection: ConnectionBase, 
        *args, 
        response_models: Optional[Iterable[PacketWithID]] = None, 
        methods: Dict[str, Tuple[Callable, Any]] = rpc_methods, 
        dont_receive=False, 
        **kwargs
        ):
        """Constructor

        Args:
            app (T): the main application to interface with
            connection (ConnectionBase): the rpc connection
            raise_on_unregistered (bool, optional): raise error if the id is not registered. Defaults to True.
            methods (Dict[str, Tuple[Callable, Any]], optional): mapping of id: method used to dispatch the rpc calls. Defaults to rpc_methods.
            response_models (Optional[Iterable[PacketWithID]], optional): `packet.PacketWithID` types for response deserializing. Defaults to None.
            dont_receive (bool, optional): dont receive anything. Defaults to False.        
        """
        super().__init__(app, connection, *args, methods=methods, dont_receive=dont_receive, **kwargs)
        if response_models:
            for packet in response_models:
                self.response_models[packet.__packet_id__] = packet
        else:
            self.response_models = {}

    async def call(
            self,
            request: PacketWithID,
            *args,
            response_required: bool = True,
            correlation_id: Union[None, str] = None,
            wait_timeout: Union[None, int, float] = None,
            **kwargs
    ) -> Any:
        """Call the remote method

        Args:
            request (PacketWithID): _description_
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
        return await super().call(request.dump(), *args, **kwargs)

    async def _dispatch_response(self, future: asyncio.Future, response: Response):
        if response.exception:
            future.set_exception(response.exception)
        else:
            if not self.response_models:
                future.set_result(response.result)

            packet_cls = None
            if isinstance(response.result, dict) and '_' in response.result:
                packet_id: int = response.result['_']
                packet_cls = self.response_models.get(packet_id, None)

            if packet_cls:
                packet = packet_cls.load(response.result)
                future.set_result(packet)
            elif self.raise_on_unregistered:
                raise RPCException(f'There is no model for response:{response.result}')
            else:
                future.set_result(response.result)

    async def _dispatch_request(self, request: Request):
        if not isinstance(request.message, dict) or '_' not in request.message:
            raise Exception(f'No packet id in request: {request.message}')

        packet_id: str = '%s' % request.message['_']
        if packet_id not in self.methods:
            raise WrongConsumer(f'Callable method for {request.message} is not registered')

        method_impl, packet_cls = self.methods[packet_id]
        packet = packet_cls.load(request.message)

        if check_is_async(method_impl):
            result = await method_impl(self.app, packet)
        else:
            result = method_impl(self.app, packet)

        if isinstance(result, PacketWithID):
            result = result.dump()
        return result
