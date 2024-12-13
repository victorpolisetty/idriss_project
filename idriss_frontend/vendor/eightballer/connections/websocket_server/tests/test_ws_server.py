# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains the tests of the HTTP Server connection module."""

import os
import socket
import asyncio
import logging
from typing import Tuple, cast
from traceback import print_exc
from unittest.mock import MagicMock

import pytest
import aiohttp
from aea.common import Address
from aea.mail.base import Message, Envelope
from aea.identity.base import Identity
from aiohttp.client_reqrep import ClientResponse
from aea.configurations.base import ConnectionConfig
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.eightballer.protocols.http.message import HttpMessage
from packages.eightballer.protocols.http.dialogues import (
    HttpDialogue,
    HttpDialogues as BaseHttpDialogues,
)
from packages.eightballer.connections.websocket_server.connection import (
    WebSocketServerConnection,
)


ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


logger = logging.getLogger(__name__)


def get_host() -> str:
    """Get the host."""
    return "0.0.0.0"  # noqa


def get_unused_tcp_port() -> int:
    """Get an unused TCP port."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((get_host(), 0))  # noqa
        return s.getsockname()[1]


class HttpDialogues(BaseHttpDialogues):
    """The dialogues class keeps track of all http dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            del receiver_address, message
            return HttpDialogue.Role.SERVER

        BaseHttpDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


@pytest.mark.asyncio
class TestWebSocketServer:
    """Tests for HTTPServer connection."""

    async def request(self, method: str, path: str, **kwargs) -> ClientResponse:
        """
        Make a http request.

        :param method: HTTP method: GET, POST etc
        :param path: path to request on server. full url constructed automatically

        :return: http response
        """
        try:
            url = f"http://{self.host}:{self.port}{path}"
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as resp:
                    await resp.read()
                    return resp
        except Exception:
            print_exc()
            raise

    def setup(self):
        """Initialise the test case."""
        self.identity = Identity("name", address="my_key", public_key="my_public_key")
        self.agent_address = self.identity.address
        self.host = get_host()
        self.port = get_unused_tcp_port()
        self.api_spec_path = os.path.join(ROOT_DIR, "tests", "data", "petstore_sim.yaml")
        self.connection_id = WebSocketServerConnection.connection_id
        self.protocol_id = HttpMessage.protocol_id
        self.target_skill_id = "some_author/some_skill:0.1.0"

        self.configuration = ConnectionConfig(
            host=self.host,
            port=self.port,
            target_skill_id=self.target_skill_id,
            api_spec_path=self.api_spec_path,
            connection_id=WebSocketServerConnection.connection_id,
            restricted_to_protocols={HttpMessage.protocol_id},
        )
        self.wss_connection = WebSocketServerConnection(
            configuration=self.configuration,
            data_dir=MagicMock(),
            identity=self.identity,
        )
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.wss_connection.connect())
        self.connection_address = str(WebSocketServerConnection.connection_id)
        self._dialogues = HttpDialogues(self.target_skill_id)
        self.original_timeout = self.wss_connection.channel.timeout_window

    @pytest.mark.asyncio
    async def test_http_connection_disconnect_channel(self):
        """Test the disconnect."""
        await self.wss_connection.channel.disconnect()
        assert self.wss_connection.channel.is_stopped

    def _get_message_and_dialogue(self, envelope: Envelope) -> Tuple[HttpMessage, HttpDialogue]:
        message = cast(HttpMessage, envelope.message)
        dialogue = cast(HttpDialogue, self._dialogues.update(message))
        assert dialogue is not None
        return message, dialogue

    def teardown(self):
        """Teardown the test case."""
        self.loop.run_until_complete(self.wss_connection.disconnect())
        self.wss_connection.channel.timeout_window = self.original_timeout
