
# -*- coding:utf-8 -*-
from typing import Callable
import unittest
import asyncio, time, functools
from asyncframework.aio import is_async, check_is_async
from asyncframework.rpc import rpc_method, rpc_methods


def external_decorator(method: Callable):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        return method(*args, **kwargs)
    return wrapper

@rpc_method(decorator=external_decorator)
async def sleepy():
    await asyncio.sleep(1.0)

@rpc_method()
def not_sleepy():
    time.sleep(1.0)

class WorkersTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_is_async(self):
        global sleepy, not_sleepy
        sleepy_is_async = is_async(sleepy)
        self.assertEqual(sleepy_is_async, True)
        not_sleepy_is_not_async = is_async(not_sleepy)
        self.assertEqual(not_sleepy_is_not_async, False)
        sleepy_is_async = check_is_async(sleepy)
        self.assertEqual(sleepy_is_async, True)
        not_sleepy_is_not_async = check_is_async(not_sleepy)
        self.assertEqual(not_sleepy_is_not_async, False)
        sleepy_, _ = rpc_methods.get('sleepy', (None, None))
        sleepy_is_async = check_is_async(sleepy_)
        self.assertEqual(sleepy_is_async, True)
        not_sleepy_, _ = rpc_methods.get('not_sleepy', (None, None))
        not_sleepy_is_not_async = check_is_async(not_sleepy_)
        self.assertEqual(not_sleepy_is_not_async, False)
        