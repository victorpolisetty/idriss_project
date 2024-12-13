# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 eightballer
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Serialization module for websockets protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import cast

from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Serializer

from packages.eightballer.protocols.websockets import websockets_pb2
from packages.eightballer.protocols.websockets.custom_types import ErrorCode
from packages.eightballer.protocols.websockets.message import WebsocketsMessage


class WebsocketsSerializer(Serializer):
    """Serialization for the 'websockets' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'Websockets' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(WebsocketsMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        websockets_msg = websockets_pb2.WebsocketsMessage()

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == WebsocketsMessage.Performative.CONNECT:
            performative = websockets_pb2.WebsocketsMessage.Connect_Performative()  # type: ignore
            url = msg.url
            performative.url = url
            websockets_msg.connect.CopyFrom(performative)
        elif performative_id == WebsocketsMessage.Performative.CONNECTION_ACK:
            performative = websockets_pb2.WebsocketsMessage.Connection_Ack_Performative()  # type: ignore
            success = msg.success
            performative.success = success
            websockets_msg.connection_ack.CopyFrom(performative)
        elif performative_id == WebsocketsMessage.Performative.SEND:
            performative = websockets_pb2.WebsocketsMessage.Send_Performative()  # type: ignore
            data = msg.data
            performative.data = data
            websockets_msg.send.CopyFrom(performative)
        elif performative_id == WebsocketsMessage.Performative.RECEIVE:
            performative = websockets_pb2.WebsocketsMessage.Receive_Performative()  # type: ignore
            data = msg.data
            performative.data = data
            websockets_msg.receive.CopyFrom(performative)
        elif performative_id == WebsocketsMessage.Performative.DISCONNECT:
            performative = websockets_pb2.WebsocketsMessage.Disconnect_Performative()  # type: ignore
            if msg.is_set("reason"):
                performative.reason_is_set = True
                reason = msg.reason
                performative.reason = reason
            websockets_msg.disconnect.CopyFrom(performative)
        elif performative_id == WebsocketsMessage.Performative.DISCONNECT_ACK:
            performative = websockets_pb2.WebsocketsMessage.Disconnect_Ack_Performative()  # type: ignore
            success = msg.success
            performative.success = success
            websockets_msg.disconnect_ack.CopyFrom(performative)
        elif performative_id == WebsocketsMessage.Performative.ERROR:
            performative = websockets_pb2.WebsocketsMessage.Error_Performative()  # type: ignore
            message = msg.message
            performative.message = message
            code = msg.code
            ErrorCode.encode(performative.code, code)
            websockets_msg.error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = websockets_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'Websockets' message.

        :param obj: the bytes object.
        :return: the 'Websockets' message.
        """
        message_pb = ProtobufMessage()
        websockets_pb = websockets_pb2.WebsocketsMessage()
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        websockets_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = websockets_pb.WhichOneof("performative")
        performative_id = WebsocketsMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == WebsocketsMessage.Performative.CONNECT:
            url = websockets_pb.connect.url
            performative_content["url"] = url
        elif performative_id == WebsocketsMessage.Performative.CONNECTION_ACK:
            success = websockets_pb.connection_ack.success
            performative_content["success"] = success
        elif performative_id == WebsocketsMessage.Performative.SEND:
            data = websockets_pb.send.data
            performative_content["data"] = data
        elif performative_id == WebsocketsMessage.Performative.RECEIVE:
            data = websockets_pb.receive.data
            performative_content["data"] = data
        elif performative_id == WebsocketsMessage.Performative.DISCONNECT:
            if websockets_pb.disconnect.reason_is_set:
                reason = websockets_pb.disconnect.reason
                performative_content["reason"] = reason
        elif performative_id == WebsocketsMessage.Performative.DISCONNECT_ACK:
            success = websockets_pb.disconnect_ack.success
            performative_content["success"] = success
        elif performative_id == WebsocketsMessage.Performative.ERROR:
            message = websockets_pb.error.message
            performative_content["message"] = message
            pb2_code = websockets_pb.error.code
            code = ErrorCode.decode(pb2_code)
            performative_content["code"] = code
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return WebsocketsMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
