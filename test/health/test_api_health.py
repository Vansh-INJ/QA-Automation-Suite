"""
Daily API Health Suite — v7.

New in this version: entries can use "path_template" + "resolve_vars"
instead of a static "path". These get their real IDs filled in at runtime
via id_resolver (see utils/health_id_resolver.py) before the request is
made. If ID resolution itself fails, that's reported as this endpoint's
failure reason — clearly distinguished from the endpoint itself being down.
"""

import pytest

from api_framework.config.health_endpoints import ENDPOINTS, DEFAULT_SLA_MS
from api_framework.auth.health_token_manager import HealthAuthError
from utils.health_id_resolver import IdResolutionError


@pytest.mark.parametrize("endpoint", ENDPOINTS, ids=[e["name"] for e in ENDPOINTS])
def test_endpoint_health(endpoint, health_client, health_reporter, failure_logger,
                          token_managers, id_resolver, base_url):
    name = endpoint["name"]
    action = endpoint.get("action", name)
    method = endpoint["method"]
    expected_status = endpoint["expected_status"]
    critical = endpoint.get("critical", False)
    sla_ms = endpoint.get("sla_ms", DEFAULT_SLA_MS)

    manager = token_managers.get("employee")
    candidate_name = manager.user_info.get("name", "") if manager else ""
    candidate_email = manager.user_info.get("email", "") if manager else ""

    # --- Login is a special case ---
    if endpoint.get("is_login"):
        from api_framework.config.health_endpoints import AUTH_PROFILES
        from api_framework.auth.health_token_manager import resolve_credentials

        path = endpoint["path"]
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
            candidate_name = manager.user_info.get("name", "")
            candidate_email = manager.user_info.get("email", "")
        except HealthAuthError as e:
            error_msg = str(e)
            api_message = "Login raised an exception"
            status_code = manager.last_login_response.get("status_code")
            elapsed_ms = manager.last_login_response.get("elapsed_ms")
            response_body = manager.last_login_response.get("body_snippet")

        health_reporter.record(
            name=name, action=action, method=method, path=path, params=None,
            status_code=status_code, expected_status=expected_status,
            passed=passed, elapsed_ms=elapsed_ms, sla_ms=sla_ms,
            api_message=api_message,
            request_headers={"Content-Type": "application/json"},
            request_payload=request_payload, response_body=response_body,
            candidate_name=candidate_name, candidate_email=candidate_email,
            error=error_msg, critical=critical,
        )
        assert passed, error_msg or f"Login check failed (status={status_code})"
        return

    # --- Resolve path_template -> real path, if needed ---
    if "path_template" in endpoint:
        resolve_vars = endpoint.get("resolve_vars", [])
        try:
            resolved = id_resolver.resolve_all(resolve_vars)
            path = endpoint["path_template"].format(**resolved)
        except IdResolutionError as e:
            # ID resolution failed — report THIS as the failure reason,
            # clearly distinct from "the endpoint itself returned an error".
            error_msg = f"ID resolution failed: {e}"
            health_reporter.record(
                name=name, action=action, method=method,
                path=endpoint["path_template"], params=None,
                status_code=None, expected_status=expected_status,
                passed=False, elapsed_ms=None, sla_ms=sla_ms,
                api_message="Could not resolve required path variable(s)",
                request_headers={}, request_payload={}, response_body="",
                candidate_name=candidate_name, candidate_email=candidate_email,
                error=error_msg, critical=critical,
            )
            failure_logger.log_failure(
                name=name, method=method, url=f"{base_url}{endpoint['path_template']}",
                request_params={}, request_headers={}, status_code=0,
                response_headers={}, response_body="", error=error_msg,
            )
            pytest.fail(error_msg)
    else:
        path = endpoint["path"]

    params = endpoint["params"]() if "params" in endpoint else None

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
        api_message=api_message, request_headers=req_headers,
        request_payload=params or {}, response_body=response_body,
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
