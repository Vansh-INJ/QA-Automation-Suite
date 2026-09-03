"""
Common security test result model.

This module defines the standard result object used across all
security testing modules.

Examples:
    - SQL Injection
    - XSS
    - Authentication Security
    - IDOR
    - Rate Limiting
    - Sensitive Data Exposure

Keeping one common result structure ensures that all security engines
produce results in a consistent format.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SecurityResult:
    """
    Standard result returned by a security test evaluation.

    Attributes:
        result:
            Final security verdict.

            Expected values:
                PASS
                FAIL
                BLOCKED

        message:
            Human-readable explanation of the verdict.

        status_code:
            HTTP status code returned by the API.

        vulnerability_type:
            Type of security test.

            Example:
                SQL Injection
                XSS
                IDOR

        field_name:
            Field or attack surface being tested.

        payload:
            Malicious payload used during testing.

        leaked_signatures:
            Security/database error signatures detected
            in the API response.

        duration_ms:
            API response duration in milliseconds.
    """

    result: str

    message: str

    status_code: Optional[int] = None

    vulnerability_type: Optional[str] = None

    field_name: Optional[str] = None

    payload: Optional[str] = None

    leaked_signatures: Optional[list[str]] = None

    duration_ms: Optional[float] = None