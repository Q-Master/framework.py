# -*- coding: utf-8 -*-
import asyncio
from typing import Dict, List, Optional, Any
from enum import Enum
from abc import abstractmethod
from multiprocessing import Process, current_process
from signal import SIGINT, SIGTERM, SIG_IGN, signal
from .proctitle import set_process_name
from .try_uvloop import *
from .service import Service
from ..aio.maybefuture import mayBeFuture
from ..log.log import get_logger


__all__ = ['ManagerTypes', 'Manager', 'Worker']


class ManagerTypes(Enum):
    """Type of the manager.
    ONESHOT will run worker once.
    RESTART will try to restart worker when it exits.
    NO_START lazy mode. No workers started on service start and need to be created manually via `create_worker`
    """
    ONESHOT = 1
    RESTART = 2
    NO_START = 3


class Worker(Service):
    """Worker parent class."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, linear=True, **kwargs)

    def __call__(self, *args, **kwargs):
        name = current_process().name
        if name:
            set_process_name(name)
        ioloop = new_event_loop()
        signal(SIGINT, SIG_IGN)  # worker'ы убиваются из основного процесса STGTERM'ом
        ioloop.add_signal_handler(SIGTERM, self._fire_stop_waiter)
        ioloop.run_until_complete(self.__work(ioloop, *args, **kwargs))
        ioloop.stop()
        ioloop.close()

    async def __work(self, ioloop, *args, **kwargs):
        await self.start(ioloop, *args, **kwargs)
        await self.run(*args, **kwargs)


class Manager(Service):
    """Multiprocess manager class"""

    log = get_logger('Manager')
    _workers_count: int
    _sleep_time: float
    _manager_type: ManagerTypes = ManagerTypes.RESTART
    _workers_list: List[Process] = []
    wargs: List[Any] = []
    wkwargs: Dict[Any, Any] = {}
    __workers_run_future: Optional[asyncio.Future] = None

    def __init__(self, workers_count: int, sleep_time: Optional[float] = None, manager_type: ManagerTypes = ManagerTypes.RESTART) -> None:
        """Constructor

        Args:
            workers_count (int): maximum workers amount.
            sleep_time (float, optional): time to sleep between worker live checks. Defaults to None.
            manager_type (ManagerTypes, optional): type of workers starting/restarting. Defaults to `ManagerTypes.RESTART`.
        """
        super().__init__()
        self._workers_count = workers_count
        self._sleep_time = sleep_time or 1.0 / self._workers_count
        self._manager_type = manager_type
        self._workers_list = []
        self.wargs = []
        self.wkwargs = {}
        self.__workers_run_future = None

    def create_worker(self):
        if self._manager_type != ManagerTypes.NO_START:
            raise RuntimeError(u'Workers cant be created manually in case of not `ManagerTypes.NO_START`')
        if not self._started:
            raise RuntimeError(u'Manager is not running')
        return self.__start_worker()

    async def __start__(self):
        """Start the manager"""
        await self.__start_manager__()
        self.log.debug(u'Start %s workers args %s, kwargs %s', self._workers_count, self.wargs, self.wkwargs)

        self.__workers_run_future = asyncio.Future(loop=self.ioloop)
        if self._manager_type != ManagerTypes.NO_START:
            for _ in range(self._workers_count):
                self.__start_worker()

    async def __body__(self):
        """Manager's `__body__` is used to check workers aliveness."""
        async def checker():
            for process in self._workers_list:
                if not process.is_alive():
                    process.join()
                    self._workers_list.remove(process)
                    await self.__worker_ended(process)
            await asyncio.sleep(self._sleep_time)

        if self._manager_type == ManagerTypes.NO_START:
            while not self._stopping:
                await checker()
        else:
            while self._workers_list:
                await checker()
        if self.__workers_run_future and not self.__workers_run_future.done():
            self.__workers_run_future.set_result(True)

    async def __stop__(self):
        """Stop the worker"""
        self.log.info(u'Stopping workers')
        for process in self._workers_list:
            self.log.info(f'Killing worker {process.pid}')
            process.terminate()
        await self.__workers_run_future
        await self.__stop_manager__()

    def __start_worker(self):
        """Start the worker process

        Returns:
            Process: the worker process descriptor
        """ 
        if self._manager_type == ManagerTypes.NO_START and len(self._workers_list) >= self._workers_count:
            self.log.warn(f'Cant start any more workers ({self._workers_count})')
            return None
        self.log.info('Starting worker')
        worker = self.__new_worker__()
        process = Process(
            target=worker,
            name='{0}W'.format(worker.__class__.__name__),
            args=self.wargs,
            kwargs=self.wkwargs,
        )
        process.start()
        self._workers_list.append(process)
        return process        

    async def __worker_ended(self, process: Process):
        """Callback on worker exits.

        Args:
            process (Process): stopped worker process.
        """        
        if not self._stopping:
            if self._manager_type == ManagerTypes.RESTART:
                self.log.warn(u'Worker process stopped with exitcode: %s, restarting', process.exitcode)
                self.__start_worker()
            elif process.exitcode is None or process.exitcode <= 0:
                self.log.error(u'Worker died with exitcode: %s', process.exitcode)
                await mayBeFuture(self.__on_worker_died__, process)
            else:
                self.log.info(u'Worker stopped with exitcode: %s', process.exitcode)
                await mayBeFuture(self.__on_worker_ended__, process)

    @abstractmethod
    async def __start_manager__(self):
        """Custom manager start abstract method
        Must be implemented."""
        raise NotImplementedError('Manager start')

    @abstractmethod
    async def __stop_manager__(self):
        """Custom manager stop abstract method
        Must be implemented."""
        raise NotImplementedError('Manager stop')

    @abstractmethod
    def __new_worker__(self) -> Worker:
        """Factory of workers abstract method.
        Must be implemented and produce the `Worker` ancestor.
        """
        raise NotImplementedError('Must be a factory of workers')

    async def __on_worker_ended__(self, worker: Process):
        """On worker safely ended callback.

        Args:
            worker (Process): the stopped worker descriptor
        """        
        pass

    async def __on_worker_died__(self, worker: Process):
        """On woker died callback.

        Args:
            worker (Process): the died worker descriptor
        """        
        pass
