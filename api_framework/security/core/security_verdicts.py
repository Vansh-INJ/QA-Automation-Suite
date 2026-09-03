"""
Common security verdict constants.

All security testing modules should use these standard verdicts
instead of hardcoding result strings throughout the framework.
"""

# Security test passed successfully.
PASS = "PASS"

# A potential security vulnerability was detected.
FAIL = "FAIL"

# The security test could not be conclusively evaluated because
# of an external or unrelated application issue.
BLOCKED = "BLOCKED"


VALID_VERDICTS = {
    PASS,
    FAIL,
    BLOCKED,
}