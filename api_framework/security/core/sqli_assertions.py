"""
SQL Injection assertion utilities.

Responsible for converting SQL injection security classifications
into pytest test outcomes.

PASS    -> Test continues successfully
FAIL    -> Test fails
BLOCKED -> Test is skipped as inconclusive
"""

from api_framework.utils.security_common import classify_sqli_result
import pytest



from api_framework.security.core.sqli_analyzer import (
    extract_response_status,
    extract_response_text,
    analyze_sql_errors,
)


def assert_sqli_safe(
    response,
    payload_used,
    field_name: str,
):
    """
    Evaluate a SQL injection response and convert the security verdict
    into the appropriate pytest outcome.

    FAIL:
        A potential SQL injection vulnerability or unsafe server
        behavior was detected.

    BLOCKED:
        The test could not conclusively evaluate the payload because
        an unrelated application prerequisite prevented evaluation.

    PASS:
        The payload was safely rejected without SQL/database leakage.
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
        payload_used=payload_used,
        response_text=response_text,
    )

    print(
        "\n[SQLI ASSERTION]\n"
        f"Field     : {field_name}\n"
        f"Payload   : {payload_used!r}\n"
        f"Status    : {status}\n"
        f"Response  : {response_text[:2000]!r}\n"
        f"Result    : {result}\n"
        f"Verdict   : {message}\n"
    )

    if result == "FAIL":
        pytest.fail(message)

    if result == "BLOCKED":
        pytest.skip(message)

    return result, message