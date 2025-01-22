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

from pathlib import Path
import re
import os
import sys
import requests
import json
from openai import OpenAI
from dataclasses import dataclass
from urllib.parse import unquote, urlparse
from aea.skills.base import Handler
from packages.eightballer.protocols.http.message import HttpMessage as ApiHttpMessage
from mech_client.interact import interact, ConfirmationType
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
current_dir = Path(__file__).parent
sys.path.append(str(current_dir.resolve()))

from daos.analyze_request_dao import AnalyzeRequestDAO


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

# Load environment variables from .env file
load_dotenv()

# Access environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analyze_request_dao = AnalyzeRequestDAO()

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

        normalized_path = self.normalize_path(path)

        handler_name, kwargs = self.get_handler_name_and_kwargs(method, normalized_path, path, body)

        handler_method = getattr(self, handler_name, None)

        if handler_method:
            self.context.logger.debug(f"Found handler method: {handler_name}")
            return handler_method(message, **kwargs)
        self.context.logger.warning(f"No handler found for {method.upper()} request to {path}")
        return self.handle_unexpected_message(message)
        
    def normalize_path(self, path: str) -> str:                                                                                                                                                                                                                                                      
        """Normalize the path using regex substitution."""                                                                                                                                                                                                                                           
        normalized_path = path.rstrip("/")
        self.context.logger.debug(f"Normalized path: {normalized_path}")

        substitutions = {
            r"^/api/user/(?P<wallet_address>[^/]+)$": "/api/user/walletAddress",
            r"^/api/wallet/(?P<wallet_address>[^/]+)$": "/api/wallet/walletAddress",
        }

        for pattern, replacement in substitutions.items():
            normalized_path = re.sub(pattern, replacement, normalized_path)
        
        self.context.logger.debug(f"After regex substitutions: {normalized_path}")
        return normalized_path
    
    def get_handler_name_and_kwargs(self, method: str, normalized_path: str, original_path: str, body: bytes) -> tuple:
        """Get the handler name and kwargs for the given method and path."""
        handler_name = f"handle_{method}_{normalized_path.lstrip('/').replace('/', '_')}"

        self.context.logger.debug(f"Initial handler name: {handler_name}")
        handler_name = handler_name.replace("walletAddress", "by_wallet_address")
        self.context.logger.debug(f"Final handler name: {handler_name}")

        kwargs = {"body": body} if method in {"post", "put", "patch"} else {}
        patterns = [
            (r"^/api/user/(?P<wallet_address>[^/]+)$", ["wallet_address"]),
            (r"^/api/wallet/(?P<wallet_address>[^/]+)$", ["wallet_address"]),
        ]

        for pattern, param_names in patterns:
            match = re.search(pattern, original_path)
            if match:
                for param_name in param_names:
                    kwargs[param_name] = match.group(param_name)
                break
        self.context.logger.debug(f"Final kwargs: {kwargs}")
        return handler_name, kwargs
    
    def extract_best_ticker_with_gpt(self, casts, prompt) -> str:
        """
        Use GPT to determine the best-matching ticker from the casts based on the prompt.

        :param prompt: The user's natural language prompt.
        :param casts: The list of casts to analyze.
        :return: The best-matching ticker as determined by GPT.
        """
        client = OpenAI(api_key=OPENAI_API_KEY)

        # Build the context with the prompt and casts
        system_prompt = (
            "You are a financial assistant tasked with analyzing text data to find the best-matching ticker symbol "
            "based on a user's natural language query. The user will provide a prompt, and you will analyze the provided "
            "list of texts (casts) to find the most relevant ticker symbol."
            "If no ticker symbol is relevant, return the most relevant one you can find."
        )

        user_message = (
            f"Prompt: {prompt}\n\n"
            f"Here are the casts:\n{casts}\n\n"
            "Please provide the best-matching ticker symbol"
        )

        try:
            # Call the GPT API
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract GPT's response
            gpt_response = response.choices[0].message.content.strip()

            # Log and return the result
            self.context.logger.info(f"GPT determined best-matching ticker: {gpt_response}")
            return gpt_response if gpt_response else "No match found"

        except Exception as e:
            self.context.logger.error(f"Error using GPT to extract ticker: {str(e)}")
            return "Error: Unable to determine ticker"


        
    def parse_prompt_with_gpt(self, prompt: str) -> dict:
        """Parse a natural language prompt using GPT and double-check parameters."""
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # GPT-4 system prompt to guide its output
        system_prompt = (
            "You are an assistant that translates natural language prompts into API query parameters."
            "Parse the input prompt and return a JSON object with keys: text, engagement, count, username, and age_limit_days."
            "The engagement key must be one of: reactions, recasts, replies, watches. Use your best judgement to pick one of these based on the prompt."
            "The count key must be a number. Only explicitly set count if the user mentions it."
            "The text key should specify the coin type (e.g., memecoin, social coin, ai coin, etc.)."
            "The age_limit_days key should be included if the prompt specifies a time frame (e.g., less than 10 days old)."
            "Additionally, provide a suggestion to improve the query if needed."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            gpt_result = response.choices[0].message.content

            # Use regex to extract JSON and suggestion (if separate text is returned)
            json_match = re.search(r'\{.*\}', gpt_result, re.DOTALL)
            if json_match:
                gpt_json = json_match.group()
                query_params = json.loads(gpt_json)

                # Look for a suggestion (optional, if GPT includes one)
                suggestion_match = re.search(r'Suggestion:(.*)', gpt_result, re.DOTALL)
                suggestion = suggestion_match.group(1).strip() if suggestion_match else None

                # Log parsed parameters and suggestions
                self.context.logger.info(f"Parsed query parameters: {query_params}")
                if suggestion:
                    self.context.logger.info(f"Suggestion from GPT: {suggestion}")

                # Double-check the parsed parameters
                if "age_limit_days" in query_params and not isinstance(query_params["age_limit_days"], int):
                    self.context.logger.warning("The 'age_limit_days' parameter is not an integer. Please verify.")
                if "age_limit_days" not in query_params:
                    self.context.logger.info("No 'age_limit_days' specified. Results will include all dates.")

                return query_params, suggestion
            
        except json.JSONDecodeError as e:
            raise ValueError(f"GPT returned invalid JSON: {e}")
        
        except Exception as e:
            raise ValueError(f"Error parsing prompt with GPT: {e}")

    def handle_post_api_analyze(self, message: ApiHttpMessage, body):
        """Handle POST request for /api/analyze with parameter interaction."""
        body_dict = json.loads(body.decode("utf-8"))
        prompt = body_dict.get("query", "")
        wallet_address = body_dict.get("wallet_address", "")

        try:
            # Parse and confirm parameters
            self.context.logger.info(f"The prompt is: {prompt}")
            query_params, suggestion = self.parse_prompt_with_gpt(prompt)
            self.context.logger.info(f"Parameters after parsing: {query_params}")

            # Check if the wallet_address exists in the database
            existing_request = self.analyze_request_dao.get_by_wallet_address(wallet_address)

            if existing_request:
                # If wallet_address exists, update the query parameters
                self.context.logger.info(f"Updating existing request for wallet_address: {wallet_address}")
                updated_data = {
                    "count": query_params.get("count"),
                    "text": query_params.get("text"),
                    "engagement": query_params.get("engagement"),
                    "prompt": prompt
                }
                updated_request = self.analyze_request_dao.update(wallet_address, **updated_data)
                self.context.logger.info(f"Updated request: {updated_request}")
            else:
                # If wallet_address doesn't exist, insert a new request
                self.context.logger.info(f"Attempting to insert new request for wallet_address: {wallet_address}")
                new_data = {
                    "wallet_address": wallet_address,
                    "count": query_params.get("count"),
                    "text": query_params.get("text"),
                    "engagement": query_params.get("engagement"),
                    "prompt": prompt
                }
                inserted_request = self.analyze_request_dao.insert(new_data)
                self.context.logger.info(f"Inserted new request SUCCESSFULLY: {inserted_request}")

            # Make the API request to SearchCaster (external API)
            searchcaster_url = "https://searchcaster.xyz/api/search"
            response = requests.get(searchcaster_url, params=query_params)

            if response.status_code == 200:
                results = response.json()
                texts = []  # List to store all text values
                for cast in results.get("casts", []):
                    text = cast.get("body", {}).get("data", {}).get("text", "")
                    self.context.logger.info("NEW CAST TEXT")
                    self.context.logger.info(text)
                    if text:  # Only add non-empty text
                        texts.append(text)

                # Join all texts with commas
                combined_texts = ", ".join(texts)
                self.context.logger.info("Combined Texts:")
                self.context.logger.info(combined_texts)

                best_matching_ticker = self.extract_best_ticker_with_gpt(combined_texts, prompt)

                return ApiResponse(
                    headers={},
                    content=json.dumps({
                        "message": "Query processed successfully.",
                        "parameters": query_params,
                        "suggestion": suggestion,
                        "first_ticker": best_matching_ticker,
                        "results": results
                    }).encode("utf-8"),
                    status_code=200,
                    status_text="Success"
                )
            else:
                return ApiResponse(
                    headers={},
                    content=json.dumps({"error": response.text}).encode("utf-8"),
                    status_code=500,
                    status_text="SearchCaster API Error"
                )
        except Exception as e:
            self.context.logger.exception(f"Error handling analyze request: {e}")
            return ApiResponse(
                headers={},
                content=json.dumps({"error": str(e)}).encode("utf-8"),
                status_code=500,
                status_text="Internal Server Error"
            )

    def handle_get_api_user_by_wallet_address(self, message: ApiHttpMessage, wallet_address):
        """Handle GET request for /api/user/{walletAddress}."""
        self.context.logger.debug(f"Path parameters: wallet_address={wallet_address}")
        try:
            # Retrieve user data by wallet address from the DAO
            user_data = self.analyze_request_dao.get_by_wallet_address(wallet_address)

            if user_data:
                # If user data exists, return it as a JSON response
                response_body = json.dumps(user_data).encode("utf-8")
                return ApiHttpMessage(
                    performative=ApiHttpMessage.Performative.RESPONSE,
                    status_code=200,
                    status_text="Success",
                    headers="Content-Type: application/json",
                    version=message.version,
                    body=response_body
                )
            else:
                # If no user data found, return a 404 response
                error_message = {"error": f"User with wallet_address '{wallet_address}' not found."}
                return ApiHttpMessage(
                    performative=ApiHttpMessage.Performative.RESPONSE,
                    status_code=404,
                    status_text="Not Found",
                    headers="Content-Type: application/json",
                    version=message.version,
                    body=json.dumps(error_message).encode("utf-8")
                )

        except Exception as e:
            # Handle any unexpected errors and log the exception
            self.context.logger.exception(f"Error handling GET request for wallet_address={wallet_address}: {e}")
            return ApiHttpMessage(
                performative=ApiHttpMessage.Performative.RESPONSE,
                status_code=500,
                status_text="Internal Server Error",
                headers="Content-Type: application/json",
                version=message.version,
                body=json.dumps({"error": str(e)}).encode("utf-8")
            )
    def handle_get_api_wallet_by_wallet_address(self, message: ApiHttpMessage, wallet_address):
        """Handle GET request for /api/wallet/{walletAddress}"""
        self.context.logger.debug(f"Path parameters: wallet_address={wallet_address}")
        try:
            # Check if wallet address exists in the database
            wallet_data = self.analyze_request_dao.get_by_wallet_address(wallet_address)

            if not wallet_data:
                response_body = json.dumps({
                    "error": f"No wallet found for the provided address: {wallet_address}.",
                    "status_code": 404
                }).encode("utf-8")
                return ApiHttpMessage(
                    performative=ApiHttpMessage.Performative.RESPONSE,
                    status_code=404,
                    status_text="Not Found",
                    headers="Content-Type: application/json",
                    version=message.version,
                    body=response_body
                )
            # Extract query parameters from the wallet data
            query_params = {
                "count": wallet_data.get("count"),
                "text": wallet_data.get("text"),
                "engagement": wallet_data.get("engagement")
            }

            # Make the API request to SearchCaster
            searchcaster_url = "https://searchcaster.xyz/api/search"
            response = requests.get(searchcaster_url, params=query_params)

            if response.status_code == 200:
                results = response.json()
                texts = []  # List to store all text values
                for cast in results.get("casts", []):
                    text = cast.get("body", {}).get("data", {}).get("text", "")
                    self.context.logger.info("NEW CAST TEXT")
                    self.context.logger.info(text)
                    if text:  # Only add non-empty text
                        texts.append(text)

                # Join all texts with commas
                combined_texts = ", ".join(texts)
                self.context.logger.info("Combined Texts:")
                self.context.logger.info(combined_texts)

                best_matching_ticker = self.extract_best_ticker_with_gpt(combined_texts, wallet_data.get("prompt"))

                response_body = json.dumps({
                    "status": "success",
                    "parameters": query_params,
                    "first_ticker": best_matching_ticker,
                }).encode("utf-8")
                return ApiHttpMessage(
                    performative=ApiHttpMessage.Performative.RESPONSE,
                    status_code=200,
                    status_text="Success",
                    headers="Content-Type: application/json",
                    version=message.version,
                    body=response_body
                )
            else:
                response_body = json.dumps({
                    "error": f"SearchCaster API error: {response.text}",
                    "status_code": response.status_code
                }).encode("utf-8")
                return ApiHttpMessage(
                    performative=ApiHttpMessage.Performative.RESPONSE,
                    status_code=500,
                    status_text="SearchCaster API Error",
                    headers="Content-Type: application/json",
                    version=message.version,
                    body=response_body
                )

        except Exception as e:
            self.context.logger.exception(f"Error handling GET request for wallet_address={wallet_address}: {e}")
            response_body = json.dumps({"error": str(e)}).encode("utf-8")
            return ApiHttpMessage(
                performative=ApiHttpMessage.Performative.RESPONSE,
                status_code=500,
                status_text="Internal Server Error",
                headers="Content-Type: application/json",
                version=message.version,
                body=response_body
            )