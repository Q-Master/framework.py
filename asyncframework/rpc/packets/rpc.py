# -*- coding:utf-8 -*-
import asyncio
from typing import Any, Sequence, Optional, Dict, Tuple, Callable, TypeVar, Union
from logging import Logger
from packets import PacketBase, json
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
    response_models: Dict[str, type[PacketBase]] = {}

    def __init__(self, 
        app: T, 
        connection: ConnectionBase, 
        *args, 
        response_models: Optional[Sequence[type[PacketBase]]] = None, 
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
            response_models (Optional[Sequence[type[PacketBase]]], optional): `packet.PacketBase` types for response deserializing. Defaults to None.
            dont_receive (bool, optional): dont receive anything. Defaults to False.        
        """
        super().__init__(app, connection, *args, methods=methods, dont_receive=dont_receive, **kwargs)
        if response_models:
            for packet in response_models:
                if 'packet_id' in packet.fields_names():
                    self.response_models[f'{packet.packet_id.info.default}'] = packet # type: ignore # if packet_id is in fields names it will be here
        else:
            self.response_models = {}

    async def call(
            self,
            request: PacketBase,
            *args,
            response_required: bool = True,
            correlation_id: Optional[str] = None,
            wait_timeout: Optional[Union[int, float]] = None,
            headers: Optional[Dict[str, Any]] = None,
            app_id: Optional[str] = None,
            **kwargs
    ) -> Any:
        """Call the remote method

        Args:
            request (PacketBase): the packet to be sent as a request.
            response_required (bool, optional): waiting for response or not. Defaults to True.
            correlation_id (str, optional): id for request (auto if None). Defaults to None.
            wait_timeout (int | float, optional): timeout to wait for response. Defaults to None.
            headers (Dict[str, Any], optional): headers for the request. Defaults to None
            app_id (str, optional): application ID for request. Defaults to None
            args: any additional positional arguments for request.
            kwargs: any additional named arguments for request.

        Raises:
            RPCSenderStopped: error if the rpc is stopped by the sender

        Returns:
            Any: the response
        """
        return await super().call(
            request.dump(), 
            *args, 
            response_required=response_required, 
            correlation_id=correlation_id, 
            wait_timeout=wait_timeout, 
            headers=headers, 
            app_id=app_id, 
            **kwargs
        )

    async def _dispatch_response(self, future: asyncio.Future, response: Response):
        if response.exception:
            future.set_exception(response.exception)
        else:
            if not self.response_models:
                future.set_result(response.result)
            else:
                packet_cls = None
                if isinstance(response.result, dict) and '_' in response.result:
                    packet_id: Optional[int] = response.result.get('_', None)
                    if packet_id is not None:
                        packet_cls = self.response_models.get(f'{packet_id}', None)
                    else:
                        packet_cls = None
                
                if packet_cls:
                    packet = packet_cls.load(response.result)
                    future.set_result(packet)
                elif self.raise_on_unregistered:
                    raise RPCException(f'There is no model for response:{response.result}')
                else:
                    future.set_result(response.result)

    async def _dispatch_request(self, request: Request) -> Any:
        if not isinstance(request.method, dict) or '_' not in request.method.keys():
            raise Exception(f'No packet id in request: {request.method}')

        packet_id: str = f'{request.method.get("_", "__NOT_EXISTING_METHOD")}'
        if packet_id not in self.methods:
            if self.raise_on_unregistered:
                raise WrongConsumer(f'Callable method for {request.method} is not registered')
        else:
            method_impl, packet_cls = self.methods[packet_id]
            packet = packet_cls.load(request.method)

            if check_is_async(method_impl):
                result = await method_impl(self.app, packet, correlation_id=request.correlation_id, app_id=request.app_id, headers=request.headers)
            else:
                result = method_impl(self.app, packet, correlation_id=request.correlation_id, app_id=request.app_id, headers=request.headers)
            
            if isinstance(result, PacketBase):
                result = result.dump()
            return result
