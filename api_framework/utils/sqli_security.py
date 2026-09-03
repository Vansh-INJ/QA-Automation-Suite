"""
Shared SQL Injection security utilities.

This module contains the common SQLi detection and classification logic
used across all SQL injection test suites.

Keeping this logic centralized ensures that POST body, query parameter,
path parameter, and header SQLi tests all use the same security rules.
"""


# ---------------------------------------------------------------------------
# SQL / DATABASE ERROR SIGNATURES
# ---------------------------------------------------------------------------

SQL_ERROR_SIGNATURES = [
    # Generic SQL errors
    "sql syntax",
    "syntax error at or near",
    "syntax error",

    # MySQL
    "mysql_fetch",
    "mysql error",
    "you have an error in your sql syntax",
    "warning: mysql",

    # PostgreSQL
    "postgresql",
    "psycopg",
    "psycopg2",
    "pg::syntaxerror",

    # SQLite
    "sqlite",
    "sqlite3.operationalerror",

    # Microsoft SQL Server
    "unclosed quotation mark",
    "microsoft sql server",
    "odbc sql server driver",
    "sqlserverexception",

    # Oracle
    "ora-",
    "ora-01756",
    "oracle error",

    # Java / JDBC
    "jdbc",
    "sqlexception",

    # ORM / Database frameworks
    "sqlalchemy",
    "database error",
    "database exception",
]


# ---------------------------------------------------------------------------
# SQL ERROR DETECTION
# ---------------------------------------------------------------------------

def find_sql_error_signatures(response_text: str) -> list[str]:
    """
    Return all known SQL/database error signatures found in a response.

    Args:
        response_text: Raw API response body.

    Returns:
        List of matched SQL/database error signatures.
    """

    text = (response_text or "").lower()

    return [
        signature
        for signature in SQL_ERROR_SIGNATURES
        if signature in text
    ]


# ---------------------------------------------------------------------------
# AUTHORITATIVE SQLI RESULT CLASSIFICATION
# ---------------------------------------------------------------------------

def classify_sqli_result(
    status,
    leaked,
    field_name,
    payload_used,
    response_text="",
):
    """
    Classify SQL injection test response into:
    PASS, FAIL, or BLOCKED.
    """

    response_lower = (
        response_text or ""
    ).lower()

    # ---------------------------------
    # 1. SQL ERROR LEAK = SECURITY FAIL
    # ---------------------------------
    if leaked:
        return (
            "FAIL",
            f"Potential SQL injection vulnerability detected on "
            f"'{field_name}'. SQL/database error signature leaked "
            f"while testing payload {payload_used!r}: {leaked}"
        )

    # ---------------------------------
    # 2. SERVER ERROR
    # ---------------------------------
    if status and status >= 500:

        # FIX 3: "aadhar" was previously a standalone match, which meant
        # ANY response mentioning that word - including a legitimate
        # validation failure specifically about the identity.aadhar
        # field, unrelated to document uploads - would get
        # misclassified as an unrelated document-prerequisite issue and
        # hidden as "BLOCKED". Now it only counts as an unrelated
        # document-prerequisite error if it's paired with
        # document/missing/upload language, not just the word "aadhar"
        # appearing anywhere in the response.
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
            any(error in response_lower for error in unrelated_errors)
            or aadhar_document_error
        ):
            return (
                "BLOCKED",
                f"SQL injection test could not be conclusively evaluated "
                f"for '{field_name}' using payload {payload_used!r}. "
                f"The API returned HTTP {status} due to an unrelated "
                f"application/prerequisite error rather than processing "
                f"the injected field."
            )

        return (
            "FAIL",
            f"HTTP {status} server error occurred while testing "
            f"SQL injection on '{field_name}' with payload "
            f"{payload_used!r}. No SQL error signature was exposed, "
            f"but the malformed input caused an unhandled server failure. "
            f"This should be investigated for robustness and potential "
            f"security impact."
        )

    # ---------------------------------
    # 3. SAFE CLIENT VALIDATION
    # ---------------------------------
    if status in [400, 401, 403, 404, 409, 422]:
        return (
            "PASS",
            f"Payload safely rejected with HTTP {status} "
            f"without SQL/database error leakage."
        )

    # ---------------------------------
    # 4. SUCCESS RESPONSE
    # ---------------------------------
    if status and 200 <= status < 300:
        return (
            "FAIL",
            f"SQL injection payload {payload_used!r} was accepted "
            f"successfully on '{field_name}' with HTTP {status}. "
            f"Manual verification is required to determine whether "
            f"the payload was safely stored as literal text or "
            f"executed/interpreted by the backend."
        )

    return (
        "BLOCKED",
        f"Unexpected HTTP response {status} received while testing "
        f"'{field_name}' with payload {payload_used!r}."
    )