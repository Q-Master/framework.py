
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


class WorkersTestCase(unittest.IsolatedAsyncioTestCase):
    @rpc_method(decorator=external_decorator)
    async def sleepy(self):
        await asyncio.sleep(1.0)

    @rpc_method()
    def not_sleepy(self):
        time.sleep(1.0)

    async def test_is_async(self):
        sleepy_is_async = is_async(self.sleepy)
        self.assertEqual(sleepy_is_async, True)
        not_sleepy_is_not_async = is_async(self.not_sleepy)
        self.assertEqual(not_sleepy_is_not_async, False)
        sleepy_is_async = check_is_async(self.sleepy)
        self.assertEqual(sleepy_is_async, True)
        not_sleepy_is_not_async = check_is_async(self.not_sleepy)
        self.assertEqual(not_sleepy_is_not_async, False)
        sleepy, _ = rpc_methods.get('sleepy', (None, None))
        sleepy_is_async = check_is_async(sleepy)
        self.assertEqual(sleepy_is_async, True)
        not_sleepy, _ = rpc_methods.get('not_sleepy', (None, None))
        not_sleepy_is_not_async = check_is_async(not_sleepy)
        self.assertEqual(not_sleepy_is_not_async, False)
        