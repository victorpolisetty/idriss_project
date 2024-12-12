# ------------------------------------------------------------------------------
#
#   Copyright 2024 victorpolisetty
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

"""This package contains a scaffold of a handler."""

import re
import json
from dataclasses import dataclass
from urllib.parse import unquote, urlparse

from aea.skills.base import Handler
from packages.eightballer.protocols.http.message import HttpMessage as ApiHttpMessage




from .exceptions import (
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ConflictError,
    ValidationError,
    InternalServerError,
    ServiceUnavailableError
)





@dataclass
class ApiResponse:
    """Api response."""
    headers: dict[str, str]
    content: bytes
    status_code: int
    status_text: str


class ApiHttpHandler(Handler):
    """Implements the API HTTP handler."""

    SUPPORTED_PROTOCOL = ApiHttpMessage.protocol_id  # type: Optional[str]

    def setup(self) -> None:
        """Set up the handler."""

    def teardown(self) -> None:
        """Tear down the handler."""

    def handle(self, message: ApiHttpMessage) -> None:
        """Handle incoming API HTTP messages."""
        method = message.method.lower()
        parsed_url = urlparse(unquote(message.url))
        path = parsed_url.path
        body = message.body

        self.context.logger.info(f"Received {method.upper()} request for {path}")

        normalized_path = path.rstrip("/")

        handler_name = f"handle_{method}_{normalized_path.lstrip('/').replace('/', '_')}"

        handler_method = getattr(self, handler_name, None)

        if handler_method:
            self.context.logger.debug(f"Found handler method: {handler_name}")
            kwargs = {"body": body} if method in {"post", "put", "patch", "delete"} else {}

            try:
                result = handler_method(message, **kwargs)
                self.context.logger.info(f"Successfully handled {method.upper()} request for {path}")
                return result
            except Exception as e:
                self.context.logger.exception(f"Error handling {method.upper()} request for {path}: {e!s}")
                raise
        else:
            self.context.logger.warning(f"No handler found for {method.upper()} request to {path}")
            return self.handle_unexpected_message(message)

    def handle_get_api(self, _message: ApiHttpMessage):
        """Handle GET request for /api."""
        try:
            result = none_dao.get_all()

            self.context.logger.info("Successfully processed GET request for /api")
            self.context.logger.debug(f"Result: {result}")
            return ApiResponse(
                headers={},
                content=result,
                status_code=200,
                status_text="HTML response"
            )

        except Exception as e:
            self.context.logger.exception("Unhandled exception")
            return ApiResponse(
                headers={},
                content=json.dumps({"error": str(e)}).encode("utf-8"),
                status_code=500,
                status_text="Internal Server Error"
            )

    def handle_post_api(self, _message: ApiHttpMessage):
        """Handle GET request for /api."""
        try:
            # Call the Searchcaster API with the 'test' parameter
            searchcaster_endpoint = "https://searchcaster.xyz/api/search"
            params = {"text": "test", "count": 1}  # Adjust 'count' as needed

            self.context.logger.info(f"Calling Searchcaster API at {searchcaster_endpoint} with params: {params}")
            response = requests.get(searchcaster_endpoint, params=params)

            # Raise an error if the request failed
            response.raise_for_status()

            # Parse and log the response
            result = response.json()
            self.context.logger.debug(f"Searchcaster API Response: {result}")

            # Return the successful API response
            return ApiResponse(
                headers={"Content-Type": "application/json"},
                content=json.dumps(result).encode("utf-8"),
                status_code=200,
                status_text="OK"
            )

        except requests.exceptions.RequestException as e:
            self.context.logger.exception(f"Error calling Searchcaster API: {e}")
            return ApiResponse(
                headers={"Content-Type": "application/json"},
                content=json.dumps({"error": "Error calling Searchcaster API"}).encode("utf-8"),
                status_code=500,
                status_text="Internal Server Error"
            )

        except Exception as e:
            self.context.logger.exception("Unhandled exception")
            return ApiResponse(
                headers={"Content-Type": "application/json"},
                content=json.dumps({"error": str(e)}).encode("utf-8"),
                status_code=500,
                status_text="Internal Server Error"
            )

    def handle_unexpected_message(self, message):
        """Handler for unexpected messages."""
        self.context.logger.info(f"Received unexpected message: {message}")
