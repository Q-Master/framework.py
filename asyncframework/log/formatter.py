# -*- coding:utf-8 -*-
from typing import Tuple
from itertools import chain
import logging


__all__ = ['LogFormatter', 'LoggerTaggingAdapter']


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


class LoggerTaggingAdapter(logging.LoggerAdapter):
    tags: dict = {}
    extra: dict = {}

    def __init__(self, logger, extra = None) -> None:
        if isinstance(logger, LoggerTaggingAdapter):
            logger, self.tags = logger.logger, logger.tags.copy()
        else:
            pass
        super().__init__(logger, extra if extra is not None else {})
        self.extra['tags'] = self.tags
        
    def process(self, msg, kwargs) -> Tuple[str, dict]:
        extra: dict = kwargs.setdefault('extra', self.extra)
        if extra is not self.extra:
            tags: dict = extra.setdefault('tags', self.tags)
            if tags is not self.tags:
                extra['tags'] = dict(chain(tags.items(), self.tags.items()))
        return msg, kwargs
