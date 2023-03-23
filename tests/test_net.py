# -*- coding:utf-8 -*-
import unittest
import asyncio
from asyncframework.net import SocketConnection
from asyncframework.net import SocketServer


class NetTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_net(self):
        srv = None
        test_complete = asyncio.Future()
        def _on_conn(transport: asyncio.BaseTransport):
            ci = transport.get_extra_info('peername')
            self.assertEqual(transport.get_extra_info('peername')[0], '127.0.0.1')

        def _on_cl(exc: Exception):
            pass

        async def _on_msg(src, msg: str):
            self.assertEqual(msg, 'test')
            await src.write('test')

        async def _on_client_msg(src, msg: str):
            self.assertEqual(msg, 'test')
            test_complete.set_result(True)

        def fabric():
            sc = SocketConnection()
            sc.add_callbacks(
                on_connection_made=_on_conn,
                on_connection_lost=_on_cl,
                on_message_received=_on_msg
            )
            return sc
        
        src = SocketConnection()
        src.add_callbacks(on_message_received=_on_client_msg)
        srv = SocketServer(fabric, host='127.0.0.1', port=56789)
        await srv.start()
        serv_future = srv.run()
        await asyncio.sleep(.2)
        await src.connect_to('127.0.0.1', 56789)
        await src.write('test')
        await test_complete
        await srv.stop()
        await serv_future


