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

"""
This module contains the classes required for websockets dialogue management.

- WebsocketsDialogue: The dialogue class maintains state of a dialogue and manages it.
- WebsocketsDialogues: The dialogues class keeps track of all dialogues.
"""

from abc import ABC
from typing import Dict, Type, Callable, FrozenSet, cast

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, Dialogues, DialogueLabel

from packages.eightballer.protocols.websockets.message import WebsocketsMessage


class WebsocketsDialogue(Dialogue):
    """The websockets dialogue class maintains state of a dialogue and manages it."""

    INITIAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {WebsocketsMessage.Performative.CONNECT, WebsocketsMessage.Performative.SEND}
    )
    TERMINAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset({WebsocketsMessage.Performative.DISCONNECT_ACK})
    VALID_REPLIES: Dict[Message.Performative, FrozenSet[Message.Performative]] = {
        WebsocketsMessage.Performative.CONNECT: frozenset(
            {
                WebsocketsMessage.Performative.CONNECTION_ACK,
                WebsocketsMessage.Performative.ERROR,
            }
        ),
        WebsocketsMessage.Performative.CONNECTION_ACK: frozenset(
            {
                WebsocketsMessage.Performative.SEND,
                WebsocketsMessage.Performative.RECEIVE,
                WebsocketsMessage.Performative.ERROR,
                WebsocketsMessage.Performative.DISCONNECT,
            }
        ),
        WebsocketsMessage.Performative.DISCONNECT: frozenset(
            {
                WebsocketsMessage.Performative.DISCONNECT_ACK,
                WebsocketsMessage.Performative.ERROR,
            }
        ),
        WebsocketsMessage.Performative.DISCONNECT_ACK: frozenset(),
        WebsocketsMessage.Performative.ERROR: frozenset({WebsocketsMessage.Performative.SEND}),
        WebsocketsMessage.Performative.RECEIVE: frozenset(
            {
                WebsocketsMessage.Performative.SEND,
                WebsocketsMessage.Performative.RECEIVE,
                WebsocketsMessage.Performative.ERROR,
                WebsocketsMessage.Performative.DISCONNECT,
            }
        ),
        WebsocketsMessage.Performative.SEND: frozenset(
            {
                WebsocketsMessage.Performative.SEND,
                WebsocketsMessage.Performative.RECEIVE,
                WebsocketsMessage.Performative.ERROR,
                WebsocketsMessage.Performative.DISCONNECT,
            }
        ),
    }

    class Role(Dialogue.Role):
        """This class defines the agent's role in a websockets dialogue."""

        CLIENT = "client"
        SERVER = "server"

    class EndState(Dialogue.EndState):
        """This class defines the end states of a websockets dialogue."""

        DISCONNECT_ACK = 0
        DISCONNECT = 1

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[WebsocketsMessage] = WebsocketsMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class used
        """
        Dialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            message_class=message_class,
            self_address=self_address,
            role=role,
        )


class WebsocketsDialogues(Dialogues, ABC):
    """This class keeps track of all websockets dialogues."""

    END_STATES = frozenset(
        {
            WebsocketsDialogue.EndState.DISCONNECT_ACK,
            WebsocketsDialogue.EndState.DISCONNECT,
        }
    )

    _keep_terminal_state_dialogues = False

    def __init__(
        self,
        self_address: Address,
        role_from_first_message: Callable[[Message, Address], Dialogue.Role],
        dialogue_class: Type[WebsocketsDialogue] = WebsocketsDialogue,
    ) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        :param dialogue_class: the dialogue class used
        :param role_from_first_message: the callable determining role from first message
        """
        Dialogues.__init__(
            self,
            self_address=self_address,
            end_states=cast(FrozenSet[Dialogue.EndState], self.END_STATES),
            message_class=WebsocketsMessage,
            dialogue_class=dialogue_class,
            role_from_first_message=role_from_first_message,
        )
