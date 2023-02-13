#!/usr/bin/env python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .is_async import is_async


__all__ = ['mayBeFuture']


pool=ThreadPoolExecutor()


def mayBeFuture(f, *args, **kwargs):
    if is_async(f):
        return f(*args, **kwargs)
    else:
        future=pool.submit(f, *args, **kwargs)
        return asyncio.wrap_future(future)
