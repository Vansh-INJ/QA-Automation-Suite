"""
SQL Injection security evaluation engine.

This module contains the core detection and classification logic
used to evaluate API responses after SQL injection payload testing.

Responsibilities:

    - Detect SQL/database error signatures
    - Classify API responses
    - Produce standardized SecurityResult objects

The engine does NOT:

    - Send API requests
    - Build onboarding payloads
    - Write Excel reports
    - Call pytest assertions

It only evaluates security evidence.
"""

from api_framework.security.core.security_result import SecurityResult

from api_framework.security.core.security_verdicts import (
    PASS,
    FAIL,
    BLOCKED,
)


# ============================================================================
# SQL / DATABASE ERROR SIGNATURES
# ============================================================================

SQL_ERROR_SIGNATURES = [

    # Generic SQL errors
    "sql syntax",
    "syntax error at or near",
    "syntax error",
    "unterminated quoted string",
    "quoted string not properly terminated",

    # MySQL
    "mysql_fetch",
    "mysql error",
    "you have an error in your sql syntax",
    "warning: mysql",
    "column count doesn't match value count",
    "unknown column",

    # PostgreSQL
    "postgresql",
    "psycopg",
    "psycopg2",
    "pg::syntaxerror",
    "pgerror",

    # SQLite
    "sqlite",
    "sqlite3.operationalerror",

    # Microsoft SQL Server
    "unclosed quotation mark",
    "microsoft sql server",
    "odbc sql server driver",
    "sqlserverexception",
    "invalid object name",
    "conversion failed when converting",
    "incorrect syntax near",

    # Oracle
    "ora-",
    "ora-01756",
    "oracle error",
    "pl/sql",

    # Java / JDBC
    "jdbc",
    "sqlexception",
    "java.sql",

    # ORM / Database frameworks
    "sqlalchemy",
    "database error",
    "database exception",
    "hibernate",
    "nhibernate",
    "entity framework",
    "sequelize",
    "typeorm",
    "knex",
    "activerecord",
    "django.db",
    "peewee",

    # Stack trace indicators
    "at org.springframework",
    "at com.mysql",
    "at java.sql",
    "traceback (most recent call last)",
    "stacktrace",

]


# ============================================================================
# SQL ERROR DETECTION
# ============================================================================

def find_sql_error_signatures(
    response_text: str,
) -> list[str]:
    """
    Return all known SQL/database error signatures found
    in an API response.

    Args:
        response_text:
            Raw API response body.

    Returns:
        List of detected SQL/database error signatures.
    """

    text = (response_text or "").lower()

    return [
        signature
        for signature in SQL_ERROR_SIGNATURES
        if signature in text
    ]


# ============================================================================
# DB VERSION STRING PATTERNS (for error-based injection detection)
# ============================================================================

VERSION_STRING_PATTERNS = [
    # MySQL versions like 5.7.x, 8.0.x
    "5.7.", "8.0.", "8.1.", "8.2.",
    # PostgreSQL versions like 14.x, 15.x, 16.x
    "postgresql 14", "postgresql 15", "postgresql 16",
    # MSSQL
    "microsoft sql server 20",
    # MariaDB
    "mariadb",
    # SQLite version
    "sqlite version",
]


def find_version_string_leaks(
    response_text: str,
) -> list[str]:
    """
    Detect if a DB version string is reflected in the response,
    which would indicate successful error-based extraction.
    """

    text = (response_text or "").lower()

    return [
        pattern
        for pattern in VERSION_STRING_PATTERNS
        if pattern in text
    ]


# ============================================================================
# SENSITIVE DATA PATTERNS (for UNION / deep leakage scan)
# ============================================================================

SENSITIVE_RESPONSE_PATTERNS = [
    "password",
    "passwd",
    "password_hash",
    "pwd_hash",
    "secret",
    "api_key",
    "private_key",
    "access_token",
    "refresh_token",
    "credit_card",
    "cvv",
    "social_security",
    "ssn",
    "information_schema",
    "mysql.user",
    "pg_shadow",
    "sys.tables",
    "sysobjects",
]


def find_sensitive_leaks(
    response_text: str,
) -> list[str]:
    """
    Return any sensitive data patterns found in the API response.
    Useful after UNION or error-based payloads.
    """

    text = (response_text or "").lower()

    return [
        pattern
        for pattern in SENSITIVE_RESPONSE_PATTERNS
        if pattern in text
    ]


# ============================================================================
# SQL INJECTION RESULT CLASSIFICATION
# ============================================================================

def evaluate_sqli_response(
    status_code,
    field_name: str,
    payload,
    response_text: str = "",
    duration_ms=None,
) -> SecurityResult:
    """
    Evaluate an API response after a SQL injection attempt.

    Classification rules:

        1. SQL/database error leaked
            -> FAIL

        2. Server error caused by malicious input
            -> FAIL

        3. Known unrelated prerequisite error
            -> BLOCKED

        4. Client-side validation rejection
            -> PASS

        5. Successful acceptance of malicious payload
            -> FAIL

        6. Unknown response
            -> BLOCKED

    Returns:
        SecurityResult
    """

    response_lower = (
        response_text or ""
    ).lower()

    leaked = find_sql_error_signatures(
        response_text
    )

    # ------------------------------------------------------------------------
    # 1. SQL ERROR LEAK = SECURITY FAIL
    # ------------------------------------------------------------------------

    if leaked:

        return SecurityResult(
            result=FAIL,
            message=(
                f"Potential SQL injection vulnerability detected "
                f"on '{field_name}'. SQL/database error signature "
                f"leaked while testing payload {payload!r}: {leaked}"
            ),
            status_code=status_code,
            vulnerability_type="SQL Injection",
            field_name=field_name,
            payload=str(payload),
            leaked_signatures=leaked,
            duration_ms=duration_ms,
        )

    # ------------------------------------------------------------------------
    # 2. SERVER ERROR
    # ------------------------------------------------------------------------

    if status_code and status_code >= 500:

        unrelated_errors = [

            "missing required document",

            "please upload",

            "required document",

        ]

        aadhar_document_error = (

            "aadhar" in response_lower

            and (

                "document" in response_lower

                or "missing" in response_lower

                or "upload" in response_lower

            )
        )

        if (

            any(
                error in response_lower
                for error in unrelated_errors
            )

            or aadhar_document_error
        ):

            return SecurityResult(
                result=BLOCKED,
                message=(
                    f"SQL injection test could not be conclusively "
                    f"evaluated for '{field_name}' using payload "
                    f"{payload!r}. The API returned HTTP "
                    f"{status_code} due to an unrelated "
                    f"application/prerequisite error rather than "
                    f"processing the injected field."
                ),
                status_code=status_code,
                vulnerability_type="SQL Injection",
                field_name=field_name,
                payload=str(payload),
                leaked_signatures=leaked,
                duration_ms=duration_ms,
            )

        return SecurityResult(
            result=FAIL,
            message=(
                f"HTTP {status_code} server error occurred while "
                f"testing SQL injection on '{field_name}' with "
                f"payload {payload!r}. No SQL error signature was "
                f"exposed, but the malformed input caused an "
                f"unhandled server failure. This should be "
                f"investigated for robustness and potential "
                f"security impact."
            ),
            status_code=status_code,
            vulnerability_type="SQL Injection",
            field_name=field_name,
            payload=str(payload),
            leaked_signatures=leaked,
            duration_ms=duration_ms,
        )

    # ------------------------------------------------------------------------
    # 3. SAFE CLIENT VALIDATION
    # ------------------------------------------------------------------------

    if status_code in [

        400,
        401,
        403,
        404,
        409,
        422,

    ]:

        return SecurityResult(
            result=PASS,
            message=(
                f"Payload safely rejected with HTTP "
                f"{status_code} without SQL/database error leakage."
            ),
            status_code=status_code,
            vulnerability_type="SQL Injection",
            field_name=field_name,
            payload=str(payload),
            leaked_signatures=leaked,
            duration_ms=duration_ms,
        )

    # ------------------------------------------------------------------------
    # 4. SUCCESS RESPONSE
    # ------------------------------------------------------------------------

    if status_code and 200 <= status_code < 300:

        return SecurityResult(
            result=FAIL,
            message=(
                f"SQL injection payload {payload!r} was accepted "
                f"successfully on '{field_name}' with HTTP "
                f"{status_code}. Manual verification is required "
                f"to determine whether the payload was safely stored "
                f"as literal text or executed/interpreted by the "
                f"backend."
            ),
            status_code=status_code,
            vulnerability_type="SQL Injection",
            field_name=field_name,
            payload=str(payload),
            leaked_signatures=leaked,
            duration_ms=duration_ms,
        )

    # ------------------------------------------------------------------------
    # 5. UNEXPECTED RESPONSE
    # ------------------------------------------------------------------------

    return SecurityResult(
        result=BLOCKED,
        message=(
            f"Unexpected HTTP response {status_code} received "
            f"while testing '{field_name}' with payload "
            f"{payload!r}."
        ),
        status_code=status_code,
        vulnerability_type="SQL Injection",
        field_name=field_name,
        payload=str(payload),
        leaked_signatures=leaked,
        duration_ms=duration_ms,
    )