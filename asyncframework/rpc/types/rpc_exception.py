# -*- coding:utf-8 -*-
from typing import Optional
from packets import FieldProcessor
from packets import json


__all__ = [
    'NotToHandle', 
    'RPCException', 
    'WrongConsumer', 
    'RPCSenderStopped', 
    'RPCDispatcherStopped', 
    'RPCDeliveryFailed', 
    'RPCExceptionProcessor', 
    'rpc_exception_t'
]


class NotToHandle(Exception):
    """The message should not be handled
    """
    pass


class RPCException(Exception):
    __slots__ = (
        'message',
        'traceback',
        'type'
    )
    def __init__(self, message: str, type: Optional[str] = None, traceback: Optional[str] = None):
        super().__init__()
        self.message = message
        self.traceback = traceback
        self.type = type or self.__class__.__name__

    def __str__(self):
        return f'<RPCException message: {self.message}, traceback: {self.traceback}>'

    def __repr__(self):
        return f'RPCException(\'{self.message}\',\'{self.traceback}\')'


class WrongConsumer(RPCException):
    """Unknown message for this dispatcher
    """
    pass


class RPCSenderStopped(RPCException):
    """Exception on trying to send message if stopping
    """
    pass


class RPCDispatcherStopped(RPCException):
    """Exception on trying to dispatch message if stopping
    """
    pass


class RPCDeliveryFailed(RPCException):
    """Exception caused by delivery error
    """
    pass


_EXCEPTIONS_MAP = {
    RPCException: 0,
    RPCSenderStopped: 1,
    RPCDispatcherStopped: 2
}
_REVERSED_MAP = {
    0: RPCException,
    1: RPCSenderStopped,
    2: RPCDispatcherStopped
}


class RPCExceptionProcessor(FieldProcessor):
    def check_py(self, value):
        assert isinstance(value, RPCException), (value, type(value))

    def check_raw(self, value):
        assert isinstance(value, str), (value, type(value))

    def raw_to_py(self, raw_value: str, strict):
        js = json.loads(raw_value)
        cls = _REVERSED_MAP[js['cls']]
        return cls(js['message'], js['traceback'])

    def py_to_raw(self, value: RPCException):
        return json.dumps({'message': value.message, 'traceback': value.traceback, 'cls': _EXCEPTIONS_MAP.get(type(value))})

    def my_type(cls):
        return 'RPCException'


rpc_exception_t = RPCExceptionProcessor()
