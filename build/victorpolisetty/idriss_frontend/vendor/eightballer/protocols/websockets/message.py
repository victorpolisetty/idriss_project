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

"""This module contains websockets's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Optional, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.eightballer.protocols.websockets.custom_types import (
    ErrorCode as CustomErrorCode,
)

_default_logger = logging.getLogger(
    "aea.packages.eightballer.protocols.websockets.message"
)

DEFAULT_BODY_SIZE = 4


class WebsocketsMessage(Message):
    """A protocol for WebSocket client applications, facilitating two-way communication over WebSocket connections."""

    protocol_id = PublicId.from_str("eightballer/websockets:0.1.0")
    protocol_specification_id = PublicId.from_str("eightballer/websockets:0.1.0")

    ErrorCode = CustomErrorCode

    class Performative(Message.Performative):
        """Performatives for the websockets protocol."""

        CONNECT = "connect"
        CONNECTION_ACK = "connection_ack"
        DISCONNECT = "disconnect"
        DISCONNECT_ACK = "disconnect_ack"
        ERROR = "error"
        RECEIVE = "receive"
        SEND = "send"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {
        "connect",
        "connection_ack",
        "disconnect",
        "disconnect_ack",
        "error",
        "receive",
        "send",
    }
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "code",
            "data",
            "dialogue_reference",
            "message",
            "message_id",
            "performative",
            "reason",
            "success",
            "target",
            "url",
        )

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs: Any,
    ):
        """
        Initialise an instance of WebsocketsMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        :param **kwargs: extra options.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=WebsocketsMessage.Performative(performative),
            **kwargs,
        )

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return self._performatives

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        enforce(self.is_set("dialogue_reference"), "dialogue_reference is not set.")
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        enforce(self.is_set("message_id"), "message_id is not set.")
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> Performative:  # type: ignore # noqa: F821
        """Get the performative of the message."""
        enforce(self.is_set("performative"), "performative is not set.")
        return cast(WebsocketsMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def code(self) -> CustomErrorCode:
        """Get the 'code' content from the message."""
        enforce(self.is_set("code"), "'code' content is not set.")
        return cast(CustomErrorCode, self.get("code"))

    @property
    def data(self) -> str:
        """Get the 'data' content from the message."""
        enforce(self.is_set("data"), "'data' content is not set.")
        return cast(str, self.get("data"))

    @property
    def message(self) -> str:
        """Get the 'message' content from the message."""
        enforce(self.is_set("message"), "'message' content is not set.")
        return cast(str, self.get("message"))

    @property
    def reason(self) -> Optional[str]:
        """Get the 'reason' content from the message."""
        return cast(Optional[str], self.get("reason"))

    @property
    def success(self) -> bool:
        """Get the 'success' content from the message."""
        enforce(self.is_set("success"), "'success' content is not set.")
        return cast(bool, self.get("success"))

    @property
    def url(self) -> str:
        """Get the 'url' content from the message."""
        enforce(self.is_set("url"), "'url' content is not set.")
        return cast(str, self.get("url"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the websockets protocol."""
        try:
            enforce(
                isinstance(self.dialogue_reference, tuple),
                "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                    type(self.dialogue_reference)
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[0], str),
                "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[0])
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[1], str),
                "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[1])
                ),
            )
            enforce(
                type(self.message_id) is int,
                "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                    type(self.message_id)
                ),
            )
            enforce(
                type(self.target) is int,
                "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                    type(self.target)
                ),
            )

            # Light Protocol Rule 2
            # Check correct performative
            enforce(
                isinstance(self.performative, WebsocketsMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == WebsocketsMessage.Performative.CONNECT:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.url, str),
                    "Invalid type for content 'url'. Expected 'str'. Found '{}'.".format(
                        type(self.url)
                    ),
                )
            elif self.performative == WebsocketsMessage.Performative.CONNECTION_ACK:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.success, bool),
                    "Invalid type for content 'success'. Expected 'bool'. Found '{}'.".format(
                        type(self.success)
                    ),
                )
            elif self.performative == WebsocketsMessage.Performative.SEND:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.data, str),
                    "Invalid type for content 'data'. Expected 'str'. Found '{}'.".format(
                        type(self.data)
                    ),
                )
            elif self.performative == WebsocketsMessage.Performative.RECEIVE:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.data, str),
                    "Invalid type for content 'data'. Expected 'str'. Found '{}'.".format(
                        type(self.data)
                    ),
                )
            elif self.performative == WebsocketsMessage.Performative.DISCONNECT:
                expected_nb_of_contents = 0
                if self.is_set("reason"):
                    expected_nb_of_contents += 1
                    reason = cast(str, self.reason)
                    enforce(
                        isinstance(reason, str),
                        "Invalid type for content 'reason'. Expected 'str'. Found '{}'.".format(
                            type(reason)
                        ),
                    )
            elif self.performative == WebsocketsMessage.Performative.DISCONNECT_ACK:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.success, bool),
                    "Invalid type for content 'success'. Expected 'bool'. Found '{}'.".format(
                        type(self.success)
                    ),
                )
            elif self.performative == WebsocketsMessage.Performative.ERROR:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.message, str),
                    "Invalid type for content 'message'. Expected 'str'. Found '{}'.".format(
                        type(self.message)
                    ),
                )
                enforce(
                    isinstance(self.code, CustomErrorCode),
                    "Invalid type for content 'code'. Expected 'ErrorCode'. Found '{}'.".format(
                        type(self.code)
                    ),
                )

            # Check correct content count
            enforce(
                expected_nb_of_contents == actual_nb_of_contents,
                "Incorrect number of contents. Expected {}. Found {}".format(
                    expected_nb_of_contents, actual_nb_of_contents
                ),
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                enforce(
                    self.target == 0,
                    "Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.".format(
                        self.target
                    ),
                )
        except (AEAEnforceError, ValueError, KeyError) as e:
            _default_logger.error(str(e))
            return False

        return True
