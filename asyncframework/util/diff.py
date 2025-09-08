# -*- coding:utf-8 -*-
from typing import Mapping, MutableSequence, Optional, Any, Union
#from itertools import filter
from operator import itemgetter
from collections import namedtuple, Counter
import itertools
from packets import PacketBase



class FieldDiff(namedtuple('_', ('prev', 'curr'))):
    def __repr__(self):
        return f'({self[0]} -> {self[1]})'


def squash(diff: FieldDiff | dict | Any) -> MutableSequence | dict | Any | None:
    if isinstance(diff, FieldDiff):
        if isinstance(diff.curr, MutableSequence) and isinstance(diff.prev, MutableSequence):
            if len(diff.curr) == len(diff.prev):
                return diff.curr
            try:
                c1 = Counter(diff.prev)
                c2 = Counter(diff.curr)
            except TypeError:
                return diff.curr
            else:
                return list(
                    itertools.chain.from_iterable(
                        itertools.repeat(element, c2[element] - c1[element])
                        for element in c2
                    )
                )
        else:
            return diff.curr
    elif isinstance(diff, dict):
        return dict(
            (k, v) for k, v in ((name, squash(value)) for name, value in diff.items())
            if v is not None
        ) or None
    else:
        return diff


def diff(data1: Optional[Any], data2: Optional[Any]) -> Union[dict, FieldDiff, Any, None]:
    if data1 is data2:
        return None
    elif data1 is None or data2 is None:
        return FieldDiff(data1, data2)
    elif isinstance(data1, PacketBase):
        assert isinstance(data2, PacketBase), (data2, type(data2))
        return dict(filter(
            itemgetter(1),
            (
                (fn, diff(getattr(data1, fn), getattr(data2, fn))) for fn in data1.fields_names()
            )
        ))
    elif isinstance(data1, Mapping):
        assert isinstance(data2, Mapping), (data2, type(data2))
        return dict(filter(
            itemgetter(1),
            (
                (fn, diff(data1.get(fn), data2.get(fn))) for fn in set(data1.keys()) | set(data2.keys())
            )
        ))
    elif data1 != data2:
        return FieldDiff(data1, data2)
    else:
        return None
