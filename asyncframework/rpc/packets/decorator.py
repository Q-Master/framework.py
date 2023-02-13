# -*- coding:utf-8 -*-
from typing import Type, Callable
from packets import PacketBase
from ...aio import set_if_async
from ..decorator import rpc_methods


__all__ = ['rpc_packet']


def rpc_packet(packet_cls: Type[PacketBase], methods = rpc_methods):
    """Decorator for adding methods to packet RPC

    Args:
        packet_cls (Type[PacketBase]): packet type to use to serialize
        methods (Dict[str, Tuple[Callable, Any]], optional): array of mapping str: Callable. Defaults to rpc_methods.
    """
    def decorator(method: Callable):
        set_if_async(method)
        methods[f'{packet_cls.__packet_id__}'] = method, packet_cls
        return method
    return decorator
