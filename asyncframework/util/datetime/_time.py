# -*- coding:utf-8 -*-
from typing import Optional
from time import *


SECONDS_IN_DAY = 86400
SECONDS_IN_HOUR = 3600
SECONDS_IN_MINUTE = 60


def unixtime() -> int:
    """Current time as unixtime

    Returns:
        int: unixtime of current time
    """
    return int(time())


def days_to_secs(days: int) -> int:
    """Convert days to seconds

    Args:
        days (int): days amount

    Returns:
        int: seconds amount
    """
    return days * SECONDS_IN_DAY


def hours_to_secs(hours: int) -> int:
    """Convert hours to seconds

    Args:
        hours (int): hours amount

    Returns:
        int: seconds amount
    """
    return hours * SECONDS_IN_HOUR


def minutes_to_secs(minutes: int) -> int:
    """Convert minutes to seconds

    Args:
        minutes (int): minutes amount

    Returns:
        int: seconds amount
    """
    return minutes * SECONDS_IN_MINUTE


def time_ms(seconds: Optional[float] = None):
    if not seconds:
        seconds = time()
    return int(seconds * 1000)
