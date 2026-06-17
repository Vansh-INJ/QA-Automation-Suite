import requests
import time

from utils.api_context import (
    API_CONTEXT
)

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

    def get(
            self,
            endpoint,
            params=None
    ):
        return requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            params=params
        )

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

        API_CONTEXT.clear()

        API_CONTEXT.update({
            "method":
                "POST",

            "endpoint":
                endpoint,

            "payload":
                payload,

            "response":
                response,

            "duration":
                duration
        })

        return response

    def put(
            self,
            endpoint,
            payload=None
    ):
        return requests.put(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            json=payload
        )

    def delete(
            self,
            endpoint
    ):
        return requests.delete(
            f"{self.base_url}{endpoint}",
            headers=self.headers
        ) 