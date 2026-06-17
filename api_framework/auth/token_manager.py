import time

from api_framework.clients.auth_client import (
    AuthClient
)

from api_framework.config.settings import (
    Settings
)


class TokenManager:

    _token = None
    _expires_at = 0

    @classmethod
    def get_token(cls):

        now = time.time()

        if (
                cls._token and
                now < cls._expires_at
        ):
            return cls._token

        client = AuthClient(
            base_url=
            Settings.BASE_URL
        )

        response = client.login(
            username=
            Settings.API_USERNAME,
            password=
            Settings.API_PASSWORD
        )

        assert (
            response.status_code == 200
        ), (
            f"Login Failed:\n"
            f"{response.text}"
        )

        body = response.json()

        cls._token = (
            body["data"]
            ["access_token"]
        )

        expires_in = (
            body["data"]
            ["expires_in"]
        )

        cls._expires_at = (
            time.time()
            + expires_in
            - 30
        )

        print(
            "\n[API LOGIN SUCCESS]"
            f"\nUser: {Settings.API_USERNAME}"
        )

        return cls._token

    @classmethod
    def get_headers(cls):

        token = cls.get_token()

        return {
            "Authorization":
                f"Bearer {token}",

            "Content-Type":
                "application/json"
        }