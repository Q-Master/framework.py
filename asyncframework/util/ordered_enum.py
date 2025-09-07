# -*- coding:utf-8 -*-
from enum import Enum


class OrderedEnum(Enum):
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        raise NotImplementedError(f'Different type of enums: {self.__class__.__name__} != {other.__class__.__name__}')

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        raise NotImplementedError(f'Different type of enums: {self.__class__.__name__} != {other.__class__.__name__}')

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        raise NotImplementedError(f'Different type of enums: {self.__class__.__name__} != {other.__class__.__name__}')

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        raise NotImplementedError(f'Different type of enums: {self.__class__.__name__} != {other.__class__.__name__}')
