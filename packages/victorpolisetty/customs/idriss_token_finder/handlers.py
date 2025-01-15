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
import os
import requests
import json
from openai import OpenAI
from dataclasses import dataclass
from urllib.parse import unquote, urlparse
from aea.skills.base import Handler
from packages.eightballer.protocols.http.message import HttpMessage as ApiHttpMessage
from mech_client.interact import interact, ConfirmationType
from datetime import datetime, timedelta, timezone
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
        self.analyze_request_dao = AnalyzeRequestDAO()  # Initialize the DAO to interact with the database



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
        
    def filter_and_sort_by_age(self, posts, max_age_days):
        """Filter and sort posts by their age in days."""
        if not max_age_days:
            return posts  # No filtering if max_age_days is not provided

        # Calculate the cutoff timestamp
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        cutoff_timestamp = int(cutoff_date.timestamp() * 1000)  # Convert to milliseconds

        # Filter posts based on age
        filtered_posts = [
            post for post in posts
            if post["body"]["publishedAt"] >= cutoff_timestamp
        ]

        # Optionally sort the filtered posts by published date
        sorted_posts = sorted(
            filtered_posts,
            key=lambda post: post["body"]["publishedAt"],
            reverse=True  # Latest posts first
        )

        return sorted_posts
    
    def extract_first_ticker(self, casts):
        """Extract the first ticker (symbol) from the casts."""
        ticker_pattern = r'\$[A-Za-z0-9]+'  # Regex pattern to find tickers like $SOCIAL
        for cast in casts:
            text = cast.get("body", {}).get("data", {}).get("text", "")
            match = re.search(ticker_pattern, text)
            if match:
                return match.group()  # Return the first match
        return None

        
    def parse_prompt_with_gpt(self, prompt: str) -> dict:
        """Parse a natural language prompt using GPT and double-check parameters."""
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # GPT-4 system prompt to guide its output
        system_prompt = (
            "You are an assistant that translates natural language prompts into API query parameters. "
            "Parse the input prompt and return a JSON object with keys: text, engagement, count, username, and age_limit_days. "
            "The engagement key must be one of: reactions, recasts, replies, watches. "
            "The count key must be a number. Only explicitly set count if the user mentions it. "
            "The text key should specify the coin type (e.g., memecoin, social coin, etc.). "
            "The age_limit_days key should be included if the prompt specifies a time frame (e.g., less than 10 days old). "
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
                    "text": prompt,
                    "engagement": query_params.get("engagement"),
                }
                updated_request = self.analyze_request_dao.update(wallet_address, **updated_data)
                self.context.logger.info(f"Updated request: {updated_request}")
            else:
                # If wallet_address doesn't exist, insert a new request
                self.context.logger.info(f"Inserting new request for wallet_address: {wallet_address}")
                new_data = {
                    "wallet_address": wallet_address,
                    "count": query_params.get("count"),
                    "text": prompt,
                    "engagement": query_params.get("engagement"),
                }
                inserted_request = self.analyze_request_dao.insert(new_data)
                self.context.logger.info(f"Inserted new request: {inserted_request}")

            # Make the API request to SearchCaster (external API)
            searchcaster_url = "https://searchcaster.xyz/api/search"
            response = requests.get(searchcaster_url, params=query_params)

            if response.status_code == 200:
                results = response.json()

                # Extract the first ticker from the results
                first_ticker = self.extract_first_ticker(results.get("casts", []))

                max_age_days = query_params.get("age_limit_days")
                if max_age_days:
                    results["casts"] = self.filter_and_sort_by_age(results["casts"], max_age_days)

                return ApiResponse(
                    headers={},
                    content=json.dumps({
                        "message": "Query processed successfully.",
                        "parameters": query_params,
                        "suggestion": suggestion,
                        "first_ticker": first_ticker,
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