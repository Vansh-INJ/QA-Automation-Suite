"""
Fixtures scoped to test/health/*.

v3: no structural change here vs v2 — health_client still returns
(resp, elapsed_ms, url, headers). The new reporter columns are populated
in test_api_health.py, which now has access to everything it needs
(request payload, response body, user identity from the token manager).
"""

import os
import time
import pytest
import requests

from api_framework.config.health_endpoints import AUTH_PROFILES
from api_framework.auth.health_token_manager import (
    HealthTokenManager,
    resolve_credentials,
    HealthAuthError,
)
from utils.health_reporter import HealthReporter
from utils.health_notifier import notify_if_failed
from utils.health_failure_logger import HealthFailureLogger
from utils.health_mailer import send_health_report_email
from utils.run_manager import get_run_folder


@pytest.fixture(scope="session")
def base_url() -> str:
    url = os.getenv("BASE_URL", "https://injin-dev.injtechnologies.com")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def health_run_folder():
    return get_run_folder()


@pytest.fixture(scope="session")
def failure_logger(health_run_folder):
    return HealthFailureLogger(health_run_folder)


@pytest.fixture(scope="session")
def health_reporter(health_run_folder):
    reporter = HealthReporter(health_run_folder)
    yield reporter
    report_path = reporter.write_excel()
    print(f"\n[health-suite] Report written to: {report_path}")

    summary = reporter.summary
    print(
        f"[health-suite] {summary['passed']}/{summary['total']} passed "
        f"({summary['pass_rate']}%)"
    )
    if summary["critical_failed"]:
        print(f"[health-suite] CRITICAL FAILURES: {summary['critical_failed']}")
    if summary["sla_breaches"]:
        print(f"[health-suite] SLA BREACHES: {summary['sla_breaches']}")

    notify_if_failed(summary, report_path=report_path)
    send_health_report_email(summary=summary, report_path=report_path)


@pytest.fixture(scope="session")
def token_managers(base_url):
    managers = {}
    for profile_name in AUTH_PROFILES:
        managers[profile_name] = HealthTokenManager(base_url)
    return managers


@pytest.fixture(scope="session")
def health_client(base_url, token_managers):
    class HealthClient:
        def request(self, method: str, path: str, params: dict = None,
                    auth_profile: str = None, json_body: dict = None):
            url = f"{base_url}{path}"
            headers = {}

            if auth_profile:
                profile_cfg = AUTH_PROFILES[auth_profile]
                username, password = resolve_credentials(profile_cfg)
                manager = token_managers[auth_profile]
                headers = manager.get_headers(username, password)

            start = time.time()
            resp = requests.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                json=json_body,
                timeout=20,
            )
            elapsed_ms = round((time.time() - start) * 1000, 1)
            return resp, elapsed_ms, url, headers

    return HealthClient()
