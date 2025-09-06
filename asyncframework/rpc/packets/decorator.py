# -*- coding:utf-8 -*-
from typing import Type, Callable, TypeVar
from packets import PacketBase
from ...aio import set_if_async
from ..decorator import rpc_methods


__all__ = ['rpc_packet']


_FT = TypeVar('_FT', bound=Callable)

def rpc_packet(packet_cls: Type[PacketBase], methods = rpc_methods):
    """Decorator for adding methods to packet RPC

    Args:
        packet_cls (Type[PacketBase]): packet type to use to serialize
        methods (Dict[str, Tuple[Callable, Any]], optional): array of mapping str: Callable. Defaults to rpc_methods.
    """
    def decorator(method: _FT) -> _FT:
        set_if_async(method)
        if 'packet_id' in packet_cls.fields_names():
            methods[f'{packet_cls.packet_id.info.default}'] = method, packet_cls # type: ignore # if packet_id is in fields names it will be here
        return method
    return decorator
