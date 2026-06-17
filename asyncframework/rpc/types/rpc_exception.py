# -*- coding:utf-8 -*-
from typing import Optional, Type
from packets.processors.base import TypeDef
from packets import json


__all__ = [
    'NotToHandle', 
    'RPCException', 
    'WrongConsumer', 
    'RPCSenderStopped', 
    'RPCDispatcherStopped', 
    'RPCConnectionLost',
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

class RPCConnectionLost(RPCException):
    """Exception on connection lost while waiting for reply
    """
    pass

class RPCDeliveryFailed(RPCException):
    __slots__ = (
        'correlation_id',
        'app_id',
        'reply_to'
    )
    """Exception caused by delivery error
    """
    def __init__(self, 
        message: str, 
        correlation_id: Optional[str], 
        app_id: Optional[str], 
        reply_to: Optional[str], 
        type: str | None = None, 
        traceback: str | None = None
    ):
        super().__init__(message, type, traceback)
        self.correlation_id = correlation_id
        self.app_id = app_id
        self.reply_to = reply_to


_EXCEPTIONS_MAP = {
    RPCException: 0,
    RPCSenderStopped: 1,
    RPCDispatcherStopped: 2,
    RPCConnectionLost: 3
}
_REVERSED_MAP = {
    0: RPCException,
    1: RPCSenderStopped,
    2: RPCDispatcherStopped,
    3: RPCConnectionLost
}


class RPCExceptionProcessor(TypeDef[RPCException]):
    def check_py(self, v: RPCException) -> bool:
        return isinstance(v, RPCException)

    def check_raw(self, r: str) -> bool:
        return isinstance(r, str)

    def raw_to_py(self, r: str, strict):
        js = json.loads(r)
        cls = _REVERSED_MAP[js['cls']]
        return cls(js['message'], js['traceback'])

    def py_to_raw(self, value: RPCException):
        return json.dumps({'message': value.message, 'traceback': value.traceback, 'cls': _EXCEPTIONS_MAP.get(type(value))})

    def zero_value(self) -> RPCException:
        return RPCException('')
    
    def self_type(self) -> Type[RPCException]:
        return RPCException


rpc_exception_t = RPCExceptionProcessor()
