# -*- coding:utf-8 -*-
from typing import Mapping, AbstractSet


__all__ = ['merge_dicts']


def merge_dicts(origin: dict, patch: dict):
    if origin is patch:
        return origin
    if origin is None:
        return patch
    if patch is None:
        return origin

    if not isinstance(patch, Mapping):
        raise TypeError('Not supported type %s' % type(patch))

    a = set(origin.keys())
    b = set(patch.keys())

    new_keys = b - a
    for key in new_keys:
        origin[key] = patch[key]

    old_keys = a & b
    for key in old_keys:
        if not isinstance(origin[key], type(patch[key])):
            raise TypeError('Types are not equal for key %s: origin is %s, patch is %s' % (key, type(origin[key]), type(patch[key])))
        if isinstance(patch[key], Mapping):
            merge_dicts(origin[key], patch[key])
        if isinstance(patch[key], AbstractSet):
            origin[key].update(patch[key])
        else:
            origin[key] = patch[key]
