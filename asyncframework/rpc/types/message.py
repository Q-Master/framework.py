# -*- coding:utf-8 -*-
from typing import Any, List, Dict, Optional
from enum import Enum
from packets import Packet, makeField
from packets.processors import string_t, Enumeration, any_t, Array, Hash, int_t
from .rpc_exception import rpc_exception_t, RPCException


__all__ = ['MessageType', 'Request', 'Response', 'BaseMessage', 'ResponseType', 'MethodReply']


class MessageType(Enum):
    MSG_REQUEST = 0
    MSG_RESPONSE = 1


message_type_t = Enumeration(MessageType)


class ResponseType(Enum):
    RESPONSE_TYPE_NONE = 0
    RESPONSE_TYPE_RESULT = 1


response_type_t = Enumeration(ResponseType)


class BaseMessage(Packet):
    correlation_id: str
    headers: Dict[str, Any]
    app_id: str
    message_type: MessageType = makeField(message_type_t)


class Request(BaseMessage):
    message_type: MessageType = makeField(message_type_t, override=True, default=MessageType.MSG_REQUEST)
    method: Any = makeField(any_t, required=True)
    response_type: int = makeField(response_type_t, required=True)
    rargs: Optional[List[Any]] = makeField(Array(any_t), 'args')
    rkwargs: Optional[Dict[str, Any]] = makeField(Hash(string_t, any_t), 'kwargs')

    @property
    def response_required(self) -> bool:
        return self.response_type != ResponseType.RESPONSE_TYPE_NONE


class Response(BaseMessage):
    message_type: MessageType = makeField(message_type_t, override=True, default=MessageType.MSG_RESPONSE)
    result: Optional[Any] = makeField(any_t)
    exception: Optional[RPCException] = makeField(rpc_exception_t)


class MethodReply():
    result: Any
    headers: Dict[str, Any]

    def __init__(self, result: Any, headers: Dict[str, Any] = {}) -> None:
        self.result = result
        self.headers = headers