# -*- coding: utf-8 -*-
import time
import asyncio
from collections import deque


__all__ = ['Throttler']


class Throttler:
    """Async context manager for throttling the function calling"""
    
    def __init__(self, rate_limit, period=1.0, retry_interval=0.01):
        """Constructor

        Args:
            rate_limit (int): the maximum calls per period
            period (float, optional): the period to check. Defaults to 1.0.
            retry_interval (float, optional): loop check retry interval. Defaults to 0.01.
        """
        self.rate_limit = rate_limit
        self.period = period
        self.retry_interval = retry_interval
        self._task_logs = deque()

    def flush(self):
        now = time.time()
        while self._task_logs:
            if now - self._task_logs[0] > self.period:
                self._task_logs.popleft()
            else:
                break

    async def acquire(self):
        while True:
            self.flush()
            if len(self._task_logs) < self.rate_limit:
                break
            await asyncio.sleep(self.retry_interval)
        self._task_logs.append(time.time())

    async def __aenter__(self):
        await self.acquire()

    async def __aexit__(self, exc_type, exc, tb):
        pass
