# -*- coding:utf-8 -*-
import traceback


def format_exception(exc: Exception, delimiter='#012') -> str:
    exc_strs = [estr.replace('\n', delimiter) for estr in traceback.format_exception(exc)]
    return ''.join(exc_strs)

def unpack_exception_str(exc: str, delimiter='#012') -> str:
    return exc.replace(delimiter, '\n')
