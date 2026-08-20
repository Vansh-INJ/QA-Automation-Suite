"""
Central registry of endpoints monitored by the daily API Health Suite.

v3: added `action` (human-readable label for the report) and `sla_ms`
(response-time threshold — flagged separately from pass/fail status match)
per endpoint.
"""

from datetime import date


def current_month_param():
    return {"month": date.today().strftime("%Y-%m")}


def leave_requests_params():
    return {"page": 1, "per_page": 10, "order": "desc"}


def tickets_params():
    return {"page": 1, "per_page": 10}


def notifications_params():
    return {"page": 1, "per_page": 10, "unread_only": "false"}


AUTH_PROFILES = {
    "employee": {
        "username_env": "HEALTH_USER_USERNAME",
        "password_env": "HEALTH_USER_PASSWORD",
    },
}

# Default SLA (ms) applied when an endpoint doesn't specify its own.
# Adjust globally here, or override per-endpoint below.
DEFAULT_SLA_MS = 2000

ENDPOINTS = [
    {
        "name": "login",
        "action": "User Login / Authentication",
        "method": "POST",
        "path": "/api/auth/login",
        "auth_profile": None,
        "is_login": True,
        "expected_status": 200,
        "critical": True,
        "sla_ms": 1500,
    },
    {
        "name": "me",
        "action": "Fetch Logged-in User Profile",
        "method": "GET",
        "path": "/api/me",
        "auth_profile": "employee",
        "expected_status": 200,
        "critical": True,
        "sla_ms": 1000,
    },
    {
        "name": "get_user_details",
        "action": "Fetch Extended User Details",
        "method": "GET",
        "path": "/api/me/getUserDetails",
        "auth_profile": "employee",
        "expected_status": 200,
        "sla_ms": 1000,
    },
    {
        "name": "employee_leave_policy",
        "action": "Fetch Leave Policy",
        "method": "GET",
        "path": "/api/me/employee-leave-policy",
        "auth_profile": "employee",
        "expected_status": 200,
        "sla_ms": 1500,
    },
    {
        "name": "employee_holiday_policy",
        "action": "Fetch Holiday Policy",
        "method": "GET",
        "path": "/api/me/employee-holiday-policy",
        "auth_profile": "employee",
        "expected_status": 200,
        "sla_ms": 1500,
    },
    {
        "name": "attendance_monthly",
        "action": "Fetch Monthly Attendance",
        "method": "GET",
        "path": "/api/me/attendance",
        "params": current_month_param,
        "auth_profile": "employee",
        "expected_status": 200,
        "sla_ms": 2000,
    },
    {
        "name": "leave_requests",
        "action": "Fetch Leave Requests",
        "method": "GET",
        "path": "/api/me/leave-requests",
        "params": leave_requests_params,
        "auth_profile": "employee",
        "expected_status": 200,
        "sla_ms": 2000,
    },
    {
        "name": "ticketing_tickets",
        "action": "Fetch Support Tickets",
        "method": "GET",
        "path": "/api/me/ticketing/tickets",
        "params": tickets_params,
        "auth_profile": "employee",
        "expected_status": 200,
        "sla_ms": 2000,
    },
    {
        "name": "notifications",
        "action": "Fetch Notifications",
        "method": "GET",
        "path": "/api/me/notifications",
        "params": notifications_params,
        "auth_profile": "employee",
        "expected_status": 200,
        "sla_ms": 1500,
    },
    {
        "name": "hr_payslips",
        "action": "Fetch Payslips",
        "method": "GET",
        "path": "/api/hr/payslips",
        "auth_profile": "employee",
        "expected_status": 200,
        "sla_ms": 2500,
    },

    # --- Deliberately EXCLUDED: write/side-effecting action ---
    # {
    #     "name": "attendance_punch",
    #     "action": "Punch Attendance",
    #     "method": "POST",
    #     "path": "/api/hr/attendance/punch",
    #     ...
    # }
]
