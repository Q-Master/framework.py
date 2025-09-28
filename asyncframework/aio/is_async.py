# coding=utf-8
from typing import Callable, Union, Awaitable, Any
import asyncio
from types import CoroutineType
from collections.abc import Coroutine
from types import MethodType, BuiltinMethodType, FunctionType, CoroutineType


__all__ = ['is_async', 'IS_ASYNC_ATTR', 'check_is_async', 'set_if_async', 'set_async', 'await_result_if_async']


# The attribute for methods which may be marked as async
IS_ASYNC_ATTR: str = '__is_async'

def is_async(impl: Union[Callable, asyncio.Future, Awaitable]) -> bool:
    """Check if `impl` is async or not

    Args:
        impl (Union[Callable, asyncio.Future]): the callable to check

    Returns:
        bool: True if async, else False
    """    
    if isinstance(impl, (MethodType, BuiltinMethodType, FunctionType)):
        return asyncio.iscoroutinefunction(impl)
    else:
        return isinstance(impl, asyncio.Future)


def check_is_async(method):
    return hasattr(method, IS_ASYNC_ATTR)


async def await_result_if_async(result: Union[Awaitable, Any]):
    if isinstance(result, (CoroutineType, Coroutine, asyncio.Future)):
        return await result
    else:
        return result


def set_if_async(method) -> bool:
    if is_async(method):
        set_async(method)
        return True
    return False


def set_async(method):
    setattr(method, IS_ASYNC_ATTR, True)