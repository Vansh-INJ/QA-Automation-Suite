"""
access_matrix.py -- TRIMMED to 7 cases against CONFIRMED-LIVE endpoints only.

Removed vs. previous version:
  - "Employee cannot access admin dashboard" (/api/admin/dashboard)
    -> health suite confirms this route 404s ("Route not found!"). Testing
       access control on a dead route produces a false PASS (404 is in
       idor_engine's CORRECT_DENIAL_CODES, so it looks like "correctly
       denied" when really it's "doesn't exist"). Re-add once the real
       dashboard path is confirmed.

  - "Employee cannot read role/permission definitions"
    (/api/admin/roles/{role_uuid}/permissions)
    -> no RESOLVER_CONFIG entry for 'role_uuid' exists yet; health suite
       confirms this fails ID resolution before even reaching the request.
       Re-add once a real roles-list source endpoint is identified and
       added to RESOLVER_CONFIG.

Everything below hits a path that PASSED in the health suite run, i.e.
confirmed live and reachable -- so a FAIL here is a real access-control
signal, not a dead-route artifact.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AccessMatrixCase:
    name: str
    endpoint: str
    method: str
    resource_owner_profile: str
    allowed_profiles: list
    denied_profiles: list
    vulnerability_type: str = "IDOR"
    resource_id_param: Optional[str] = None
    notes: str = ""


ACCESS_MATRIX = [

    # -----------------------------------------------------------------
    # HORIZONTAL IDOR -- same role (employee), different identity
    # -----------------------------------------------------------------
    AccessMatrixCase(
        name="Employee cannot view another employee's payslips",
        endpoint="/api/hr/payslips",
        method="GET",
        resource_owner_profile="employee_a",
        allowed_profiles=["employee_a", "hr", "admin", "finance"],
        denied_profiles=["employee_b"],
        vulnerability_type="HORIZONTAL_ACCESS",
        notes=("If this list endpoint is server-scoped to the caller (always "
               "returns YOUR OWN payslips regardless of who calls it), a 200 "
               "for employee_b is expected and this test needs to instead "
               "assert employee_b's response body does not contain employee_a's "
               "payslip data, not expect a 403/404. Flag if this fires."),
    ),
    AccessMatrixCase(
        name="Employee cannot view another employee's attendance",
        endpoint="/api/me/attendance",
        method="GET",
        resource_owner_profile="employee_a",
        allowed_profiles=["employee_a", "hr", "admin"],
        denied_profiles=["employee_b"],
        vulnerability_type="HORIZONTAL_ACCESS",
        notes="Same self-scoping caveat as payslips above.",
    ),

    # -----------------------------------------------------------------
    # VERTICAL ACCESS -- employee should NOT reach HR/Admin/Finance data
    # -----------------------------------------------------------------
    AccessMatrixCase(
        name="Employee cannot list all users (HR-only directory)",
        endpoint="/api/hr/users",
        method="GET",
        resource_owner_profile="hr",
        allowed_profiles=["hr", "admin"],
        denied_profiles=["employee"],
        vulnerability_type="VERTICAL_ACCESS",
        notes="Full user directory -- reconnaissance value if leaked to any employee.",
    ),
    AccessMatrixCase(
        name="Employee cannot view salary structures",
        endpoint="/api/admin/salary-structures",
        method="GET",
        resource_owner_profile="admin",
        allowed_profiles=["admin", "finance"],
        denied_profiles=["employee", "hr"],  # TODO: confirm whether HR should see this
        vulnerability_type="VERTICAL_ACCESS",
        notes="Compensation bands -- high business-sensitivity if leaked.",
    ),
    AccessMatrixCase(
        name="Employee cannot view pay components",
        endpoint="/api/admin/pay-components",
        method="GET",
        resource_owner_profile="admin",
        allowed_profiles=["admin", "finance"],
        denied_profiles=["employee", "hr"],
        vulnerability_type="VERTICAL_ACCESS",
    ),
    AccessMatrixCase(
        name="Employee cannot view payroll runs",
        endpoint="/api/admin/payroll/runs",
        method="GET",
        resource_owner_profile="finance",
        allowed_profiles=["finance", "admin"],
        denied_profiles=["employee", "hr"],
        vulnerability_type="VERTICAL_ACCESS",
        notes="Payroll run data -- confirms who was paid what, when. Finance/Admin only.",
    ),
    AccessMatrixCase(
        name="Employee cannot view offer/onboarding pipeline",
        endpoint="/api/hr/offers",
        method="GET",
        resource_owner_profile="hr",
        allowed_profiles=["hr", "admin"],
        denied_profiles=["employee"],
        vulnerability_type="VERTICAL_ACCESS",
        notes="Candidate PII (name, email, offered salary) in the pipeline.",
    ),
]

# -----------------------------------------------------------------------
# PARKED -- re-add once prerequisites below are resolved
# -----------------------------------------------------------------------
#   1. "Employee cannot access admin dashboard" -- need real dashboard path
#      (confirmed /api/admin/dashboard 404s)
#   2. "Employee cannot read role/permission definitions" -- need real
#      roles-list endpoint added to RESOLVER_CONFIG as 'role_uuid'