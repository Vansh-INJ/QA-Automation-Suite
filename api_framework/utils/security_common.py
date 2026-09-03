"""
Common security testing utilities.

This module contains shared security-related logic that can be reused
across different security test types such as SQL Injection, XSS,
authentication testing, and other vulnerability checks.
"""


# ============================================================================
# SQL ERROR SIGNATURES
# ============================================================================

SQL_ERROR_SIGNATURES = [
    # MySQL
    "you have an error in your sql syntax",
    "mysql_fetch",
    "mysql_num_rows",
    "mysql_query",
    "mysqli_sql_exception",
    "mysql error",

    # PostgreSQL
    "postgresql error",
    "pg_query",
    "pg_exec",
    "psqlexception",

    # Microsoft SQL Server
    "unclosed quotation mark",
    "quoted string not properly terminated",
    "microsoft sql server",
    "sqlserverexception",
    "odbc sql server driver",

    # Oracle
    "ora-",
    "oracle error",

    # SQLite
    "sqlite error",
    "sqlite3.operationalerror",
    "sqlite_exception",

    # Generic SQL errors
    "sql syntax",
    "syntax error near",
    "database error",
    "sqlstate",
]


# ============================================================================
# SQL ERROR DETECTION
# ============================================================================

def find_sql_error_signatures(response_text: str) -> list[str]:
    """
    Search API response text for known SQL/database error signatures.

    Args:
        response_text:
            Raw API response body.

    Returns:
        List of detected SQL error signatures.
        Empty list means no known SQL error was detected.
    """

    if not response_text:
        return []

    response_lower = response_text.lower()

    detected = []

    for signature in SQL_ERROR_SIGNATURES:

        if signature in response_lower:
            detected.append(signature)

    return detected


# ============================================================================
# SQL INJECTION RESULT CLASSIFICATION
# ============================================================================

def classify_sqli_result(
    status: int | None,
    leaked: list[str],
    field_name: str,
    payload_used: str,
    response_text: str,
) -> tuple[str, str]:
    """
    Classify the result of a SQL Injection test.

    Classification is based on:

    1. SQL/database error leakage
    2. Unexpected server errors
    3. Proper rejection of malicious input
    4. Suspicious successful responses

    Returns:
        tuple:
            (result, message)

        result:
            PASS / FAIL / WARNING
    """

    # ------------------------------------------------------------
    # CASE 1: SQL ERROR LEAKED
    # ------------------------------------------------------------

    if leaked:
        return (
            "FAIL",
            (
                f"Potential SQL Injection vulnerability detected. "
                f"Database error leaked for field '{field_name}'. "
                f"Detected signatures: {', '.join(leaked)}"
            ),
        )

    # ------------------------------------------------------------
    # CASE 2: SERVER ERROR
    # ------------------------------------------------------------

    if status is not None and status >= 500:
        return (
            "WARNING",
            (
                f"Server error ({status}) received while testing "
                f"SQL injection payload in field '{field_name}'. "
                f"No explicit SQL error was detected, but the API "
                f"should handle malicious input gracefully."
            ),
        )

    # ------------------------------------------------------------
    # CASE 3: MALICIOUS INPUT REJECTED
    # ------------------------------------------------------------

    if status in [400, 401, 403, 422]:
        return (
            "PASS",
            (
                f"SQL injection payload was safely rejected for "
                f"field '{field_name}' with status {status}."
            ),
        )

    # ------------------------------------------------------------
    # CASE 4: SUCCESS RESPONSE
    # ------------------------------------------------------------

    if status in [200, 201, 202, 204]:
        return (
            "WARNING",
            (
                f"SQL injection payload was accepted with status "
                f"{status} for field '{field_name}'. "
                f"Manual verification is recommended."
            ),
        )

    # ------------------------------------------------------------
    # CASE 5: UNKNOWN RESPONSE
    # ------------------------------------------------------------

    return (
        "WARNING",
        (
            f"Unexpected response status '{status}' received while "
            f"testing SQL injection payload in field '{field_name}'. "
            f"Manual investigation recommended."
        ),
    )