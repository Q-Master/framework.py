# -*- coding:utf-8 -*-
from typing import Sequence, List, Any
from random import *
from operator import add
from functools import reduce
from bisect import bisect_left


_sys_random = SystemRandom()
random = _sys_random.random
shuffle = _sys_random.shuffle
choice = _sys_random.choice
getrandbits = _sys_random.getrandbits
sample = _sys_random.sample
randint = _sys_random.randint


def rand32() -> int:
    """Get random number as int32 signed
    """
    return _sys_random.getrandbits(32) - 2147483648


def roll(chance: float) -> bool:
    """Rolls the dice with the chance and return True or False

    Args:
        chance (float): the chance (0..1)

    Returns:
        bool: True if got a chance, else False
    """
    return _sys_random.random() < chance


def get_distribution(probabilities: Sequence[float]) -> List[float]:
    """Returns a distribution table using the probabilities table
    e.x. probabilities [0.1, 0.2, 0.3, 0.4] will generate distribution [0.1, 0.3, 0.6, 1.0]

    Args:
        probabilities (List[float]): probabilities list

    Returns:
        List[float]: distribution list
    """
    if abs(sum(probabilities) - 1) > 1e-6:
        raise ValueError(f'Summ of probabilities can\'t be higher than 1.0, but {sum(probabilities)} given')
    return [reduce(add, probabilities[:i + 1]) for i in range(len(probabilities))]


def roll_event_distribution(events: Sequence[Any], distribution: Sequence[float]) -> Any:
    """Rolls a single event from events list using the distribution table

    Args:
        events (List[Any]): list of the events to select from
        distribution (List[float]): distribution table see `get_distribution`

    Returns:
        Any: a single random element from events list
    """    
    return events[bisect_left(distribution, _sys_random.random())]


def roll_event_probabilities(events: Sequence[Any], probabilities: List[float]) -> Any:
    """Rolls a single event from events list using the probabilities table

    Args:
        events (List[Any]): list of the events to select from
        probabilities (List[float]): probabilities table

    Returns:
        Any: a single random element from events list
    """    
    distribution = get_distribution(probabilities)
    return roll_event_distribution(events, distribution)
