# -*- coding: utf-8 -*-
import asyncio
from typing import Optional
from abc import ABCMeta, abstractmethod


__all__ = ['Service', 'ServiceFailedException']


class ServiceFailedException(Exception):
    """Exception on failing to start"""
    pass


class Service(metaclass=ABCMeta):
    """Base class for all services"""
    _started: bool
    _stopping: bool
    _stop_waiter: Optional[asyncio.Future]
    __run_future: Optional[asyncio.Future]
    __ioloop: Optional[asyncio.AbstractEventLoop]
    __linear: bool

    @property
    def ioloop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self.__ioloop

    def __init__(self, *args, linear = False, **kwargs) -> None:
        """Constructor

        Args:
            linear (bool, optional): if set forces to call `stop` after `__body__` exits. Defaults to False.
        """
        super().__init__(*args, **kwargs)
        self._started = False
        self._stopping = False
        self._stop_waiter = None
        self.__run_future = None
        self.__ioloop = None
        self.__linear = linear

    async def start(self, ioloop: Optional[asyncio.AbstractEventLoop] = None, *args, **kwargs):
        """Start service

        Args:
            ioloop (asyncio.AbstractEventLoop): async ioloop.
        """        
        self._started = True
        self._stopping = False
        self.__ioloop = ioloop or asyncio.get_event_loop()
        await self.__start__(*args, **kwargs)

    def run(self, *args, **kwargs) -> asyncio.Future:
        """Run service

        Raises:
            ServiceFailedException: failed to start `__body`.

        Returns:
            asyncio.Future: future to wait for service to complete run.
        """        
        self.__run_future = asyncio.ensure_future(self.__run(*args, **kwargs))
        if self.__run_future:
            return self.__run_future
        else:
            raise ServiceFailedException('Task not started somehow')

    async def __run(self, *args, **kwargs):
        self._stop_waiter = asyncio.Future()
        stop_args_future = asyncio.ensure_future(self.__body__(*args, **kwargs))
        if self.__linear:
            stop_args_future.add_done_callback(self._fire_stop_waiter)
        if self._started:
            await self._stop_waiter
            await stop_args_future
            if self.__linear:
                await self._stop()

    def _fire_stop_waiter(self, ft: Optional[asyncio.Future] = None):
        self._stopping = True
        if self._stop_waiter and not self._stop_waiter.done():
            self._stop_waiter.set_result(True)

    async def stop(self):
        """Stop service"""        
        if self._started:
            self._fire_stop_waiter()
            await self._stop()
            await self.__run_future

    async def _stop(self):
        await self.__stop__()
        self._started = False
        del self._stop_waiter

    @abstractmethod
    async def __start__(self, *args, **kwargs):
        """Start function.
        Need to be implemented to do anything on service start.
        """        
        raise NotImplementedError('Must be implemented')

    async def __body__(self, *args, **kwargs):
        """Body function.
        Might be implemented in children. This is the main service function called when `run()`.
        """
        pass

    @abstractmethod
    async def __stop__(self):
        """Stop function.
        Need to be implemented to stop service.
        """
        raise NotImplementedError('Must be implemented')
