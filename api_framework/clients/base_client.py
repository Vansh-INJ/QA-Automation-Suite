import requests
import time

from utils.api_context import (
    API_CONTEXT
)

# Keys that should never be written to the Excel log in plaintext.
# Add to this set if your payloads/headers carry other secrets.
SENSITIVE_KEYS = {"password", "authorization", "token", "access_token"}


def _redact(data):
    """
    Returns a redacted COPY of a dict for LOGGING purposes only.
    The original dict (with real values) is still what's actually sent
    on the request - this only affects what gets written to Excel.
    """
    if not isinstance(data, dict):
        return data

    redacted = {}

    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = value

    return redacted


class BaseClient:

    def __init__(
            self,
            base_url,
            headers=None
    ):
        self.base_url = (
            base_url.rstrip("/")
        )

        self.headers = (
            headers or {}
        )

    def _track(
            self,
            method,
            endpoint,
            payload,
            response,
            duration
    ):
        API_CONTEXT.clear()

        API_CONTEXT.update({
            "method":
                method,

            "endpoint":
                endpoint,

            "payload":
                _redact(payload),

            "headers":
                _redact(self.headers),

            "response":
                response,

            "duration":
                duration,
        })

    def get(
            self,
            endpoint,
            params=None
    ):
        start = time.time()

        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            params=params
        )

        duration = round(
            (
                time.time()
                - start
            ) * 1000,
            2
        )

        self._track(
            "GET",
            endpoint,
            params,
            response,
            duration
        )

        return response

    def post(
            self,
            endpoint,
            payload=None
    ):
        start = time.time()

        response = requests.post(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=payload
        )

        duration = round(
            (
                time.time()
                - start
            ) * 1000,
            2
        )

        self._track(
            "POST",
            endpoint,
            payload,
            response,
            duration
        )

        return response

    def put(
            self,
            endpoint,
            payload=None
    ):
        start = time.time()

        response = requests.put(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=payload
        )

        duration = round(
            (
                time.time()
                - start
            ) * 1000,
            2
        )

        self._track(
            "PUT",
            endpoint,
            payload,
            response,
            duration
        )

        return response

    def delete(
            self,
            endpoint
    ):
        start = time.time()

        response = requests.delete(
            f"{self.base_url}{endpoint}",
            headers=self.headers
        )

        duration = round(
            (
                time.time()
                - start
            ) * 1000,
            2
        )

        self._track(
            "DELETE",
            endpoint,
            None,
            response,
            duration
        )

        return response