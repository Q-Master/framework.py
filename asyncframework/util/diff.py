# -*- coding:utf-8 -*-
from typing import Mapping, Optional, Any, Union, Iterator, TypeVar, Dict, List, Tuple, MutableSequence, Sequence
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
        curr: Optional[_DT]
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
            return FieldDiff(iterate_fields(data1, data2, data1.fields_names()))
        elif isinstance(data1, Mapping):
            assert isinstance(data2, Mapping), (data2, type(data2))
            return FieldDiff(iterate_fields(data1, data2, iter(set(data1.keys()) | set(data2.keys()))))
        elif isinstance(data1, (MutableSequence)) and isinstance(data2, (MutableSequence)):
            if len(data1) == len(data2):
                return FieldDiff(data2)
            try:
                c1 = Counter(data1)
                c2 = Counter(data2)
            except TypeError:
                return FieldDiff(data2)
            else:
                return FieldDiff(list(
                    itertools.chain.from_iterable(
                        itertools.repeat(element, c2[element] - c1[element])
                        for element in c2.keys()
                    )
                )) # type: ignore
        elif data1 != data2:
            return FieldDiff(data2)
        else:
            return None
    d = _real_diff(data1, data2)
    return d.curr if d is not None else d


def diff_keys(data1: Union[PacketBase, dict], data2: Union[PacketBase, dict]) -> List[str]:
    """Generate a difference between two items (only dict and Packet supported)

    Args:
        data1 (Union[PacketBase, dict]): item 1
        data2 (Union[PacketBase, dict]): item 2

    Raises:
        ValueError: in case of unsupported items

    Returns:
        List[str]: list of fields, touched by changes in format a.b.c
    """
    keys_diff = []
    def iterate_fields(it: Union[Iterator[Tuple[str, Any]], dict_items]):
        for fn, fv1 in it:
            fv2 = data2.get(fn)
            if fv1 is None and fv2 is None:
                continue
            elif fv1 is None or fv2 is None:
                keys_diff.append(fn)
            elif isinstance(fv1, (PacketBase, dict)):
                sub_list = diff_keys(fv1, fv2)
                keys_diff.extend([f'{fn}.{sfn}' for sfn in sub_list])
            elif fv1 != fv2:
                keys_diff.append(fn)
    if isinstance(data1, PacketBase):
        assert isinstance(data2, PacketBase), (data2, type(data2))

    if data1 is data2:
        return keys_diff
    elif data1 is None or data2 is None:
        return FieldDiff(data1, data2)
    elif isinstance(data1, PacketBase):
        assert isinstance(data2, PacketBase), (data2, type(data2))
        iterate_fields(data1.packet_fields())
    elif isinstance(data1, dict):
        assert isinstance(data2, dict), (data2, type(data2))
        iterate_fields(data1.items())
    else:
        raise ValueError(f'Cant diff {type(data1)} vs {type(data2)}')
    return keys_diff
