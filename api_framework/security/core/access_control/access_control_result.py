"""
access_control_result.py

Result model for Access Control / IDOR test outcomes.
Mirrors the existing SecurityResult pattern used by the SQLi engine so it
plugs into the same reporting pipeline (Excel/JSON) with minimal changes.
"""

from dataclasses import dataclass, field
from typing import Optional


# Verdict constants (mirrors PASS/FAIL/BLOCKED convention from sqli_engine)
PASS = "PASS"        # Access correctly denied/scoped as expected
FAIL = "FAIL"        # Unauthorized access succeeded -> vulnerability
BLOCKED = "BLOCKED"  # Inconclusive (e.g. resource didn't exist, setup issue)
ERROR = "ERROR"      # Test itself errored (network, auth setup failure)


@dataclass
class AccessControlResult:
    result: str                        # PASS / FAIL / BLOCKED / ERROR
    vulnerability_type: str            # IDOR | PRIVILEGE_ESCALATION | FORCED_BROWSING | HORIZONTAL_ACCESS | VERTICAL_ACCESS
    endpoint: str                      # e.g. "/api/employee/{employee_id}"
    method: str                        # GET/POST/PUT/DELETE
    acting_profile: str                # auth_profile used to make the call, e.g. "employee"
    target_owner_profile: Optional[str] = None  # whose resource was targeted, e.g. "other_employee"
    expected_status: int = 403         # what SHOULD happen (403/404) if access control is correct
    actual_status: int = None
    resource_id: Optional[str] = None
    owasp_category: str = "A01:2021-Broken Access Control"
    confidence: str = "HIGH"
    leaked_fields: list = field(default_factory=list)  # if body leaked, which sensitive fields were present
    message: str = ""
    duration_ms: float = 0.0