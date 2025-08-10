# -*- coding: utf-8 -*-
import asyncio
from .try_uvloop import *
from .proctitle import set_process_name
from ..log.log import get_logger


__all__ = ['main']


log = get_logger('main')

def start(ioloop, app):
    return app(ioloop)

def main(appCls, *args, **kwargs):
    set_process_name(appCls.__name__)
    app = appCls(*args, **kwargs)
    if uvloop_imported:
        ioloop = uvloop.new_event_loop()
    else:
        ioloop = asyncio.new_event_loop()
    asyncio.set_event_loop(ioloop)
    ioloop.run_until_complete(start(ioloop, app))
    ioloop.close()
