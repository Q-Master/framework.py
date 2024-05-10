# -*- coding:utf-8 -*-
from typing import Callable, Dict, Tuple, Any
from ..aio import set_if_async


__all__ = ['rpc_methods', 'rpc_method']


rpc_methods: Dict[str, Tuple[Callable, Any]] = {}


def rpc_method(methods: Dict[str, Tuple[Callable, Any]] = rpc_methods, decorator: Callable[[Callable], Callable] | None = None):
    def wrapper(method: Callable):
        print(f'METHOD {method.__name__}')
        assert method.__name__ not in rpc_methods, f'Duplicate rpc method: {method.__name__}'
        set_if_async(method)
        methods[method.__name__] = method if decorator is None else decorator(method), None
        return method
    return wrapper
