# -*- coding: utf-8 -*-
from typing import Optional
from packets import makeField, Packet
from packets.typedef.string_t import string_t, StringT
from packets.processors.hash import HashT, Hash


__all__ = ['RPCMessage', 'RPCConnectionMixin']


class RPCMessage(Packet):
    msg: StringT = makeField(string_t, required=True)
    msg_type: StringT = makeField(string_t, required=True)
    correlation_id: Optional[StringT] = makeField(string_t)
    content_type: StringT = makeField(string_t, default='application/text')
    app_id: Optional[StringT] = makeField(string_t)
    headers: HashT = makeField(Hash(string_t, string_t), default={})
    reply_to: Optional[StringT] = makeField(string_t)


class RPCConnectionMixin:
    """Connection mixin on streams not supporting sending additional params through
    the connection channel.
    """
    async def write(self, 
        msg: str, 
        type: str,
        correlation_id: Optional[str] = None, 
        content_type: Optional[str] = None,
        app_id: Optional[str] = None,
        headers: Optional[dict] = None,
        reply_to: Optional[str] = None
    ):
        message = RPCMessage(
            msg = msg,
            msg_type = type,
            correlation_id = correlation_id,
            app_id = app_id,
            reply_to = reply_to
        )
        if content_type:
            message.content_type = content_type
        if headers:
            message.headers = HashT(headers)
        await super().write(message.dumps()) # type: ignore

    async def on_message_received(self, msg: str):
        message = RPCMessage.loads(msg)
        await super().on_message_received( # type: ignore
            message.msg, 
            msg_type = message.msg_type, 
            correlation_id = message.correlation_id, 
            content_type = message.content_type, 
            app_id = message.app_id,
            headers = message.headers,
            reply_to = message.reply_to
        ) 

    async def on_message_returned(self, msg: str):
        message = RPCMessage.loads(msg)
        await super().on_message_returned( # type: ignore
            message.msg, 
            correlation_id = message.correlation_id, 
            app_id = message.app_id,
            reply_to = message.reply_to,
            raw_msg = msg
        )