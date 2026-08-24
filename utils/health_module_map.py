"""
Classifies each endpoint into a business module (User / HR / Admin /
Finance / Other) purely from its path — no need to manually tag all 149+
registry entries. Also holds the owner-assignment map so failures can be
routed to a responsible developer automatically in the dashboard email.
"""

import re

# ---------------------------------------------------------------------------
# Path-prefix -> module classification.
# Order matters: more specific prefixes are checked first.
# ---------------------------------------------------------------------------
MODULE_RULES = [
    (r"^/api/admin/payroll", "Finance"),
    (r"^/api/hr/payslips", "Finance"),
    (r"^/api/hr/payroll", "Finance"),
    (r"^/api/admin/employees/.*/(tax|perquisites)", "Finance"),
    (r"^/api/hr/tax-declaration", "Finance"),
    (r"^/api/admin", "Admin"),
    (r"^/api/hr", "HR"),
    (r"^/api/me", "User"),
    (r"^/api/auth", "User"),
]


def classify_module(path: str) -> str:
    for pattern, module in MODULE_RULES:
        if re.match(pattern, path):
            return module
    return "Other"


# ---------------------------------------------------------------------------
# Owner assignment — who gets notified/blamed for failures in each module.
# EDIT THESE to your actual team's real email addresses.
# ---------------------------------------------------------------------------
MODULE_OWNERS = {
    "User": "vansh.sharma@injpartners.com",
    "HR": "vansh.sharma@injpartners.com",
    "Admin": "vansh.sharma@injpartners.com",
    "Finance": "vansh.sharma@injpartners.com",
    "Other": "vansh.sharma@injpartners.com",
}


def owner_for(path: str) -> str:
    return MODULE_OWNERS.get(classify_module(path), MODULE_OWNERS["Other"])
