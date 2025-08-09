# -*- coding:utf-8 -*-
from typing import Dict, TypeVar


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class DictWithDefault(Dict[_KT, _VT]):
    default: _VT | None = None

    def __missing__(self, _) -> _VT | None:
        return self.default
