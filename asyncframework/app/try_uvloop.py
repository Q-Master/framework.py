# coding=utf-8
import asyncio


__all__ = ('uvloop_imported', 'uvloop', 'new_event_loop')


try:
    import uvloop
    uvloop_imported = True
except ImportError:
    uvloop_imported = False

def new_event_loop() -> asyncio.AbstractEventLoop:
    ioloop: asyncio.AbstractEventLoop
    if uvloop_imported:
        ioloop = uvloop.new_event_loop()
    else:
        ioloop = asyncio.new_event_loop()
    asyncio.set_event_loop(ioloop)
    return ioloop
