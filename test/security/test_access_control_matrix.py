"""
test/security/test_access_control_matrix.py

CORRECTED: security_client.request() returns (resp, elapsed_ms, url, headers)
-- matches the real health_client pattern in test/health/conftest.py.
"""

import pytest

from api_framework.security.core.access_control.access_matrix import ACCESS_MATRIX
from api_framework.security.core.access_control.idor_engine import evaluate_access_attempt
from api_framework.security.core.access_control.access_reporter import AccessControlReporter

reporter = AccessControlReporter()


@pytest.fixture(scope="session", autouse=True)
def write_access_control_report_at_end():
    yield
    reporter.write_excel()
    reporter.write_summary_json()


def resolve_resource_id(case, security_client):
    if not case.resource_id_param:
        return None
    return security_client.resolve_owned_resource_id(
        owner_profile=case.resource_owner_profile,
        param_name=case.resource_id_param,
    )


def _build_path(case, resource_id):
    if case.resource_id_param and resource_id:
        return case.endpoint.format(**{case.resource_id_param: resource_id})
    return case.endpoint


@pytest.mark.parametrize("case", ACCESS_MATRIX, ids=[c.name for c in ACCESS_MATRIX])
def test_access_matrix_denied_profiles(case, security_client):
    resource_id = resolve_resource_id(case, security_client)
    path = _build_path(case, resource_id)

    for profile in case.denied_profiles:
        resp, elapsed_ms, url, headers = security_client.request(
            method=case.method, path=path, auth_profile=profile
        )

        result = evaluate_access_attempt(
            endpoint=path,
            method=case.method,
            acting_profile=profile,
            status_code=resp.status_code,
            response_text=resp.text,
            should_have_access=False,
            target_owner_profile=case.resource_owner_profile,
            resource_id=resource_id,
            vulnerability_type=case.vulnerability_type,
            duration_ms=elapsed_ms,
        )
        reporter.record(result)

        assert result.result == "PASS", (
            f"[{case.name}] profile '{profile}' should be denied on {case.method} {path} "
            f"but got status {resp.status_code}. {result.message}"
        )


@pytest.mark.parametrize("case", ACCESS_MATRIX, ids=[c.name for c in ACCESS_MATRIX])
def test_access_matrix_allowed_profiles(case, security_client):
    resource_id = resolve_resource_id(case, security_client)
    path = _build_path(case, resource_id)

    for profile in case.allowed_profiles:
        resp, elapsed_ms, url, headers = security_client.request(
            method=case.method, path=path, auth_profile=profile
        )

        result = evaluate_access_attempt(
            endpoint=path,
            method=case.method,
            acting_profile=profile,
            status_code=resp.status_code,
            response_text=resp.text,
            should_have_access=True,
            target_owner_profile=case.resource_owner_profile,
            resource_id=resource_id,
            vulnerability_type=case.vulnerability_type,
            duration_ms=elapsed_ms,
        )
        reporter.record(result)

        assert result.result == "PASS", (
            f"[{case.name}] profile '{profile}' should have access on {case.method} {path} "
            f"but got status {resp.status_code}. {result.message}"
        )