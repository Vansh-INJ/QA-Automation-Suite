"""
Fixtures scoped to test/health/*.

v5: SMTP mailer call REMOVED from teardown (org blocks SMTP ports —
notification is now n8n's job, triggered externally via trigger_server.py).
Added write_summary_json() call so results are available as structured
JSON, not just the Excel file.
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
from utils.health_failure_logger import HealthFailureLogger
from utils.health_n8n_notifier import notify_n8n
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
    summary_path = reporter.write_summary_json()
    print(f"\n[health-suite] Report written to: {report_path}")
    print(f"[health-suite] Summary JSON written to: {summary_path}")

    summary = reporter.summary
    print(
        f"[health-suite] {summary['passed']}/{summary['total']} passed "
        f"({summary['pass_rate']}%)"
    )
    if summary["critical_failed"]:
        print(f"[health-suite] CRITICAL FAILURES: {summary['critical_failed']}")
    if summary["sla_breaches"]:
        print(f"[health-suite] SLA BREACHES: {summary['sla_breaches']}")

    # PUSH MODEL (recommended): this suite calls OUT to an n8n Webhook
    # with the results — no inbound port/firewall rule needed on this
    # machine. n8n receives the payload and handles email/Slack itself,
    # via channels that survive the org's SMTP port block (Graph API /
    # OAuth-based mail sending, or n8n's own approved connector).
    # No-op unless N8N_WEBHOOK_ENABLED=true is set in .env.
    notify_n8n(summary=summary, report_path=report_path)


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
                method=method, url=url, params=params, headers=headers,
                json=json_body, timeout=20,
            )
            elapsed_ms = round((time.time() - start) * 1000, 1)
            return resp, elapsed_ms, url, headers

    return HealthClient()
