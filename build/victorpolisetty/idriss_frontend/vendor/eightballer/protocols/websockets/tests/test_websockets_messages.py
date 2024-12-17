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

"""Test messages module for websockets protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.eightballer.protocols.websockets.message import WebsocketsMessage
from packages.eightballer.protocols.websockets.custom_types import ErrorCode


class TestMessageWebsockets(BaseProtocolMessagesTestCase):
    """Test for the 'websockets' protocol message."""

    MESSAGE_CLASS = WebsocketsMessage

    def build_messages(self) -> List[WebsocketsMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.CONNECT,
                url="some str",
            ),
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.CONNECTION_ACK,
                success=True,
            ),
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.SEND,
                data="some str",
            ),
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.RECEIVE,
                data="some str",
            ),
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.DISCONNECT,
                reason="some str",
            ),
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.DISCONNECT_ACK,
                success=True,
            ),
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.ERROR,
                message="some str",
                code=ErrorCode(1),
            ),
        ]

    def build_inconsistent(self) -> List[WebsocketsMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.CONNECT,
                # skip content: url
            ),
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.CONNECTION_ACK,
                # skip content: success
            ),
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.SEND,
                # skip content: data
            ),
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.RECEIVE,
                # skip content: data
            ),
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.DISCONNECT_ACK,
                # skip content: success
            ),
            WebsocketsMessage(
                performative=WebsocketsMessage.Performative.ERROR,
                # skip content: message
                code=ErrorCode(1),
            ),
        ]
