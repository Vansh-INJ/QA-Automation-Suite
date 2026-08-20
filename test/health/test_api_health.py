"""
Daily API Health Suite — v3.

Feeds the full reporting column set (identity, SLA, payload, response body,
etc.) into HealthReporter.record() for every endpoint, using real data
captured from the actual request/response — nothing fabricated.
"""

import pytest

from api_framework.config.health_endpoints import ENDPOINTS, DEFAULT_SLA_MS
from api_framework.auth.health_token_manager import HealthAuthError


@pytest.mark.parametrize("endpoint", ENDPOINTS, ids=[e["name"] for e in ENDPOINTS])
def test_endpoint_health(endpoint, health_client, health_reporter, failure_logger,
                          token_managers, base_url):
    name = endpoint["name"]
    action = endpoint.get("action", name)
    method = endpoint["method"]
    path = endpoint["path"]
    expected_status = endpoint["expected_status"]
    critical = endpoint.get("critical", False)
    sla_ms = endpoint.get("sla_ms", DEFAULT_SLA_MS)
    params = endpoint["params"]() if "params" in endpoint else None

    manager = token_managers.get("employee")
    # Identity the check runs as — populated from the login response's
    # `user` block once login has happened at least once this session.
    candidate_name = manager.user_info.get("name", "") if manager else ""
    candidate_email = manager.user_info.get("email", "") if manager else ""

    # --- Login is a special case: it validates auth itself ---
    if endpoint.get("is_login"):
        from api_framework.config.health_endpoints import AUTH_PROFILES
        from api_framework.auth.health_token_manager import resolve_credentials

        profile_cfg = AUTH_PROFILES["employee"]
        username, password = resolve_credentials(profile_cfg)

        request_payload = {"username": username, "password": "***MASKED***"}
        error_msg = ""
        passed = False
        status_code = None
        elapsed_ms = None
        api_message = ""
        response_body = None

        try:
            manager.get_access_token(username, password, force_refresh=True)
            status_code = manager.last_login_response.get("status_code")
            elapsed_ms = manager.last_login_response.get("elapsed_ms")
            passed = status_code == expected_status
            api_message = "Login successful" if passed else "Login failed"
            response_body = manager.last_login_response.get("body_snippet")
            # Now that login succeeded, backfill identity for this row too
            candidate_name = manager.user_info.get("name", "")
            candidate_email = manager.user_info.get("email", "")
        except HealthAuthError as e:
            error_msg = str(e)
            api_message = "Login raised an exception"
            status_code = manager.last_login_response.get("status_code")
            elapsed_ms = manager.last_login_response.get("elapsed_ms")
            response_body = manager.last_login_response.get("body_snippet")

        health_reporter.record(
            name=name, action=action, method=method, path=path, params=params,
            status_code=status_code, expected_status=expected_status,
            passed=passed, elapsed_ms=elapsed_ms, sla_ms=sla_ms,
            api_message=api_message,
            request_headers={"Content-Type": "application/json"},
            request_payload=request_payload,
            response_body=response_body,
            candidate_name=candidate_name, candidate_email=candidate_email,
            error=error_msg, critical=critical,
        )

        if not passed:
            failure_logger.log_failure(
                name=name, method=method, url=f"{base_url}{path}",
                request_params={}, request_headers={"Content-Type": "application/json"},
                status_code=status_code or 0, response_headers={},
                response_body=response_body or "", error=error_msg,
            )

        assert passed, error_msg or f"Login check failed (status={status_code})"
        return

    # --- Standard endpoint check ---
    error_msg = ""
    passed = False
    status_code = None
    elapsed_ms = None
    resp = None
    req_url = f"{base_url}{path}"
    req_headers = {}
    api_message = ""
    response_body = None

    try:
        resp, elapsed_ms, req_url, req_headers = health_client.request(
            method=method, path=path, params=params,
            auth_profile=endpoint.get("auth_profile"),
        )
        status_code = resp.status_code
        passed = status_code == expected_status
        response_body = resp.text

        if passed:
            api_message = "OK"
        else:
            # Try to surface the server's own message field if present
            try:
                body_json = resp.json()
                api_message = body_json.get("message", f"Unexpected status {status_code}")
            except Exception:
                api_message = f"Unexpected status {status_code}"
            error_msg = f"Expected {expected_status}, got {status_code}: {resp.text[:300]}"

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        api_message = "Request exception (network/timeout/connection)"

    health_reporter.record(
        name=name, action=action, method=method, path=path, params=params,
        status_code=status_code, expected_status=expected_status,
        passed=passed, elapsed_ms=elapsed_ms, sla_ms=sla_ms,
        api_message=api_message,
        request_headers=req_headers,
        request_payload=params or {},   # GET requests: query params doubles as the "payload" shown
        response_body=response_body,
        candidate_name=candidate_name, candidate_email=candidate_email,
        error=error_msg, critical=critical,
    )

    if not passed:
        failure_logger.log_failure(
            name=name, method=method, url=req_url,
            request_params=params or {}, request_headers=req_headers,
            status_code=status_code or 0,
            response_headers=dict(resp.headers) if resp is not None else {},
            response_body=response_body or "", error=error_msg,
        )

    assert passed, error_msg
