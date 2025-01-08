"""
Behaviours for the simple react skill.
"""

import json
import os
from typing import Optional, cast
import requests
from aea.skills.base import Behaviour
from packages.eightballer.protocols.websockets.message import WebsocketsMessage
from packages.eightballer.skills.ui_loader_abci.models import (
    UserInterfaceClientStrategy,
)


class LogReadingBehaviour(Behaviour):
    """Handles WebSocket interactions and API calls."""

    def setup(self):
        """
        Setup the behaviour.
        """
        # self.log_file = os.environ.get("LOG_FILE", "log.txt")
        self.context.logger.info("IdrissBrowserConnectionBehviour initialized.")

    def teardown(self):
        """
        Teardown the behaviour.
        """
        self.context.logger.info("IdrissBrowserConnectionBehviour stopped.")

    @property
    def strategy(self) -> Optional[str]:
        """Get the strategy."""
        return cast(
            UserInterfaceClientStrategy, self.context.user_interface_client_strategy
        )

    def act(self):
        """
        Periodically check for pings and handle them.
        """
        self.check_for_ping()

    def send_message(self, data, dialogue):
        """
        Send a message to the client.
        """
        msg = dialogue.reply(
            performative=WebsocketsMessage.Performative.SEND,
            data=data,
        )
        self.context.outbox.put_message(message=msg)

    def check_for_ping(self):
        """
        Listen for 'ping' messages from WebSocket clients and handle them.
        """
        for _, dialogue in self.strategy.clients.items():
            self.context.logger.info(f"Dialogue attributes: {dir(dialogue)}")
            # if last_message:
            #     try:
            #         # Parse the 'data' field as JSON
            #         message_content = json.loads(last_message.data)
                    
            #         # Check for nested 'type' and 'query'
            #         if message_content.get("type") == "ping" and message_content.get("query") == "Keep-alive ping":
            #             self.context.logger.info("Received 'ping' message. Calling analyze endpoint.")
            #             self.call_analyze_endpoint(dialogue)
            #         else:
            #             self.context.logger.info("Received a non-ping message.")
            #     except json.JSONDecodeError:
            #         self.context.logger.error("Failed to parse 'data' field as JSON.")


    def call_analyze_endpoint(self, dialogue):
        """
        Make a call to the /api/analyze endpoint or external API.
        """
        api_url = "https://searchcaster.xyz/api/search?text=memecoins"  # Replace with your API URL
        headers = {"Content-Type": "application/json"}

        try:
            # Call the external API
            response = requests.get(api_url, headers=headers, timeout=10)

            if response.status_code == 200:
                self.context.logger.info("API call successful.")
                # Send the API response back to the WebSocket client
                self.send_message(response.text, dialogue)
            else:
                self.context.logger.error(f"API call failed with status {response.status_code}: {response.text}")
                self.send_message(
                    f"API call failed with status {response.status_code}.",
                    dialogue,
                )
        except requests.RequestException as e:
            self.context.logger.error(f"Error while calling the API: {e}")
            self.send_message(
                f"Error while calling the API: {str(e)}", dialogue
            )
