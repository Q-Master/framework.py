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
        self.assertEquals(tcl.started, False)
        self.assertEquals(tcl.running, False)
        await tcl.start()
        self.assertEquals(tcl.started, True)
        self.assertEquals(tcl.running, False)
        run_future = tcl.run()
        self.assertEquals(tcl.running, False)
        await asyncio.sleep(.1)
        self.assertEquals(tcl.started, True)
        self.assertEquals(tcl.running, True)
        await tcl.stop()
        await asyncio.sleep(.1)
        self.assertEquals(tcl.started, False)
        self.assertEquals(tcl.running, False)
    
    async def test_linear_service(self):
        tcl = TestLinearService(linear=True)
        self.assertEquals(tcl.started, False)
        self.assertEquals(tcl.running, False)
        self.assertEquals(tcl.check, 0)
        await tcl.start()
        self.assertEquals(tcl.started, True)
        self.assertEquals(tcl.running, False)
        self.assertEquals(tcl.check, 10)
        run_future = tcl.run()
        self.assertEquals(tcl.running, False)
        self.assertEquals(tcl.check, 10)
        await asyncio.sleep(.1)
        self.assertEquals(tcl.started, True)
        self.assertEquals(tcl.running, True)
        self.assertEquals(tcl.check, 5)
        await run_future
        self.assertEquals(tcl.started, False)
        self.assertEquals(tcl.running, False)
        self.assertEquals(tcl.check, 0)
