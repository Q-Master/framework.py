# -*- coding: utf-8 -*-
import asyncio
import logging
from .service import Service
from .pidfile import PidFile
from ..log import log


__all__ = ['Script']


class Script(Service):
    pidfile = None
    log: logging.Logger = log.get_logger()

    def __init__(self, pidfile: str):
        super().__init__(linear = True)
        self.pidfile = pidfile

    async def __call__(self, ioloop: asyncio.events.AbstractEventLoop, *args, **kwargs):
        self.log.info(u'Start script')
        await self.start(ioloop, *args, **kwargs)
        if self.pidfile:
            with PidFile(self.pidfile):
                await self.run(*args, **kwargs)
        else:
            await self.run(*args, **kwargs)
        self.log.info(u'Script stopped')
