"""
idor_engine.py

Core classification logic for Access Control / IDOR test results.
Given a response returned when acting_profile tried to access a resource
it should NOT be able to (or SHOULD be able to, for negative-of-negative
sanity checks), classify the outcome.

Design mirrors sqli_engine.py's evaluate_sqli_response() so it's familiar
to anyone who has worked in the SQLi module.
"""

from api_framework.security.core.access_control.access_control_result import (
    AccessControlResult, PASS, FAIL, BLOCKED, ERROR
)

# Sensitive field names to scan for in response bodies when access SHOULD
# have been denied but the request returned 200 anyway. Extend this list
# to match your actual HRMS payload shapes (salary, bank details, etc.)
SENSITIVE_FIELD_MARKERS = [
    "salary", "bank_account", "ssn", "pan_number", "aadhaar",
    "date_of_birth", "compensation", "bonus", "password", "token",
    "employee_id", "email", "phone", "address",
    # Payroll/financial aggregate fields (added after confirmed leak via
    # /api/admin/payroll/runs -- these are org-wide financial totals,
    # not per-employee PII, but equally sensitive from a business
    # confidentiality standpoint)
    "total_gross", "total_net_pay", "total_lop_deduction",
    "total_pf_employee", "total_pf_employer",
    "total_esi_employee", "total_esi_employer",
    "total_pt", "total_lwf_employee", "total_lwf_employer",
    "legal_entity_name", "approved_at", "paid_at",
]

# Status codes that represent CORRECT denial of unauthorized access
CORRECT_DENIAL_CODES = {401, 403, 404}


def evaluate_access_attempt(
    endpoint: str,
    method: str,
    acting_profile: str,
    status_code: int,
    response_text: str,
    should_have_access: bool,
    target_owner_profile: str = None,
    resource_id: str = None,
    vulnerability_type: str = "IDOR",
    duration_ms: float = 0.0,
) -> AccessControlResult:
    """
    should_have_access: whether `acting_profile` SHOULD legitimately be able
    to access this resource. False for the vast majority of IDOR/privilege
    escalation cases (an employee should NOT reach another employee's data).
    True is used for control cases -- verifying legitimate access still works
    (so you're not just testing a broken/over-locked-down endpoint).
    """
    leaked = _find_leaked_fields(response_text) if status_code == 200 else []

    if should_have_access:
        # Control case: access SHOULD succeed. 2xx = correct. Anything else = FAIL
        # (a false-positive lockout, which breaks legitimate users -- still a bug)
        if 200 <= status_code < 300:
            return AccessControlResult(
                result=PASS, vulnerability_type=vulnerability_type, endpoint=endpoint,
                method=method, acting_profile=acting_profile, target_owner_profile=target_owner_profile,
                expected_status=200, actual_status=status_code, resource_id=resource_id,
                message="Legitimate access correctly allowed.", duration_ms=duration_ms,
            )
        return AccessControlResult(
            result=FAIL, vulnerability_type="FALSE_POSITIVE_LOCKOUT", endpoint=endpoint,
            method=method, acting_profile=acting_profile, target_owner_profile=target_owner_profile,
            expected_status=200, actual_status=status_code, resource_id=resource_id,
            message="Legitimate user incorrectly denied access.", duration_ms=duration_ms,
        )

    # Primary case: access should NOT succeed
    if status_code in CORRECT_DENIAL_CODES:
        return AccessControlResult(
            result=PASS, vulnerability_type=vulnerability_type, endpoint=endpoint,
            method=method, acting_profile=acting_profile, target_owner_profile=target_owner_profile,
            expected_status=403, actual_status=status_code, resource_id=resource_id,
            message="Access correctly denied.", duration_ms=duration_ms,
        )

    if 200 <= status_code < 300:
        return AccessControlResult(
            result=FAIL, vulnerability_type=vulnerability_type, endpoint=endpoint,
            method=method, acting_profile=acting_profile, target_owner_profile=target_owner_profile,
            expected_status=403, actual_status=status_code, resource_id=resource_id,
            confidence="HIGH" if leaked else "MEDIUM",
            leaked_fields=leaked,
            message=f"Unauthorized access SUCCEEDED. Leaked fields: {leaked}" if leaked
                    else "Unauthorized access succeeded (2xx returned).",
            duration_ms=duration_ms,
        )

    if 500 <= status_code < 600:
        return AccessControlResult(
            result=BLOCKED, vulnerability_type=vulnerability_type, endpoint=endpoint,
            method=method, acting_profile=acting_profile, target_owner_profile=target_owner_profile,
            expected_status=403, actual_status=status_code, resource_id=resource_id,
            message="Server error -- inconclusive, needs manual review.", duration_ms=duration_ms,
        )

    # Any other unexpected code (e.g. 400) -- inconclusive but log it
    return AccessControlResult(
        result=BLOCKED, vulnerability_type=vulnerability_type, endpoint=endpoint,
        method=method, acting_profile=acting_profile, target_owner_profile=target_owner_profile,
        expected_status=403, actual_status=status_code, resource_id=resource_id,
        message=f"Unexpected status code {status_code} -- review manually.", duration_ms=duration_ms,
    )


def _find_leaked_fields(response_text: str) -> list:
    """Scan a 200-OK response body for sensitive field markers, case-insensitive."""
    if not response_text:
        return []
    lowered = response_text.lower()
    return [f for f in SENSITIVE_FIELD_MARKERS if f in lowered]