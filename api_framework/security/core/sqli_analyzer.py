"""
SQL Injection response analysis utilities.

Responsible for analyzing API responses during SQL injection testing.

This module does not send requests and does not inject payloads.
It only extracts security-relevant evidence from responses.
"""



from api_framework.security.core.sqli_engine import find_sql_error_signatures
def extract_response_text(response) -> str:
    """
    Safely extract response text.

    Args:
        response: HTTP response object.

    Returns:
        Response body as a string.
    """

    return getattr(
        response,
        "text",
        "",
    ) or ""


def extract_response_status(response):
    """
    Safely extract HTTP status code.

    Args:
        response: HTTP response object.

    Returns:
        HTTP status code or None.
    """

    return getattr(
        response,
        "status_code",
        None,
    )


def analyze_sql_errors(response) -> list[str]:
    """
    Detect SQL/database error signatures in an API response.

    Args:
        response: HTTP response object.

    Returns:
        List of detected SQL error signatures.
    """

    response_text = extract_response_text(
        response
    )

    return find_sql_error_signatures(
        response_text
    )


def build_response_signature(response) -> dict:
    """
    Build a lightweight response signature.

    Primarily used for comparing responses during
    boolean-based blind SQL injection testing.
    """

    response_text = extract_response_text(
        response
    )

    return {
        "status": extract_response_status(
            response
        ),
        "sql_error_signatures": tuple(
            find_sql_error_signatures(
                response_text
            )
        ),
        "response_length": len(
            response_text
        ),
    }