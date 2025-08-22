# -*- coding:utf-8 -*-
import unittest
from typing import Optional
from packets import Packet, Field, makeField
from packets.processors import string_t, int_t, bool_t
from asyncframework.app.config import Config, ConfigTableProtocolBase, ConfigProtocolBase



class Record(Packet):
    name: str = makeField(string_t, required=True)
    number: int = makeField(int_t, required=True)
    active: bool = makeField(bool_t, default=True)
    

class RecordsConfig(ConfigTableProtocolBase[Record]):
    __filename__ = 'records.json'
    __default_field__ = makeField(Record)


class SimpleConfig(ConfigProtocolBase):
    __filename__ = 'simple.json'
    record: Record = makeField(Record, required=True)
    test: Optional[bool] = makeField(bool_t)


class TConfig(Config):
    records = RecordsConfig()


class TestConfig(unittest.TestCase):
    def test_config(self):
        c1: TConfig = TConfig.load_cfg('dummy.json')
        c3: SimpleConfig = SimpleConfig.load_cfg()
        self.assertEqual(len(c1.records), 3)
        self.assertIsNotNone(c1.records)
        assert c1.records is not None
        self.assertEqual(c1.records.record1.name, 'test')
        self.assertEqual(c1.records.record1.number, 1)
        self.assertEqual(c1.records.record2.name, 'test2')
        self.assertEqual(c1.records.record2.number, 2)
        self.assertEqual(c1.records.record3.name, 'test3')
        self.assertEqual(c1.records.record3.number, 3)
        self.assertEqual(c3.test, None)
