# -*- coding: utf-8 -*-
import signal
import asyncio
import logging
from .pidfile import PidFile
from .service import Service
from ..log import log


__all__ = ['App']


class App(Service):
    pidfile = None
    log: logging.Logger = log.get_logger()

    def __init__(self, pidfile: str):
        super().__init__()
        self.pidfile = pidfile

    async def __start__(self, *args, **kwargs):
        for signame in ('SIGINT', 'SIGTERM'):
            self.ioloop.add_signal_handler(getattr(signal, signame), self._fire_stop_waiter)
        result = await super().__start__(*args, **kwargs)
        return result

    async def __call__(self, ioloop: asyncio.events.AbstractEventLoop, *args, **kwargs):
        self.log.info(u'Starting Application')
        await self.start(ioloop, *args, **kwargs)
        if self.pidfile:
            with PidFile(self.pidfile):
                await self.run(*args, **kwargs)
        else:
            await self.run(*args, **kwargs)
        await self.stop()
        self.log.info(u'Application stopped')
