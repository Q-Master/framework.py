# -*- coding: utf-8 -*-
from typing import Dict, Union, Callable, Any, Optional
from uuid import UUID, uuid4
from asyncio import Future, ensure_future, sleep
from functools import partial
from packets import unixtime
from ..app import Service
from ..log import get_logger
from ..util.datetime import time
from .is_async import is_async


__all__ = ['TimersService', 'Timer']


class Timer:
    __slots__ = ['when', 'callback', 'args', 'kwargs', 'id']
    def __init__(self, when: Union[unixtime, int], callback: Callable, *cargs, id: Any = None, **ckwargs) -> None:
        self.when = when
        self.callback = callback
        self.args = cargs
        self.kwargs = ckwargs
        if not id:
            self.id = uuid4()

    def __hash__(self) -> int:
        if isinstance(id, UUID):
            return id.__hash__()
        else:
            return hash(id)

    async def __call__(self) -> Any:
        if is_async(self.callback):
            await self.callback(*self.args, **self.kwargs)
        else:
            self.callback(*self.args, **self.kwargs)


class TimersService(Service):
    log = get_logger('TimersService')
    __timers: Dict[Timer, Future]
    
    def __init__(self) -> None:
        super().__init__()
    
    async def __start__(self, *args, **kwargs):
        self.log.debug('Starting timers service')
        self.__timers = {}
    
    async def __stop__(self):
        self.log.debug('Stopping timers service')
        for timer, future in self.__timers.items():
            if not future.done():
                self.log.info(f'Cancelling timer {timer.id}')
                future.cancel()
    
    def add(self, timer: Timer) -> Future:
        if not self.ioloop:
            raise RuntimeError('ioloop must be initialized')
        fut = ensure_future(self._execute(timer))
        _remove_timer = partial(self.remove_timer, timer)
        fut.add_done_callback(_remove_timer)
        self.__timers[timer] = fut
        return fut
    
    def remove_timer(self, timer: Timer, _ = None):
        fut = self.__timers.pop(timer, None)
        if fut and not fut.done():
            self.log.info(f'Cancelling timer {timer.id}')
            fut.cancel()
    
    def replace_timer(self, old_timer: Timer, new_timer: Timer):
        self.remove_timer(old_timer)
        self.add(new_timer)

    async def _execute(self, timer: Timer):
        delay = timer.when - time.time()
        if delay <= 0:
            await timer()
        else:
            await sleep(delay)
            await timer()
