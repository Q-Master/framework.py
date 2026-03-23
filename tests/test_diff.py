from typing import Optional, List
import unittest
from copy import deepcopy
from packets import Packet, makeField
from packets.processors import Array
from packets.typedef.int_t import int_t
from packets.typedef.string_t import string_t
from packets.typedef.float_t import float_t 
from asyncframework.util.diff import diff


class Internal(Packet):
    d: Optional[int] = makeField(int_t)
    e: str = makeField(string_t, required=True)
    f: List[str] = makeField(Array(string_t), default=[])


class Front(Packet):
    a: int = makeField(int_t, default=10)
    b: Optional[float] = makeField(float_t)
    c: Internal = makeField(Internal, required=True)


class TestPacketDiff(unittest.TestCase):
    def test_packet_diff(self):
        pkt = Front(
            a = 10, b = 4.0,
            c = Internal(
                e = 'test',
                f = ['1', '2', '3', '4']
            )
        )
        pkt_snapshot = deepcopy(pkt)
        pkt.a = 0
        pkt.c.e = 'test2'
        pkt.c.d = 8
        pkt.c.f = ['1', '2', '6']
        if pkt.is_modified():
            pkt_diff = diff(pkt_snapshot, pkt)
            self.assertIsInstance(pkt_diff, dict)
            self.assertDictEqual(pkt_diff, {'a': 0, 'c': {'d': 8, 'e': 'test2', 'f': ['6']}}) # type: ignore
