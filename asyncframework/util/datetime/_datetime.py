# -*- coding:utf-8 -*-
from typing import Optional, Union
from copy import copy
from datetime import *
from time import mktime


def parse(s: str) -> datetime:
    """Parse string for date and time with default pattern

    Args:
        s (str): date and time string

    Returns:
        datetime: parsed datetime
    """
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


def parse_date(s: str) -> datetime:
    """Parse string for date only with default pattern

    Args:
        s (str): date string

    Returns:
        datetime: parsed datetime
    """
    return datetime.strptime(s, '%Y-%m-%d')


def parse_time(s: str) -> datetime:
    """Parse string for time only with default pattern

    Args:
        s (str): time string

    Returns:
        datetime: parsed datetime
    """
    return datetime.strptime(s, '%H:%M:%S')


def to_text(dt: datetime) -> str:
    """Convert date and time to text with default pattern

    Args:
        dt (datetime): datetime to convert

    Returns:
        str: converted string
    """
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def to_date_text(dt: datetime) -> str:
    """Convert only date to text with default pattern

    Args:
        dt (datetime): date to convert

    Returns:
        str: converted string
    """
    return dt.strftime('%Y-%m-%d')


def to_time_text(dt: Union[datetime, time]):
    """Convert only time to text with default pattern

    Args:
        dt (Union[datetime, time]): time to convert

    Returns:
        str: converted string
    """
    return dt.strftime('%H:%M:%S')


def to_unixtime(dt: datetime) -> int:
    """Return unixtime from datetime

    Args:
        dt (datetime): datetime to convert

    Returns:
        int: unixtime
    """
    return int(mktime(dt.timetuple()))


def str_to_unixtime(time_str: str) -> int:
    """Convert string with default pattern to unixtime

    Args:
        time_str (str): string time

    Returns:
        int: unixtime
    """
    dt = parse(time_str)
    return to_unixtime(dt)


def unixtime_to_str(ts: int) -> str:
    """Convert unixtime to text string

    Args:
        ts (int): unix time

    Returns:
        str: converted string
    """
    dt = datetime.fromtimestamp(ts)
    return to_text(dt)


def midnight(dtnow: Optional[Union[datetime, int, float]] = None, offset: int = 0) -> datetime:
    """Get midnight for current date or given date

    Args:
        dtnow (Optional[Union[datetime, int, float]], optional): datetime or timestamp for calculate midnight. Defaults to today.
        offset (int, optional): the amount of days to add to the dtnow. Might be negative Defaults to 0.

    Returns:
        datetime: the datetime for midnight
    """
    if dtnow is None:
        dtnow = datetime.today()
    elif isinstance(dtnow, (int, float)):
        dtnow = datetime.fromtimestamp(dtnow)
    else:
        dtnow = copy(dtnow)
    return (dtnow + timedelta(days=offset)).replace(hour=0, minute=0, second=0, microsecond=0)


def day_end(dtnow: Optional[Union[datetime, int, float]] = None, offset: int = 0) -> datetime:
    """Get day end for current date or given date

    Args:
        dtnow (Optional[Union[datetime, int, float]], optional): datetime or timestamp for calculate day end. Defaults to today.
        offset (int, optional): the amount of days to add to the dtnow. Might be negative Defaults to 0.

    Returns:
        datetime: the datetime for day end
    """
    if dtnow is None:
        dtnow = datetime.today()
    elif isinstance(dtnow, (int, float)):
        dtnow = datetime.fromtimestamp(dtnow)
    else:
        dtnow = copy(dtnow)
    return (dtnow + timedelta(days=offset)).replace(hour=23, minute=59, second=59, microsecond=0)

def week_start(dtnow: Optional[datetime] = None) -> datetime:
    """Calculate start of the week

    Args:
        dtnow (Optional[datetime], optional): the date for which week to calculate week start. Defaults to today.

    Returns:
        datetime: the start of the week for the date
    """
    dt: datetime = midnight(dtnow)
    return (dt - timedelta(days=dt.weekday()))


def week_end(dtnow: Optional[datetime] = None) -> datetime:
    """Calculate the end of the week for the date

    Args:
        dtnow (Optional[datetime], optional): the date for which week to calculate week end. Defaults to today.

    Returns:
        datetime: the end of the week for the date
    """
    return (week_start(dtnow) + timedelta(days=7) - timedelta(seconds=1))


def end_of_month(dtnow: Optional[datetime] = None) -> datetime:
    """Calculate end of the month for the date

    Args:
        dtnow (Optional[datetime], optional): the date for which month to calculate end of month date. Defaults to today.

    Returns:
        datetime: the end of the month for the date
    """
    dt: datetime = midnight(dtnow)
    if dt.month == 12:
        return dt.replace(day=31)
    return (dt.replace(month=dt.month + 1, day=1) - timedelta(seconds=1))
