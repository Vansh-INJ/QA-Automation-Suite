from api_framework.clients.base_client import (
    BaseClient
)


class AuthClient(BaseClient):

    def login(
            self,
            username,
            password
    ):
        payload = {
            "username": username,
            "password": password,
            "rememberMe": False
        }

        return self.post(
            "/api/auth/login",
            payload
        )