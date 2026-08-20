"""
HealthTokenManager — a minimal, self-contained auth helper for the
API Health Suite.

Why a separate manager instead of reusing api_framework/auth/token_manager.py
directly?
    - The health suite must be resilient to auth ITSELF being broken (that's
      one of the things it's monitoring). It should not silently reuse a
      cached/stale token from another part of the framework.
    - Keeps the health suite dependency-light and easy to run in isolation
      (e.g. in CI) without pulling in unrelated framework state.

If your existing TokenManager already does exactly this, you can swap this
out for it later — the health tests only depend on `get_access_token()`
returning a valid bearer token string (or raising, on failure).
"""

import os
import time
import requests


class HealthAuthError(Exception):
    """Raised when the login call itself fails or returns an unexpected shape."""
    pass


class HealthTokenManager:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._token = None
        self._expires_at = 0
        self._user_info = None
        self._last_login_response = None  # kept for reporting on failure

    def _login(self, username: str, password: str):
        url = f"{self.base_url}/api/auth/login"
        payload = {"username": username, "password": password}

        start = time.time()
        resp = requests.post(url, json=payload, timeout=15)
        elapsed_ms = round((time.time() - start) * 1000, 1)

        self._last_login_response = {
            "status_code": resp.status_code,
            "elapsed_ms": elapsed_ms,
            "body_snippet": resp.text[:500],
        }

        if resp.status_code != 200:
            raise HealthAuthError(
                f"Login failed with status {resp.status_code}: {resp.text[:300]}"
            )

        body = resp.json()
        if body.get("status") != "success" or "data" not in body:
            raise HealthAuthError(f"Login returned unexpected payload shape: {body}")

        data = body["data"]
        token = data.get("access_token")
        expires_in = data.get("expires_in", 900)  # seconds; 900 = 15 min, per observed response
        user = data.get("user", {})

        if not token:
            raise HealthAuthError(f"Login response missing access_token: {body}")

        self._token = token
        # Refresh 30s before actual expiry to avoid edge-of-window failures
        self._expires_at = time.time() + max(expires_in - 30, 0)
        self._user_info = user

        return resp

    def get_access_token(self, username: str, password: str, force_refresh: bool = False) -> str:
        """
        Returns a valid bearer token, logging in (or re-logging in) as needed.
        Given the 15-min TTL observed on this API, a health run should treat
        tokens as effectively single-use per run rather than caching long-term.
        """
        if force_refresh or self._token is None or time.time() >= self._expires_at:
            self._login(username, password)
        return self._token

    def get_headers(self, username: str, password: str) -> dict:
        token = self.get_access_token(username, password)
        return {"Authorization": f"Bearer {token}"}

    @property
    def user_info(self) -> dict:
        return self._user_info or {}

    @property
    def last_login_response(self) -> dict:
        return self._last_login_response or {}


def resolve_credentials(auth_profile: dict) -> tuple[str, str]:
    """
    Pulls username/password from env vars named in the profile config.
    Keeps credentials out of source entirely — set these in .env locally
    or as CI secrets (e.g. GitHub Actions repo secrets).
    """
    username = os.getenv(auth_profile["username_env"])
    password = os.getenv(auth_profile["password_env"])

    missing = [
        name for name, val in [
            (auth_profile["username_env"], username),
            (auth_profile["password_env"], password),
        ] if not val
    ]
    if missing:
        raise HealthAuthError(
            f"Missing required environment variable(s) for health auth: {missing}. "
            f"Set them in .env (local) or as CI secrets."
        )

    return username, password
