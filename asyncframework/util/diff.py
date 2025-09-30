# -*- coding:utf-8 -*-
from typing import Mapping, Optional, Any, Union, Iterator, TypeVar, Dict, Tuple, MutableSequence, TypeAlias
import itertools
from _collections_abc import dict_keys, dict_items
from collections import Counter
from packets import PacketBase


_DT = TypeVar('_DT')


def diff(data1: Optional[_DT], data2: Optional[_DT]) -> Union[Dict[Any, Any], _DT, None]:
    """Generate a difference between two items

    Args:
        data1 (Optional[Any]): item 1
        data2 (Optional[Any]): item 2

    Returns:
        Union[dict, FieldDiff, Any, None]: the difference between two items in fmt key:[prev, curr] or just [prev, curr]
    """
    class FieldDiff():
        curr: Optional[_DT] = None
        def __init__(self, curr: Optional[_DT]) -> None:
            self.curr = curr

    def iterate_fields(data1: Optional[_DT], data2: Optional[_DT], it: Union[Iterator, dict_keys]):
        assert isinstance(data1, (PacketBase, Dict))
        assert isinstance(data2, (PacketBase, Dict))
        result = {}
        for fn in it:
            d = _real_diff(data1.get(fn), data2.get(fn))
            if d is None:
                continue
            else:
                result[fn] = d.curr
        return result

    def _real_diff(data1: Optional[_DT], data2: Optional[_DT]) -> Optional[FieldDiff]:
        if data1 is data2:
            return None
        elif data1 is None or data2 is None:
            return FieldDiff(data2)
        elif isinstance(data1, PacketBase):
            d = iterate_fields(data1, data2, data1.fields_names())
            return FieldDiff(d) if d else None
        elif isinstance(data1, Mapping):
            assert isinstance(data2, Mapping), (data2, type(data2))
            d = iterate_fields(data1, data2, iter(set(data1.keys()) | set(data2.keys())))
            return FieldDiff(d) if d else None
        elif isinstance(data1, (MutableSequence)) and isinstance(data2, (MutableSequence)):
            dlist: MutableSequence = []
            for a, b in itertools.zip_longest(data1, data2):
                d = _real_diff(a, b)
                if d is None or d.curr is None:
                    continue
                else:
                    dlist.append(d.curr)
            return FieldDiff(dlist) if dlist else None # type: ignore 
        elif data1 != data2:
            return FieldDiff(data2)
        else:
            return None
    d = _real_diff(data1, data2)
    return d.curr if d is not None else d


DiffKeys: TypeAlias = Dict[str, Union[str, 'DiffKeys']]

def diff_keys(data1: Union[PacketBase, dict], data2: Union[PacketBase, dict]) -> DiffKeys:
    """Generate a difference between two items (only dict and Packet supported)

    Args:
        data1 (Union[PacketBase, dict]): item 1
        data2 (Union[PacketBase, dict]): item 2

    Raises:
        ValueError: in case of unsupported items

    Returns:
        List[str]: list of fields, touched by changes in format a.b.c
    """
    keys_diff = {}
    def iterate_fields(it: Union[Iterator[Tuple[str, Any]], dict_items]):
        for fn, fv1 in it:
            fv2 = data2.get(fn)
            if fv1 is None and fv2 is None:
                continue
            elif fv1 is None or fv2 is None:
                keys_diff[fn] = '1'
            elif isinstance(fv1, (PacketBase, dict)):
                sub_dict = diff_keys(fv1, fv2)
                keys_diff[fn] = sub_dict
            elif fv1 != fv2:
                keys_diff[fn] = '1'
    if isinstance(data1, PacketBase):
        assert isinstance(data2, PacketBase), (data2, type(data2))

    if data1 is data2:
        return keys_diff
    elif data1 is None and data2 is not None:
        for fn in data2.fields_names():
            keys_diff[fn] = '1'
    elif data1 is not None and data2 is None:
        return keys_diff
    elif isinstance(data1, PacketBase):
        assert isinstance(data2, PacketBase), (data2, type(data2))
        iterate_fields(data1.packet_fields())
    elif isinstance(data1, dict):
        assert isinstance(data2, dict), (data2, type(data2))
        iterate_fields(data1.items())
    else:
        raise ValueError(f'Cant diff {type(data1)} vs {type(data2)}')
    return keys_diff
