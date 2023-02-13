# -*- coding:utf-8 -*-
import logging


__all__ = ['LogFormatter']


class LogFormatter(logging.Formatter):
    __DEFAULT_FMT = '%(asctime)s.%(msecs)03d %(process)5s %(levelname).1s %(module)s:%(lineno)d] %(name)s %(tags)s %(message)s'
    __DEFAULT_DATE_FMT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, fmt=__DEFAULT_FMT, datefmt=__DEFAULT_DATE_FMT):
        super().__init__(fmt, datefmt)

    def format(self, record):
        if 'tags' not in record.__dict__:
            record.tags = '{}'
        else:
            record.tags = '{' + ','.join(('='.join(map(str, i)) for i in record.tags.items())) + '}'
        return super().format(record)
