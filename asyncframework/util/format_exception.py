# -*- coding:utf-8 -*-
import traceback


def format_exception(exc: Exception, delimiter='#012'):
    exc_strs = traceback.format_exception(exc)
    return delimiter.join(exc_strs)
