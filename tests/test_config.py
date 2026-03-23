# -*- coding:utf-8 -*-
import unittest
from typing import Optional
from packets import Packet, makeField
from packets.typedef.string_t import string_t
from packets.typedef.int_t import int_t
from packets.typedef.bool_t import bool_t
from asyncframework.app.config import Config, TableConfigReader, ConfigReader, configReader



class Record(Packet):
    name: str = makeField(string_t, required=True)
    number: int = makeField(int_t, required=True)
    active: bool = makeField(bool_t, default=True)
    

class RecordsConfig(TableConfigReader[Record]):
    __filename__ = 'tests/records.json'
    __default_field__ = makeField(Record, required=True)


class RecordsConfigWithField(TableConfigReader[Record]):
    __filename__ = 'tests/records_with_field.json'
    __default_field__ = makeField(Record, required=True)
    additional: bool = makeField(bool_t, required=True)


class SimpleConfig(ConfigReader):
    __filename__ = 'tests/simple.json'
    record: Record = makeField(Record, required=True)
    test: Optional[bool] = makeField(bool_t)


class TConfig(Config):
    records = configReader(RecordsConfig)


class TConfig1(Config):
    records = configReader(RecordsConfigWithField)


class TestConfig(unittest.TestCase):
    def test_config(self):
        c3: SimpleConfig = SimpleConfig.load_cfg()
        self.assertEqual(c3.test, None)
    
    def _test_config_table(self):
        c1: TConfig = TConfig.load_cfg('tests/dummy.json')
        self.assertEqual(len(c1.records), 3)
        self.assertIsNotNone(c1.records)
        assert c1.records is not None
        self.assertEqual(c1.records.record1.name, 'test')
        self.assertEqual(c1.records.record1.number, 1)
        self.assertEqual(c1.records.record2.name, 'test2')
        self.assertEqual(c1.records.record2.number, 2)
        self.assertEqual(c1.records.record3.name, 'test3')
        self.assertEqual(c1.records.record3.number, 3)

    def test_config_table_with_field(self):
        c2: TConfig1 = TConfig1.load_cfg('tests/dummy.json')
        self.assertEqual(c2.records.recordwf1.name, 'record')
        self.assertEqual(c2.records.recordwf1.number, 123)
        self.assertEqual(c2.records.recordwf2.name, 'record2')
        self.assertEqual(c2.records.recordwf2.number, 256)
        self.assertEqual(c2.records.additional, True)

