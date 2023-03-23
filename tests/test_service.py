# -*- coding:utf-8 -*-
import unittest
import asyncio
from asyncframework.app import Service

class TestService(Service):
    started: bool = False
    running: bool = False

    async def __start__(self, *args, **kwargs):
        await asyncio.sleep(.1)
        self.started = True

    async def __body__(self, *args, **kwargs):
        self.running = True
        while not self._stopping:
            await asyncio.sleep(.1)
        self.running = False

    async def __stop__(self):
        self.started = False
        self.running = False


class TestLinearService(Service):
    started: bool = False
    running: bool = False
    check: int = 0

    async def __start__(self, *args, **kwargs):
        await asyncio.sleep(.1)
        self.started = True
        self.check = 10

    async def __body__(self, *args, **kwargs):
        self.running = True
        self.check = 5
        await asyncio.sleep(.2)
        self.running = False

    async def __stop__(self):
        self.started = False
        self.running = False
        self.check = 0


class ServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_service(self):
        tcl = TestService()
        self.assertEqual(tcl.started, False)
        self.assertEqual(tcl.running, False)
        await tcl.start()
        self.assertEqual(tcl.started, True)
        self.assertEqual(tcl.running, False)
        run_future = tcl.run()
        self.assertEqual(tcl.running, False)
        await asyncio.sleep(.1)
        self.assertEqual(tcl.started, True)
        self.assertEqual(tcl.running, True)
        await tcl.stop()
        await asyncio.sleep(.1)
        self.assertEqual(tcl.started, False)
        self.assertEqual(tcl.running, False)
    
    async def test_linear_service(self):
        tcl = TestLinearService(linear=True)
        self.assertEqual(tcl.started, False)
        self.assertEqual(tcl.running, False)
        self.assertEqual(tcl.check, 0)
        await tcl.start()
        self.assertEqual(tcl.started, True)
        self.assertEqual(tcl.running, False)
        self.assertEqual(tcl.check, 10)
        run_future = tcl.run()
        self.assertEqual(tcl.running, False)
        self.assertEqual(tcl.check, 10)
        await asyncio.sleep(.1)
        self.assertEqual(tcl.started, True)
        self.assertEqual(tcl.running, True)
        self.assertEqual(tcl.check, 5)
        await run_future
        self.assertEqual(tcl.started, False)
        self.assertEqual(tcl.running, False)
        self.assertEqual(tcl.check, 0)
