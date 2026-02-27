from typing import Optional, List
import unittest
from copy import deepcopy
from asyncframework.log import LoggerTaggingAdapter, get_logger, LogFormatter, init_logging

class TestLogging(unittest.TestCase):
    def test_logging(self):
        init_logging(
            stdout=True,
            log_name='TestLogging',
            log_level='INFO',
            formatter=LogFormatter('%(asctime)s.%(msecs)03d %(name)s <%(levelname).1s> %(module)s:%(lineno)d] %(tags)s %(message)s', '%Y-%m-%d %H:%M:%S')
        )
        log = get_logger('TestLogger')
        log.info('Simple log')
        log_adapted = LoggerTaggingAdapter(log)
        log_adapted.tags['SomeNumber'] = 1234
        log_adapted.info('Tagged log')
        log_adapted_adapted = LoggerTaggingAdapter(log_adapted)
        log_adapted_adapted.tags['SomeString'] = 'text'
        log_adapted_adapted.info('Tagged tagged log')
        log_adapted.info('Should be no SomeString')
