"""
SQL Injection evidence reporting.

Responsible for collecting SQL injection test evidence,
classifying the result, and writing the security result
to the centralized test report.
"""

from api_framework.utils.security_common import classify_sqli_result
from utils.helpers import write_sql_injection_result


from api_framework.security.core.sqli_analyzer import (
    extract_response_status,
    extract_response_text,
    analyze_sql_errors,
)

from api_framework.security.core.sqli_engine import (
    find_version_string_leaks,
)


# ============================================================================
# SEVERITY RATING
# ============================================================================

def _compute_severity(
    result: str,
    status_code,
    leaked: list,
    version_leaks: list,
) -> str:
    """
    Map result + evidence to a severity level for the report.

    CRITICAL : SQL/DB error or version string leaked
    HIGH     : Server error (500) with malicious input, or 2xx accepted
    MEDIUM   : Unexpected status code / inconclusive
    LOW      : Safely rejected (4xx) without any leakage
    INFO     : Informational — zero-delay or safe probe passed
    """

    if leaked or version_leaks:
        return "CRITICAL"

    if result == "FAIL":
        if status_code and 200 <= status_code < 300:
            return "HIGH"
        if status_code and status_code >= 500:
            return "HIGH"
        return "MEDIUM"

    if result == "BLOCKED":
        return "MEDIUM"

    # PASS
    if status_code in (400, 401, 403, 404, 409, 422):
        return "LOW"

    return "INFO"


# ============================================================================
# EVIDENCE LOGGER
# ============================================================================

def log_sqli_evidence(
    category: str,
    field_name: str,
    payload,
    response,
    elapsed=None,
):
    """
    Collect SQL injection evidence and persist the authoritative result.

    Args:
        category:
            SQL injection attack category.

        field_name:
            Field being tested.

        payload:
            Malicious payload used.

        response:
            HTTP response object.

        elapsed:
            Optional request duration in seconds.

    Returns:
        tuple:
            (result, message)
    """

    status = extract_response_status(
        response
    )

    response_text = extract_response_text(
        response
    )

    leaked = analyze_sql_errors(
        response
    )

    version_leaks = find_version_string_leaks(
        response_text
    )

    result, message = classify_sqli_result(
        status=status,
        leaked=leaked,
        field_name=field_name,
        payload_used=payload,
        response_text=response_text,
    )

    severity = _compute_severity(
        result=result,
        status_code=status,
        leaked=leaked,
        version_leaks=version_leaks,
    )

    elapsed_display = (
        f"{elapsed:.3f}s"
        if elapsed is not None
        else "n/a"
    )

    all_leaks = leaked + version_leaks

    print(
        f"[SECURITY EVIDENCE] {category} | "
        f"field={field_name} | "
        f"payload={payload!r} | "
        f"status={status} | "
        f"resp_len={len(response_text)} | "
        f"elapsed={elapsed_display} | "
        f"sql_error_leak="
        f"{all_leaks if all_leaks else 'none'} | "
        f"result={result} | "
        f"severity={severity} | "
        f"verdict={message}"
    )

    write_sql_injection_result(
        field=field_name,
        payload=payload,
        payload_type=category,
        actual_status=status,
        response_body=response_text,
        duration_ms=(
            elapsed * 1000
            if elapsed is not None
            else None
        ),
        result=result,
        api_message=(
            f"[{severity}] {message}"
        ),
    )

    return result, message