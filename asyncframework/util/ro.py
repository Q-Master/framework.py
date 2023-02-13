# -*- coding:utf-8 -*-
from typing import Hashable
from datetime import time, datetime, timedelta
from types import MethodType, BuiltinMethodType, FunctionType


class ReadOnly():
    __wrapped = None

    @classmethod
    def make_ro(cls, obj):
        if not isinstance(obj, (type(None), int, float, complex, bool, str, tuple, time, timedelta, datetime)):
            return cls(obj)
        return obj

    @staticmethod
    def __readonly(*args, **kwargs):
        raise RuntimeError('This is the read only object')

    def __init__(self, wrapped):
        super().__setattr__('__wrapped', wrapped)

    def __getattr__(self, attr: str):
        wrapped = super().__getattribute__('__wrapped')
        value = getattr(wrapped, attr)
        if isinstance(value, (MethodType, BuiltinMethodType, FunctionType)):
            if attr == 'get' and isinstance(wrapped, dict):
                return self.__get
            elif attr in ('add', 'remove', 'pop', 'setdefault', 'append', 'extend', 'insert', 'sort', 'reverse', 'clear'):
                return self.__readonly
            else:
                return value
        else:
            return ReadOnly.make_ro(value)

    def __getitem__(self, item):
        wrapped = super().__getattribute__('__wrapped')
        if isinstance(item, slice):
            return ReadOnly.make_ro([ReadOnly.make_ro(element) for element in wrapped[item]])
        else:
            return ReadOnly.make_ro(wrapped[item])

    def __get(self, item, default=None):
        wrapped = super().__getattribute__('__wrapped')
        result = wrapped.get(item, default)
        return ReadOnly.make_ro(result)

    def __repr__(self):
        wrapped = super().__getattribute__('__wrapped')
        return repr(wrapped)

    def __str__(self):
        wrapped = super().__getattribute__('__wrapped')
        return str(wrapped)

    def __iter__(self):
        wrapped = super().__getattribute__('__wrapped')
        return iter(wrapped)

    def __len__(self):
        wrapped = super().__getattribute__('__wrapped')
        try:
            return len(wrapped)
        except TypeError:
            return bool(wrapped)

    def __eq__(self, other):
        return super().__getattribute__('__wrapped') == other

    def __hash__(self):
        wrapped = super().__getattribute__('__wrapped')
        try:
            return hash(wrapped)
        except:
            return hash(str(wrapped))

    @property
    def __class__(self):
        return super().__getattribute__('__wrapped').__class__

    @__class__.setter
    def __class__(self):
        ReadOnly.__readonly()

    __setattr__ = __readonly
    __setitem__ = __readonly
    __delattr__ = __readonly
    __delitem__ = __readonly

