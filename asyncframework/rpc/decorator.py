# -*- coding:utf-8 -*-
from typing import Callable, Dict, Tuple, Any, TypeVar, Union
from ..aio import is_async, set_async, set_if_async


__all__ = ['rpc_methods', 'rpc_method']


rpc_methods: Dict[str, Tuple[Callable, Any]] = {}

_FT = TypeVar('_FT', bound=Callable)

def rpc_method(methods: Dict[str, Tuple[Callable, Any]] = rpc_methods, decorator: Callable[[Callable], Callable] | None = None):
    def wrapper(method: _FT) -> _FT:
        assert method.__name__ not in rpc_methods, f'Duplicate rpc method: {method.__name__}'
        is_a = set_if_async(method)
        if decorator:
            decorated = decorator(method)
            if is_a:
                set_async(decorated)
            methods[method.__name__] = decorated, None
        else:
            methods[method.__name__] = method, None
        return method
    return wrapper
