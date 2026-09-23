"""
test/security/conftest.py

Reuses base_url, token_managers, health_client exactly as built in
test/health/conftest.py -- no new auth plumbing, just a resolver helper
for owned-resource IDs used by the access control matrix.

IMPORTANT: health_client.request() returns a TUPLE:
    (resp, elapsed_ms, url, headers)
not a bare response object. test_access_control_matrix.py must unpack it
accordingly -- see the corrected version below.
"""

import pytest

from api_framework.config.health_endpoints import AUTH_PROFILES, RESOLVER_CONFIG
from api_framework.auth.health_token_manager import HealthTokenManager, resolve_credentials
from utils.health_id_resolver import HealthIdResolver


@pytest.fixture(scope="session")
def base_url():
    import os
    return os.getenv("HEALTH_BASE_URL", "https://injin-dev.injtechnologies.com").rstrip("/")


@pytest.fixture(scope="session")
def token_managers(base_url):
    # Reuses the SAME AUTH_PROFILES dict -- once you add employee_a/employee_b
    # to AUTH_PROFILES in health_endpoints.py, they're automatically available
    # here too, no duplication needed.
    return {name: HealthTokenManager(base_url) for name in AUTH_PROFILES}


@pytest.fixture(scope="session")
def security_client(base_url, token_managers):
    """
    Same shape as health_client, reused as-is so both suites share one
    mental model. request() returns (resp, elapsed_ms, url, headers).
    """
    import time
    import requests

    class SecurityClient:
        def request(self, method, path, params=None, auth_profile=None, json_body=None):
            url = f"{base_url}{path}"
            headers = {}

            if auth_profile:
                profile_cfg = AUTH_PROFILES[auth_profile]
                username, password = resolve_credentials(profile_cfg)
                manager = token_managers[auth_profile]
                headers = manager.get_headers(username, password)

            start = time.time()
            resp = requests.request(
                method=method, url=url, params=params,
                headers=headers, json=json_body, timeout=20,
            )
            elapsed_ms = round((time.time() - start) * 1000, 1)
            return resp, elapsed_ms, url, headers

        def resolve_owned_resource_id(self, owner_profile, param_name):
            """
            Resolves a real ID owned by `owner_profile`, reusing your existing
            HealthIdResolver + RESOLVER_CONFIG where a matching entry exists
            (e.g. payslip_uuid, employee_uuid, role_uuid-equivalents).

            NOTE: HealthIdResolver as currently used in health suite resolves
            IDs generically (first record from a list), not "owned by a
            specific profile". For true per-owner resolution (e.g. "the
            payslip belonging specifically to employee_a"), you likely need
            to call the list endpoint AS that profile and extract from ITS
            own response, rather than a shared/generic resolver call. This
            is the one piece of custom wiring the matrix genuinely needs --
            flagging rather than guessing your data model here.
            """
            resolver = HealthIdResolver(self, RESOLVER_CONFIG)
            if param_name in RESOLVER_CONFIG:
                return resolver.resolve(param_name)
            return None

    return SecurityClient()