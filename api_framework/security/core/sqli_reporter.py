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

    result, message = classify_sqli_result(
        status=status,
        leaked=leaked,
        field_name=field_name,
        payload_used=payload,
        response_text=response_text,
    )

    elapsed_display = (
        f"{elapsed:.3f}s"
        if elapsed is not None
        else "n/a"
    )

    print(
        f"[SECURITY EVIDENCE] {category} | "
        f"field={field_name} | "
        f"payload={payload!r} | "
        f"status={status} | "
        f"resp_len={len(response_text)} | "
        f"elapsed={elapsed_display} | "
        f"sql_error_leak="
        f"{leaked if leaked else 'none'} | "
        f"result={result} | "
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
        api_message=message,
    )

    return result, message