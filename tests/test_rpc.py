# -*- coding:utf-8 -*-
import unittest
import asyncio
from asyncframework.net import SocketConnection
from asyncframework.net import SocketServer
from asyncframework.rpc import RPC, rpc_method
from asyncframework.rpc.packets import RPCPackets, rpc_packet
from packets import Packet, makeField
from packets.processors import int_t, string_t, int32_t


@rpc_method()
def test(app, msg):
    app.assertEqual(msg, 'complete')
    app.test_complete.set_result(True)
    return 'ok'


class RPCPacketTestRequest(Packet):
    packet_id: int = makeField(int32_t, '_', default=1, override=True)
    query: str = makeField(string_t, required=True)


class RPCPacketTestReply(Packet):
    packet_id: int = makeField(int32_t, '_', default=2, override=True)
    reply: int = makeField(int_t, required=True)


@rpc_packet(RPCPacketTestRequest)
def packet_test(app, msg, *args, **kwargs):
    app.assertEqual(msg.query, 'test')
    app.test_complete.set_result(True)
    return RPCPacketTestReply(reply=1)


class RPCTestCase(unittest.IsolatedAsyncioTestCase):
    test_complete: asyncio.Future = asyncio.Future()

    async def test_rpc(self):
        self.test_complete = asyncio.Future()
        def fabric():
            sc = SocketConnection()
            RPC(self, sc)
            return sc
        srv = SocketServer(fabric, host='127.0.0.1', port=56789)
        await srv.start()
        serv_future = srv.run()
        await asyncio.sleep(.2)
        src = SocketConnection()
        src_rpc = RPC(self, src)
        await src.connect_to('127.0.0.1', 56789)
        res = await src_rpc.call('test', 'complete')
        self.assertEqual(res, 'ok')
        await self.test_complete
        await srv.stop()
        await serv_future

    async def test_packet_rpc(self):
        self.test_complete = asyncio.Future()
        def fabric_packet():
            sc = SocketConnection()
            RPCPackets(self, sc, response_models=[RPCPacketTestReply, RPCPacketTestRequest])
            return sc
        srv = SocketServer(fabric_packet, host='127.0.0.1', port=56789)
        await srv.start()
        serv_future = srv.run()
        await asyncio.sleep(.2)
        src = SocketConnection()
        src_rpc = RPCPackets(self, src, response_models=[RPCPacketTestReply, RPCPacketTestRequest])
        await src.connect_to('127.0.0.1', 56789)
        res = await src_rpc.call(RPCPacketTestRequest(query='test'))
        self.assertEqual(res.reply, 1)
        await self.test_complete
        await srv.stop()
        await serv_future
