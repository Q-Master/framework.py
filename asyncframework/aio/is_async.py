# coding=utf-8
import asyncio
from typing import Callable, Union


__all__ = ['is_async', 'IS_ASYNC_ATTR', 'check_is_async', 'set_if_async']


# The attribute for methods which may be marked as async
IS_ASYNC_ATTR: str = '__is_async'


def is_async(impl: Union[Callable, asyncio.Future]) -> bool:
    """Check if `impl` is async or not

    Args:
        impl (Union[Callable, asyncio.Future]): the callable to check

    Returns:
        bool: True if async, else False
    """    
    return asyncio.iscoroutinefunction(impl) or isinstance(impl, asyncio.Future)


def check_is_async(method):
    return hasattr(method, IS_ASYNC_ATTR)


def set_if_async(method):
    if is_async(method):
        setattr(method, IS_ASYNC_ATTR, True)
