# -*- coding:utf-8 -*-
from typing import Any, List, Dict
from enum import Enum
from packets import Packet, Field, string_t, Enumeration, any_t, Array, Hash, bool_t
from .rpc_exception import rpc_exception_t, RPCException


__all__ = ['MessageType', 'Request', 'Response', 'BaseMessage']


class MessageType(Enum):
    MSG_REQUEST: int = 0
    MSG_RESPONSE: int = 1


message_type_t = Enumeration(MessageType)


class BaseMessage(Packet):
    message_type: MessageType = Field(message_type_t)  # type: ignore
    correlation_id: str = Field(string_t)  # type: ignore


class Request(BaseMessage):
    message_type: MessageType = Field(message_type_t, override=True, default=MessageType.MSG_REQUEST)  # type: ignore
    message: Any = Field(any_t, required=True)  # type: ignore
    response_required: bool = Field(bool_t, default=True)  # type: ignore
    args: List[Any] = Field(Array(any_t))  # type: ignore
    kwargs: Dict[str, Any] = Field(Hash(string_t, any_t))  # type: ignore


class Response(BaseMessage):
    message_type: MessageType = Field(message_type_t, override=True, default=MessageType.MSG_RESPONSE)  # type: ignore
    result: Any = Field(any_t)  # type: ignore
    exception: RPCException = Field(rpc_exception_t)  # type: ignore
