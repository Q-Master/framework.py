# -*- coding: utf-8 -*-
from typing import TypeVar, Generator, List

_T = TypeVar("_T")
def chunks(l: int, n: List[_T]) -> Generator[List[_T], None, None]:
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]
