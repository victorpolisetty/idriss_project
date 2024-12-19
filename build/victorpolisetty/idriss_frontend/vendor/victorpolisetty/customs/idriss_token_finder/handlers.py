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

import os
import requests
import json
from openai import OpenAI
from dataclasses import dataclass
from urllib.parse import unquote, urlparse
from aea.skills.base import Handler
from packages.eightballer.protocols.http.message import HttpMessage as ApiHttpMessage
from mech_client.interact import interact, ConfirmationType




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

    def handle_post_api_analyze(self, message: ApiHttpMessage, body):
        """Handle POST request for /api/analyze."""
        self.context.logger.debug(f"Request body: {body}")

        try:
            # Decode the body from bytes to string and parse it as JSON
            decoded_body = body.decode('utf-8')
            body_dict = json.loads(decoded_body)

            # Now you can safely use `.get()` on the dictionary
            query = body_dict.get("query", "test")  # Default to "test" if 'query' is not in the body
            max_results = body_dict.get("max_results", 1)

            # Prepare the parameters for the SearchCaster API
            params = {
                "count": max_results,
                "text": query,  # Use text search based on the query
            }

            # Make the API call to SearchCaster
            searchcaster_url = "https://searchcaster.xyz/api/search"
            response = requests.get(searchcaster_url, params=params)
            print('The response is:',response)

            # Check if the response from SearchCaster is successful
            if response.status_code == 200:
                result = response.json()  # Assuming the response is JSON
                self.context.logger.info("Successfully processed POST request for /api/analyze")
                self.context.logger.debug(f"Result from SearchCaster: {result}")

                return ApiResponse(
                    headers={},
                    content=json.dumps(result).encode("utf-8"),
                    status_code=200,
                    status_text="Successful analysis"
                )
            else:
                self.context.logger.error(f"Error from SearchCaster API: {response.status_code} - {response.text}")
                return ApiResponse(
                    headers={},
                    content=json.dumps({"error": "Error from SearchCaster API"}).encode("utf-8"),
                    status_code=500,
                    status_text="Internal Server Error"
                )

        except BadRequestError:
            self.context.logger.exception("Bad request")
            return ApiResponse(
                headers={},
                content=json.dumps({"error": "Bad request"}).encode("utf-8"),
                status_code=400,
                status_text="Bad Request"
            )

        except Exception as e:
            self.context.logger.exception("Unhandled exception")
            return ApiResponse(
                headers={},
                content=json.dumps({"error": str(e)}).encode("utf-8"),
                status_code=500,
                status_text="Internal Server Error"
            )

    def handle_post_api_predict(self, message: ApiHttpMessage, body):
        """Handle POST request for /api/predict."""
        self.context.logger.debug(f"Request body: {body}")
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        try:
            # Decode the body from bytes to string and parse it as JSON
            decoded_body = body.decode('utf-8')
            body_dict = json.loads(decoded_body)

            # Extract parameters from the body
            prompt_text = body_dict.get("prompt_text", "")

            if not prompt_text:
                raise BadRequestError("The 'prompt_text' parameter is required.")

            # Ensure the OpenAI API key is set
            if not client.api_key:
                raise BadRequestError("OpenAI API key not found in environment variables.")

            # Prepare the messages parameter for the ChatCompletion API
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_text}
            ]

            # Call the OpenAI GPT-4 API to generate the result
            response = client.chat.completions.create(
                model="gpt-4",  # Use GPT-4
                messages=messages  # Provide the conversation history
            )

            # Extract the content from the ChatCompletionMessage object
            result_content = response.choices[0].message.content

            self.context.logger.info('The result content is: ' + result_content)

            # Return the result as a JSON response
            return ApiResponse(
                headers={},
                content=json.dumps({"message": result_content}).encode("utf-8"),
                status_code=200,
                status_text="Prediction result"
            )

        except BadRequestError as e:
            self.context.logger.exception("Bad request")
            return ApiResponse(
                headers={},
                content=json.dumps({"error": str(e)}).encode("utf-8"),
                status_code=400,
                status_text="Bad Request"
            )

        except Exception as e:
            self.context.logger.exception("Unhandled exception")
            return ApiResponse(
                headers={},
                content=json.dumps({"error": str(e)}).encode("utf-8"),
                status_code=500,
                status_text="Internal Server Error"
            )
