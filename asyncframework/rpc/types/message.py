# -*- coding:utf-8 -*-
from typing import Any, List, Dict
from enum import Enum
from packets import Packet, Field, string_t, Enumeration, any_t, Array, Hash, int_t
from .rpc_exception import rpc_exception_t, RPCException


__all__ = ['MessageType', 'Request', 'Response', 'BaseMessage', 'ResponseType']


class MessageType(Enum):
    MSG_REQUEST: int = 0
    MSG_RESPONSE: int = 1


message_type_t = Enumeration(MessageType)


class ResponseType(Enum):
    RESPONSE_TYPE_NONE = 0
    RESPONSE_TYPE_RESULT = 1


response_type_t = Enumeration(ResponseType)


class BaseMessage(Packet):
    correlation_id: str
    headers: Dict[str, Any]
    app_id: str
    message_type: MessageType = Field(message_type_t)  # type: ignore


class Request(BaseMessage):
    message_type: MessageType = Field(message_type_t, override=True, default=MessageType.MSG_REQUEST)  # type: ignore
    message: Any = Field(any_t, required=True)  # type: ignore
    response_type: int = Field(response_type_t, required=True)  # type: ignore
    rargs: List[Any] = Field(Array(any_t), 'args')  # type: ignore
    rkwargs: Dict[str, Any] = Field(Hash(string_t, any_t), 'kwargs')  # type: ignore

    @property
    def response_required(self) -> bool:
        return self.response_type != ResponseType.RESPONSE_TYPE_NONE


class Response(BaseMessage):
    message_type: MessageType = Field(message_type_t, override=True, default=MessageType.MSG_RESPONSE)  # type: ignore
    result: Any = Field(any_t)  # type: ignore
    exception: RPCException = Field(rpc_exception_t)  # type: ignore
