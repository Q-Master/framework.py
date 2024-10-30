# -*- coding:utf-8 -*-
from typing import Tuple, Any, Mapping, Sequence
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
            record.tags = str(record.tags)
        return super().format(record)


class TagDict(dict):
    def __setitem__(self, __key: Any, __value: Any) -> None:
        __key = f'"{__key}"'
        __value = _to_tag_value(__value)
        return super().__setitem__(__key, __value)
    
    def __str__(self) -> str:
        return f'{{{",".join((":".join(map(str, i)) for i in self.items()))}}}'


def _to_tag_value(__value: Any) -> str:
    if isinstance(__value, str):
        __value = f'"{__value}"'
    elif isinstance(__value, Mapping):
        __value = str(_to_tag_dict(__value))
    elif isinstance(__value, Sequence):
        __value = f'[{",".join([_to_tag_value(v) for v in __value])}]'
    else:
        __value = str(__value)
    return __value


def _to_tag_dict(__value: Mapping) -> 'TagDict':
    nv: TagDict = TagDict()
    for k, v in __value.items():
        nv[k] = v
    return nv


class LoggerTaggingAdapter(logging.LoggerAdapter):

    def __init__(self, logger, extra = None) -> None:
        if isinstance(logger, LoggerTaggingAdapter):
            logger, self.tags = logger.logger, logger.tags.copy()
        else:
            self.tags = TagDict()
        super().__init__(logger, extra if extra is not None else {})
        self.extra['tags'] = self.tags
        
    def process(self, msg, kwargs) -> Tuple[str, dict]:
        extra: dict = kwargs.setdefault('extra', self.extra)
        if extra is not self.extra:
            tags: dict = extra.setdefault('tags', self.tags)
            if tags is not self.tags:
                extra['tags'] = dict(chain(tags.items(), self.tags.items()))
        return msg, kwargs
