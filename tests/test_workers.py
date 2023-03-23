# -*- coding:utf-8 -*-
import unittest
import asyncio
from asyncframework.app import Worker, Manager


class TestWorker(Worker):
    started: bool = False
    running: bool = False

    async def __start__(self, *args, **kwargs):
        self.started = False
        self.running = False
        await asyncio.sleep(.1)

    async def __body__(self, *args, **kwargs):
        self.running = True
        while not self._stopping:
            await asyncio.sleep(.1)
        self.running = False

    async def __stop__(self):
        self.started = False
        self.running = False


class TestManager(Manager):
    def __init__(self, testcase) -> None:
        super().__init__(2)
        self.app = testcase

    async def __start_manager__(self):
        await asyncio.sleep(.1)

    async def __stop_manager__(self):
        await asyncio.sleep(.1)
    
    def __new_worker__(self):
        return TestWorker()

class WorkersTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_workers(self):
        mgr = TestManager(self)
        await mgr.start()
        self.assertEqual(len(mgr._workers_list), 2)
        mgr_future = mgr.run()
        await asyncio.sleep(.5)
        await mgr.stop()
        self.assertEqual(len(mgr._workers_list), 0)
        await mgr_future
