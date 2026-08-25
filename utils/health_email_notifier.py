"""
HRMS API Health Suite
Resend Email Notification / Executive Dashboard

Sends:
    1. HTML health dashboard
    2. Excel health report
    3. summary.json

No SMTP.
No n8n.
Uses Resend HTTPS API.
"""

import base64
import html
import os
from collections import OrderedDict
from datetime import datetime

import resend


# ============================================================
# CONFIGURATION
# ============================================================

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

FROM_EMAIL = os.getenv(
    "HEALTH_MAIL_FROM",
    "HRMS API Health <onboarding@resend.dev>",
)

TO_EMAIL = os.getenv(
    "HEALTH_MAIL_TO",
    "",
)

ENVIRONMENT = os.getenv(
    "HEALTH_ENVIRONMENT",
    "Development",
)

BASE_URL = os.getenv(
    "BASE_URL",
    "",
)


# ============================================================
# HELPERS
# ============================================================

def _safe(value):
    if value is None:
        return ""

    return html.escape(str(value))


def _status_color(passed):
    return "#16a34a" if passed else "#dc2626"


def _status_label(passed):
    return "HEALTHY" if passed else "FAILED"


def _format_duration(value):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):.1f} ms"
    except Exception:
        return str(value)


def _format_status(value):
    if value is None:
        return "NO RESPONSE"

    return str(value)


def _get_health_percentage(summary):
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)

    if total == 0:
        return 0

    return round((passed / total) * 100, 1)


def _overall_status(summary):
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)

    critical_failed = summary.get(
        "critical_failed",
        [],
    )

    if total == 0:
        return {
            "label": "NO DATA",
            "color": "#64748b",
            "emoji": "⚪",
        }

    if critical_failed:
        return {
            "label": "CRITICAL FAILURE",
            "color": "#dc2626",
            "emoji": "🔴",
        }

    if passed < total:
        return {
            "label": "DEGRADED",
            "color": "#f59e0b",
            "emoji": "🟡",
        }

    return {
        "label": "ALL SYSTEMS HEALTHY",
        "color": "#16a34a",
        "emoji": "🟢",
    }


def _progress_bar(percentage):
    if percentage >= 95:
        color = "#16a34a"
    elif percentage >= 80:
        color = "#f59e0b"
    else:
        color = "#dc2626"

    return f"""
    <div style="
        width:100%;
        height:14px;
        background:#e5e7eb;
        border-radius:8px;
        overflow:hidden;
        margin-top:10px;
    ">
        <div style="
            width:{percentage}%;
            height:14px;
            background:{color};
            border-radius:8px;
        "></div>
    </div>
    """


# ============================================================
# CRITICAL FAILURES
# ============================================================

def _build_critical_failures(summary):
    critical_failures = summary.get(
        "critical_failed",
        [],
    )

    if not critical_failures:
        return """
        <div style="
            background:#f0fdf4;
            border:1px solid #bbf7d0;
            border-radius:8px;
            padding:16px;
            margin-bottom:20px;
        ">
            <div style="
                font-size:15px;
                font-weight:700;
                color:#166534;
            ">
                🟢 No Critical Failures
            </div>

            <div style="
                color:#475569;
                margin-top:6px;
                font-size:13px;
            ">
                All critical APIs passed during this health check.
            </div>
        </div>
        """

    rows = ""

    for failure in critical_failures:
        rows += f"""
        <div style="
            background:#fef2f2;
            border-left:5px solid #dc2626;
            padding:14px;
            margin-bottom:10px;
            border-radius:5px;
        ">
            <div style="
                font-size:15px;
                font-weight:700;
                color:#991b1b;
            ">
                🔴 {_safe(failure)}
            </div>

            <div style="
                font-size:12px;
                color:#64748b;
                margin-top:5px;
            ">
                CRITICAL API
            </div>
        </div>
        """

    return f"""
    <div style="margin-bottom:20px;">
        <div style="
            font-size:18px;
            font-weight:700;
            color:#0f172a;
            margin-bottom:10px;
        ">
            🚨 Critical Failures
        </div>

        {rows}
    </div>
    """


# ============================================================
# FAILURE DETAILS
# ============================================================

def _build_failure_details(results):
    failures = [
        result
        for result in results
        if not result.get("passed", False)
    ]

    if not failures:
        return """
        <div style="
            background:#f0fdf4;
            border:1px solid #bbf7d0;
            border-radius:8px;
            padding:18px;
            margin-bottom:20px;
        ">
            <div style="
                font-size:16px;
                font-weight:700;
                color:#166534;
            ">
                ✅ No API Failures
            </div>

            <div style="
                font-size:13px;
                color:#475569;
                margin-top:5px;
            ">
                All monitored APIs returned their expected status codes.
            </div>
        </div>
        """

    cards = ""

    for result in failures:

        action = _safe(
            result.get(
                "action",
                result.get("name", "Unknown API"),
            )
        )

        method = _safe(
            result.get("method", "")
        )

        endpoint = _safe(
            result.get("endpoint", "")
        )

        actual_status = _format_status(
            result.get("status_code")
        )

        expected_status = _safe(
            result.get("expected_status", "")
        )

        duration = _format_duration(
            result.get("elapsed_ms")
        )

        sla = _format_duration(
            result.get("sla_ms")
        )

        api_message = _safe(
            result.get(
                "api_message",
                "API request failed",
            )
        )

        error = _safe(
            result.get("error", "")
        )

        critical = result.get(
            "critical",
            False,
        )

        critical_badge = ""

        if critical:
            critical_badge = """
            <span style="
                display:inline-block;
                background:#dc2626;
                color:white;
                padding:3px 8px;
                border-radius:10px;
                font-size:10px;
                font-weight:700;
                margin-left:8px;
            ">
                CRITICAL
            </span>
            """

        cards += f"""
        <div style="
            background:#ffffff;
            border:1px solid #fecaca;
            border-left:5px solid #dc2626;
            border-radius:8px;
            margin-bottom:16px;
            overflow:hidden;
        ">

            <div style="
                background:#fef2f2;
                padding:13px 16px;
            ">
                <div style="
                    font-size:16px;
                    font-weight:700;
                    color:#991b1b;
                ">
                    🔴 {action}
                    {critical_badge}
                </div>
            </div>

            <div style="padding:16px;">

                <table
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    style="
                        font-size:13px;
                        border-collapse:collapse;
                    "
                >

                    <tr>
                        <td style="
                            width:150px;
                            padding:6px 0;
                            font-weight:700;
                            color:#475569;
                        ">
                            API
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#0f172a;
                            font-family:monospace;
                        ">
                            {_safe(method)}
                            {_safe(endpoint)}
                        </td>
                    </tr>

                    <tr>
                        <td style="
                            padding:6px 0;
                            font-weight:700;
                            color:#475569;
                        ">
                            Expected Status
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#16a34a;
                            font-weight:700;
                        ">
                            {expected_status}
                        </td>
                    </tr>

                    <tr>
                        <td style="
                            padding:6px 0;
                            font-weight:700;
                            color:#475569;
                        ">
                            Actual Status
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#dc2626;
                            font-weight:700;
                        ">
                            {actual_status}
                        </td>
                    </tr>

                    <tr>
                        <td style="
                            padding:6px 0;
                            font-weight:700;
                            color:#475569;
                        ">
                            Response Time
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#0f172a;
                        ">
                            {duration}
                        </td>
                    </tr>

                    <tr>
                        <td style="
                            padding:6px 0;
                            font-weight:700;
                            color:#475569;
                        ">
                            SLA
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#0f172a;
                        ">
                            {sla}
                        </td>
                    </tr>

                    <tr>
                        <td style="
                            padding:6px 0;
                            font-weight:700;
                            color:#475569;
                        ">
                            API Message
                        </td>

                        <td style="
                            padding:6px 0;
                            color:#0f172a;
                        ">
                            {api_message}
                        </td>
                    </tr>

                </table>

                <div style="
                    margin-top:15px;
                    background:#f8fafc;
                    border:1px solid #e2e8f0;
                    border-radius:6px;
                    padding:12px;
                ">

                    <div style="
                        font-size:12px;
                        font-weight:700;
                        color:#475569;
                        margin-bottom:6px;
                    ">
                        🔎 Diagnostic
                    </div>

                    <div style="
                        font-family:Consolas,Monaco,monospace;
                        font-size:11px;
                        line-height:1.5;
                        color:#334155;
                        word-break:break-word;
                    ">
                        {_safe(error or api_message)}
                    </div>

                </div>

            </div>
        </div>
        """

    return f"""
    <div style="margin-bottom:20px;">

        <div style="
            font-size:18px;
            font-weight:700;
            color:#0f172a;
            margin-bottom:12px;
        ">
            🔴 API Failure Details
        </div>

        {cards}

    </div>
    """


# ============================================================
# MODULE CATEGORISATION
# ============================================================

_MODULE_ORDER = [
    "Authentication",
    "Employee Self-Service",
    "HR Management",
    "Onboarding",
    "Payroll",
    "Ticketing",
    "Notifications",
    "Org Hierarchy",
    "RBAC & Settings",
    "Master Data",
]

_MODULE_EMOJI = {
    "Authentication": "🔐",
    "Employee Self-Service": "👤",
    "HR Management": "🏢",
    "Onboarding": "📋",
    "Payroll": "💰",
    "Ticketing": "🎫",
    "Notifications": "🔔",
    "Org Hierarchy": "🌳",
    "RBAC & Settings": "⚙️",
    "Master Data": "🗂️",
}


# ============================================================
# PATH BASED MODULE FALLBACK
# ============================================================

_PATH_MODULE_RULES = [

    ("/api/auth/", "Authentication", "Login"),

    ("/api/me/team", "Employee Self-Service", "Team"),
    ("/api/me/organisation", "Employee Self-Service", "Org Chart"),
    ("/api/me/notifications", "Employee Self-Service", "Notifications"),
    ("/api/me/notification", "Employee Self-Service", "Notifications"),
    ("/api/me/announcements", "Employee Self-Service", "Announcements"),
    ("/api/me/dashboard", "Employee Self-Service", "Dashboard"),
    ("/api/me/leave", "Employee Self-Service", "Leave"),
    ("/api/me/fetch-all", "Employee Self-Service", "Leave"),
    ("/api/me/attendance", "Employee Self-Service", "Attendance"),
    ("/api/me/users", "Employee Self-Service", "Profile"),
    ("/api/me/permissions", "Employee Self-Service", "Profile"),
    ("/api/me/payslips", "Employee Self-Service", "Payslips"),
    ("/api/me/", "Employee Self-Service", "Profile"),

    ("/api/hr/dashboard", "HR Management", "Dashboard"),
    ("/api/hr/users", "HR Management", "Users"),
    ("/api/hr/attendance", "HR Management", "Attendance"),
    ("/api/hr/employees", "HR Management", "Attendance"),
    ("/api/hr/leave", "HR Management", "Leave"),
    ("/api/hr/fetch-all", "HR Management", "Leave"),
    ("/api/hr/hr-employee", "HR Management", "Leave"),
    ("/api/hr/announcements", "HR Management", "Announcements"),
    ("/api/hr/announcement", "HR Management", "Announcements"),
    ("/api/hr/offers", "HR Management", "Onboarding"),
    ("/api/hr/onboarding", "HR Management", "Onboarding"),
    ("/api/hr/employee-holiday", "HR Management", "Holiday"),
    ("/api/hr/employee-weekly", "HR Management", "Weekly Off"),
    ("/api/hr/payslips", "Employee Self-Service", "Payslips"),
    ("/api/hr/", "HR Management", "Users"),

    ("/api/onboarding/", "Onboarding", "Meta"),

    ("/api/admin/payroll/pf", "Payroll", "PF Config"),
    ("/api/admin/payroll/esi", "Payroll", "ESI Config"),
    ("/api/admin/payroll/pt", "Payroll", "PT Slabs"),
    ("/api/admin/payroll/lwf", "Payroll", "LWF Config"),
    ("/api/admin/payroll/grat", "Payroll", "Gratuity Config"),
    ("/api/admin/payroll/tax", "Payroll", "Tax Config"),
    ("/api/admin/payroll/cal", "Payroll", "Payroll Calendar"),
    ("/api/admin/payroll/runs", "Payroll", "Payroll Runs"),
    ("/api/admin/payroll/conf", "Payroll", "Config"),
    ("/api/admin/payroll/", "Payroll", "Payroll Runs"),

    ("/api/admin/employees", "Payroll", "Employee Statutory"),

    ("/api/admin/salary", "Master Data", "Salary Structure"),
    ("/api/admin/pay-component", "Master Data", "Pay Components"),
    ("/api/admin/pay-range", "Master Data", "Pay Range"),
    ("/api/admin/pay-grade", "Master Data", "Pay Grade"),
    ("/api/admin/cost-center", "Master Data", "Cost Center"),
    ("/api/admin/job-title", "Master Data", "Job Title"),
    ("/api/admin/sub-function", "Master Data", "Sub Function"),
    ("/api/admin/functions", "Master Data", "Function"),
    ("/api/admin/work-location", "Master Data", "Work Location"),
    ("/api/admin/geozones", "Master Data", "Geo Zones"),
    ("/api/admin/legal-entit", "Master Data", "Legal Entity"),
    ("/api/admin/hierarchy", "Master Data", "Hierarchy Levels"),
    ("/api/admin/attendance-de", "Master Data", "Attendance Default"),
    ("/api/admin/attendance-so", "Master Data", "Attendance Source"),
    ("/api/admin/attendance-po", "Master Data", "Attendance Policy"),
    ("/api/admin/attendance", "Master Data", "Attendance Default"),
    ("/api/admin/break-policy", "Master Data", "Break Policy"),
    ("/api/admin/shifts", "Master Data", "Shifts"),
    ("/api/admin/work-mode", "Master Data", "Work Mode"),
    ("/api/admin/ip-address", "Master Data", "IP Address"),
    ("/api/admin/master-option", "Master Data", "Master Options"),
    ("/api/admin/financial-year", "Master Data", "Financial Year"),
    ("/api/admin/comp-off", "Master Data", "Comp Off Requests"),
    ("/api/admin/optional-holi", "Master Data", "Optional Holiday"),
    ("/api/admin/leave-approval", "Master Data", "Leave Approval Workflow"),
    ("/api/admin/holiday-group", "Master Data", "Holiday Group"),
    ("/api/admin/leave-balance", "Master Data", "Leave Balance Ledger"),
    ("/api/admin/policy-group", "Master Data", "Leave Policy Group"),
    ("/api/admin/leave-types", "Master Data", "Leave Types"),

    ("/api/admin/ticketing/wor", "Ticketing", "Workflows"),
    ("/api/admin/ticketing/", "Ticketing", "Admin Tickets"),

    ("/api/admin/notifications", "Notifications", "Events"),

    ("/api/admin/permissions", "RBAC & Settings", "Permissions"),
    ("/api/admin/roles", "RBAC & Settings", "Roles"),
    ("/api/admin/settings/emp", "RBAC & Settings", "Employee Code"),
    ("/api/admin/settings/time", "RBAC & Settings", "Timezone"),
    ("/api/admin/settings/ui", "RBAC & Settings", "UI Color"),
    ("/api/admin/settings/hr", "RBAC & Settings", "HR Defaults"),

    ("/api/ticketing/pending", "Ticketing", "Pending Approvals"),
    ("/api/ticketing/", "Ticketing", "Tickets"),
    ("/admin/ticketing/", "Ticketing", "Ticket Types"),

    ("/api/hr/tax-declaration", "Payroll", "Tax Declaration"),
]


def _infer_module_submodule(result):
    """
    Return (module, submodule) for a result dict.

    Priority:
        1. module/submodule explicitly supplied by runner
        2. endpoint/path based fallback
        3. Other / Uncategorised
    """

    module = result.get("module")
    submodule = result.get("submodule")

    if module and submodule:
        return module, submodule

    path = result.get(
        "endpoint",
        result.get("path", ""),
    )

    for prefix, mod, sub in _PATH_MODULE_RULES:
        if path.startswith(prefix):
            return mod, sub

    return "Other", "Uncategorised"


def _group_results(results):
    """
    Returns:

        OrderedDict(
            {
                module: {
                    submodule: [result, ...]
                }
            }
        )

    Modules are displayed in _MODULE_ORDER.
    Unknown modules are appended at the end.
    """

    grouped = {}

    for result in results:
        module, submodule = _infer_module_submodule(result)

        grouped.setdefault(
            module,
            {},
        ).setdefault(
            submodule,
            [],
        ).append(result)

    ordered = OrderedDict()

    for module in _MODULE_ORDER:
        if module in grouped:
            ordered[module] = grouped.pop(module)

    for module, submodules in grouped.items():
        ordered[module] = submodules

    return ordered


# ============================================================
# MODULE STAT GRID
# ============================================================

def _build_module_stat_grid(results):
    """
    Compact per-module summary table.
    """

    if not results:
        return ""

    grouped = _group_results(results)

    rows = ""

    for module, submodules in grouped.items():

        all_in_module = [
            result
            for sub in submodules.values()
            for result in sub
        ]

        total = len(all_in_module)

        passed = sum(
            1
            for result in all_in_module
            if result.get("passed", False)
        )

        failed = total - passed

        percentage = (
            round((passed / total) * 100, 1)
            if total
            else 0
        )

        emoji = _MODULE_EMOJI.get(
            module,
            "📦",
        )

        if percentage >= 95:
            pill_bg = "#dcfce7"
            pill_col = "#16a34a"
            pill_text = f"{percentage}% ✅"

        elif percentage >= 75:
            pill_bg = "#fef9c3"
            pill_col = "#b45309"
            pill_text = f"{percentage}% ⚠️"

        else:
            pill_bg = "#fee2e2"
            pill_col = "#dc2626"
            pill_text = f"{percentage}% ❌"

        rows += f"""
        <tr style="border-bottom:1px solid #e2e8f0;">

            <td style="
                padding:10px 12px;
                font-weight:600;
                font-size:13px;
            ">
                {emoji} {_safe(module)}
            </td>

            <td style="
                padding:10px 12px;
                text-align:center;
                font-size:13px;
                color:#16a34a;
                font-weight:700;
            ">
                {passed}
            </td>

            <td style="
                padding:10px 12px;
                text-align:center;
                font-size:13px;
                color:{'#dc2626' if failed else '#94a3b8'};
                font-weight:700;
            ">
                {failed}
            </td>

            <td style="
                padding:10px 12px;
                text-align:center;
                font-size:13px;
                color:#64748b;
            ">
                {total}
            </td>

            <td style="padding:10px 12px;">

                <span style="
                    display:inline-block;
                    background:{pill_bg};
                    color:{pill_col};
                    border-radius:12px;
                    padding:3px 10px;
                    font-size:11px;
                    font-weight:700;
                    white-space:nowrap;
                ">
                    {pill_text}
                </span>

            </td>

        </tr>
        """

    return f"""
    <div style="margin-bottom:24px;">

        <div style="
            font-size:18px;
            font-weight:700;
            color:#0f172a;
            margin-bottom:12px;
        ">
            🗺️ Module Health Summary
        </div>

        <div style="
            border:1px solid #e2e8f0;
            border-radius:10px;
            overflow:hidden;
        ">

            <table
                width="100%"
                cellpadding="0"
                cellspacing="0"
                style="
                    border-collapse:collapse;
                    font-family:Arial,sans-serif;
                "
            >

                <thead>

                    <tr style="background:#f1f5f9;">

                        <th
                            align="left"
                            style="
                                padding:10px 12px;
                                font-size:12px;
                                color:#475569;
                            "
                        >
                            Module
                        </th>

                        <th
                            align="center"
                            style="
                                padding:10px 12px;
                                font-size:12px;
                                color:#16a34a;
                            "
                        >
                            Passed
                        </th>

                        <th
                            align="center"
                            style="
                                padding:10px 12px;
                                font-size:12px;
                                color:#dc2626;
                            "
                        >
                            Failed
                        </th>

                        <th
                            align="center"
                            style="
                                padding:10px 12px;
                                font-size:12px;
                                color:#64748b;
                            "
                        >
                            Total
                        </th>

                        <th
                            align="left"
                            style="
                                padding:10px 12px;
                                font-size:12px;
                                color:#475569;
                            "
                        >
                            Health
                        </th>

                    </tr>

                </thead>

                <tbody>
                    {rows}
                </tbody>

            </table>

        </div>
    </div>
    """


# ============================================================
# CATEGORISED API DETAIL
# ============================================================

def _build_categorized_summary(results):
    """
    Renders module cards with submodule endpoint breakdown.
    """

    if not results:
        return ""

    grouped = _group_results(results)

    module_cards = ""

    for module, submodules in grouped.items():

        all_in_module = [
            result
            for sub in submodules.values()
            for result in sub
        ]

        total_module = len(all_in_module)

        passed_module = sum(
            1
            for result in all_in_module
            if result.get("passed", False)
        )

        failed_module = total_module - passed_module

        emoji = _MODULE_EMOJI.get(
            module,
            "📦",
        )

        if failed_module == 0:
            header_bg = "#f0fdf4"
            header_border = "#86efac"
            header_color = "#166534"
            stat_pill_bg = "#dcfce7"
            stat_pill_color = "#16a34a"

        elif failed_module < total_module * 0.3:
            header_bg = "#fffbeb"
            header_border = "#fde68a"
            header_color = "#92400e"
            stat_pill_bg = "#fef3c7"
            stat_pill_color = "#b45309"

        else:
            header_bg = "#fef2f2"
            header_border = "#fca5a5"
            header_color = "#991b1b"
            stat_pill_bg = "#fee2e2"
            stat_pill_color = "#dc2626"

        submodule_sections = ""

        for submodule, sub_results in sorted(
            submodules.items()
        ):

            sub_total = len(sub_results)

            sub_passed = sum(
                1
                for result in sub_results
                if result.get("passed", False)
            )

            sub_failed = sub_total - sub_passed

            sub_color = (
                "#16a34a"
                if sub_failed == 0
                else "#dc2626"
            )

            endpoint_rows = ""

            for result in sub_results:

                passed = result.get(
                    "passed",
                    False,
                )

                status_color = _status_color(
                    passed
                )

                status_label = _status_label(
                    passed
                )

                action = _safe(
                    result.get(
                        "action",
                        result.get(
                            "name",
                            "Unknown",
                        ),
                    )
                )

                method = _safe(
                    result.get("method", "")
                )

                endpoint_url = _safe(
                    result.get("endpoint", "")
                )

                status_code = _format_status(
                    result.get("status_code")
                )

                duration = _format_duration(
                    result.get("elapsed_ms")
                )

                sla_ms = result.get("sla_ms")

                elapsed_ms = result.get(
                    "elapsed_ms"
                )

                sla_breach = (
                    sla_ms is not None
                    and elapsed_ms is not None
                    and elapsed_ms > sla_ms
                )

                critical = result.get(
                    "critical",
                    False,
                )

                critical_badge = ""

                if critical:
                    critical_badge = """
                    <span style="
                        display:inline-block;
                        background:#dc2626;
                        color:#fff;
                        font-size:9px;
                        font-weight:700;
                        padding:1px 6px;
                        border-radius:8px;
                        margin-left:5px;
                        vertical-align:middle;
                    ">
                        CRITICAL
                    </span>
                    """

                sla_badge = ""

                if sla_breach:
                    sla_badge = """
                    <span style="
                        display:inline-block;
                        background:#fef3c7;
                        color:#92400e;
                        font-size:9px;
                        font-weight:700;
                        padding:1px 6px;
                        border-radius:8px;
                        margin-left:4px;
                        vertical-align:middle;
                    ">
                        SLA BREACH
                    </span>
                    """

                endpoint_rows += f"""
                <tr style="
                    background:
                    {'#fef2f2' if not passed else '#ffffff'};
                ">

                    <td style="
                        padding:8px 10px;
                        border-bottom:1px solid #f1f5f9;
                        font-size:12px;
                        font-weight:600;
                        color:#0f172a;
                    ">
                        {action}
                        {critical_badge}
                    </td>

                    <td style="
                        padding:8px 10px;
                        border-bottom:1px solid #f1f5f9;
                        font-family:monospace;
                        font-size:10px;
                        color:#475569;
                    ">
                        <span style="
                            background:#e0f2fe;
                            color:#0369a1;
                            padding:1px 6px;
                            border-radius:4px;
                            font-weight:700;
                        ">
                            {method}
                        </span>
                    </td>

                    <td style="
                        padding:8px 10px;
                        border-bottom:1px solid #f1f5f9;
                        font-family:monospace;
                        font-size:10px;
                        color:#64748b;
                        word-break:break-all;
                    ">
                        {endpoint_url}
                    </td>

                    <td style="
                        padding:8px 10px;
                        border-bottom:1px solid #f1f5f9;
                        font-size:11px;
                        font-weight:700;
                        color:#475569;
                        text-align:center;
                    ">
                        {status_code}
                    </td>

                    <td style="
                        padding:8px 10px;
                        border-bottom:1px solid #f1f5f9;
                        font-size:11px;
                        color:#64748b;
                        white-space:nowrap;
                    ">
                        {duration}
                        {sla_badge}
                    </td>

                    <td style="
                        padding:8px 10px;
                        border-bottom:1px solid #f1f5f9;
                        font-size:11px;
                        font-weight:700;
                        color:{status_color};
                        white-space:nowrap;
                    ">
                        {status_label}
                    </td>

                </tr>
                """

            submodule_sections += f"""
            <div style="margin-bottom:6px;">

                <div style="
                    background:#f8fafc;
                    border-left:4px solid {sub_color};
                    padding:8px 14px;
                ">

                    <span style="
                        font-size:12px;
                        font-weight:700;
                        color:#334155;
                    ">
                        ↳ {_safe(submodule)}
                    </span>

                    <span style="
                        font-size:11px;
                        color:#64748b;
                        margin-left:10px;
                    ">
                        {sub_passed}/{sub_total}
                        {
                            '✅'
                            if sub_failed == 0
                            else f'— {sub_failed} failed ❌'
                        }
                    </span>

                </div>

                <table
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                    style="
                        border-collapse:collapse;
                        font-family:Arial,sans-serif;
                    "
                >

                    <thead>

                        <tr style="
                            background:#f8fafc;
                            border-bottom:1px solid #e2e8f0;
                        ">

                            <th
                                align="left"
                                style="
                                    padding:6px 10px;
                                    font-size:10px;
                                    color:#94a3b8;
                                "
                            >
                                API
                            </th>

                            <th
                                align="left"
                                style="
                                    padding:6px 10px;
                                    font-size:10px;
                                    color:#94a3b8;
                                "
                            >
                                Method
                            </th>

                            <th
                                align="left"
                                style="
                                    padding:6px 10px;
                                    font-size:10px;
                                    color:#94a3b8;
                                "
                            >
                                Endpoint
                            </th>

                            <th
                                align="center"
                                style="
                                    padding:6px 10px;
                                    font-size:10px;
                                    color:#94a3b8;
                                "
                            >
                                HTTP
                            </th>

                            <th
                                align="left"
                                style="
                                    padding:6px 10px;
                                    font-size:10px;
                                    color:#94a3b8;
                                "
                            >
                                Time
                            </th>

                            <th
                                align="left"
                                style="
                                    padding:6px 10px;
                                    font-size:10px;
                                    color:#94a3b8;
                                "
                            >
                                Status
                            </th>

                        </tr>

                    </thead>

                    <tbody>
                        {endpoint_rows}
                    </tbody>

                </table>

            </div>
            """

        module_cards += f"""
        <div style="
            border:1px solid {header_border};
            border-radius:10px;
            margin-bottom:20px;
            overflow:hidden;
        ">

            <div style="
                background:{header_bg};
                padding:14px 18px;
                border-bottom:1px solid {header_border};
            ">

                <table
                    width="100%"
                    cellpadding="0"
                    cellspacing="0"
                >

                    <tr>

                        <td>

                            <div style="
                                font-size:16px;
                                font-weight:700;
                                color:{header_color};
                            ">
                                {emoji} {_safe(module)}
                            </div>

                            <div style="
                                font-size:11px;
                                color:#64748b;
                                margin-top:3px;
                            ">
                                {len(submodules)}
                                submodule
                                {
                                    's'
                                    if len(submodules) != 1
                                    else ''
                                }
                                ·
                                {total_module}
                                endpoint
                                {
                                    's'
                                    if total_module != 1
                                    else ''
                                }
                            </div>

                        </td>

                        <td align="right">

                            <span style="
                                display:inline-block;
                                background:{stat_pill_bg};
                                color:{stat_pill_color};
                                border-radius:14px;
                                padding:4px 14px;
                                font-size:13px;
                                font-weight:700;
                                white-space:nowrap;
                            ">

                                {passed_module}/{total_module}
                                passed

                                {
                                    '✅'
                                    if failed_module == 0
                                    else f' · {failed_module} ❌'
                                }

                            </span>

                        </td>

                    </tr>

                </table>

            </div>

            <div style="padding:14px 18px;">
                {submodule_sections}
            </div>

        </div>
        """

    return f"""
    <div style="margin-top:25px;">

        <div style="
            font-size:18px;
            font-weight:700;
            color:#0f172a;
            margin-bottom:14px;
        ">
            📊 API Health — Module Breakdown
        </div>

        {module_cards}

    </div>
    """


# ============================================================
# API OVERVIEW SUMMARY
# ============================================================

def _build_api_summary(results):
    """
    Renders the complete API Overview section.
    """

    if not results:
        return """
        <div style="
            background:#f8fafc;
            border:1px solid #e2e8f0;
            border-radius:8px;
            padding:20px;
            text-align:center;
            color:#64748b;
            font-size:14px;
        ">
            No API results available.
        </div>
        """

    stat_grid = _build_module_stat_grid(
        results
    )

    categorized_detail = _build_categorized_summary(
        results
    )

    return f"""
    <div style="margin-bottom:20px;">

        <div style="
            font-size:20px;
            font-weight:700;
            color:#0f172a;
            margin-bottom:16px;
            border-bottom:2px solid #e2e8f0;
            padding-bottom:10px;
        ">
            📡 API Overview
        </div>

        {stat_grid}

        {categorized_detail}

    </div>
    """


# ============================================================
# COMPLETE EMAIL
# ============================================================

def build_health_email(
    summary,
    results,
    environment=ENVIRONMENT,
):
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)

    sla_breaches = summary.get(
        "sla_breaches",
        [],
    )

    critical_failures = summary.get(
        "critical_failed",
        [],
    )

    percentage = _get_health_percentage(
        summary
    )

    overall = _overall_status(
        summary
    )

    run_time = summary.get(
        "run_time",
        datetime.now().isoformat(
            timespec="seconds"
        ),
    )

    return f"""
<!DOCTYPE html>

<html>

<head>

    <meta charset="UTF-8">

    <title>
        HRMS API Health Monitor
    </title>

</head>

<body style="
    margin:0;
    padding:0;
    background:#f1f5f9;
    font-family:Arial,Helvetica,sans-serif;
    color:#0f172a;
">

<table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    style="
        background:#f1f5f9;
        padding:25px 10px;
    "
>

<tr>

<td align="center">

<table
    width="900"
    cellpadding="0"
    cellspacing="0"
    style="
        max-width:900px;
        width:100%;
        background:#ffffff;
        border-radius:12px;
        overflow:hidden;
    "
>

<!-- ======================================================
     HEADER
====================================================== -->

<tr>

<td style="
    background:#0f172a;
    padding:25px 30px;
">

    <div style="
        color:#ffffff;
        font-size:25px;
        font-weight:700;
    ">
        HRMS API Health Monitor
    </div>

    <div style="
        color:#cbd5e1;
        font-size:13px;
        margin-top:6px;
    ">
        Automated API Reliability &amp; Availability Report
    </div>

</td>

</tr>


<!-- ======================================================
     STATUS
====================================================== -->

<tr>

<td style="
    padding:25px 30px 15px 30px;
">

<div style="
    background:{overall["color"]}15;
    border:1px solid {overall["color"]}40;
    border-radius:10px;
    padding:20px;
    text-align:center;
">

    <div style="
        font-size:30px;
        font-weight:800;
        color:{overall["color"]};
    ">
        {overall["emoji"]}
        {percentage}%
    </div>

    <div style="
        margin-top:5px;
        font-size:14px;
        font-weight:700;
        color:{overall["color"]};
        letter-spacing:0.5px;
    ">
        {overall["label"]}
    </div>

    {_progress_bar(percentage)}

</div>

</td>

</tr>


<!-- ======================================================
     METRICS
====================================================== -->

<tr>

<td style="
    padding:5px 30px 20px 30px;
">

<table
    width="100%"
    cellpadding="0"
    cellspacing="8"
>

<tr>

<td
    width="25%"
    style="
        background:#f8fafc;
        border-radius:8px;
        padding:18px;
        text-align:center;
    "
>

    <div style="
        font-size:28px;
        font-weight:800;
    ">
        {total}
    </div>

    <div style="
        color:#64748b;
        font-size:12px;
        margin-top:4px;
    ">
        TOTAL APIs
    </div>

</td>


<td
    width="25%"
    style="
        background:#f0fdf4;
        border-radius:8px;
        padding:18px;
        text-align:center;
    "
>

    <div style="
        font-size:28px;
        font-weight:800;
        color:#16a34a;
    ">
        {passed}
    </div>

    <div style="
        color:#166534;
        font-size:12px;
        margin-top:4px;
    ">
        HEALTHY
    </div>

</td>


<td
    width="25%"
    style="
        background:#fef2f2;
        border-radius:8px;
        padding:18px;
        text-align:center;
    "
>

    <div style="
        font-size:28px;
        font-weight:800;
        color:#dc2626;
    ">
        {failed}
    </div>

    <div style="
        color:#991b1b;
        font-size:12px;
        margin-top:4px;
    ">
        FAILED
    </div>

</td>


<td
    width="25%"
    style="
        background:#fffbeb;
        border-radius:8px;
        padding:18px;
        text-align:center;
    "
>

    <div style="
        font-size:28px;
        font-weight:800;
        color:#d97706;
    ">
        {len(sla_breaches)}
    </div>

    <div style="
        color:#92400e;
        font-size:12px;
        margin-top:4px;
    ">
        SLA BREACHES
    </div>

</td>

</tr>

</table>

</td>

</tr>


<!-- ======================================================
     RUN INFORMATION
====================================================== -->

<tr>

<td style="
    padding:0 30px 20px 30px;
">

<div style="
    background:#f8fafc;
    border-radius:8px;
    padding:16px;
">

<div style="
    font-size:15px;
    font-weight:700;
    margin-bottom:10px;
">
    📋 Run Information
</div>

<table
    width="100%"
    cellpadding="4"
    cellspacing="0"
    style="font-size:13px;"
>

<tr>

<td style="
    color:#64748b;
    width:140px;
">
    Environment
</td>

<td style="font-weight:700;">
    {_safe(environment)}
</td>

</tr>


<tr>

<td style="color:#64748b;">
    Run Time
</td>

<td>
    {_safe(run_time)}
</td>

</tr>


<tr>

<td style="color:#64748b;">
    Critical Failures
</td>

<td style="
    font-weight:700;
    color:
    {'#dc2626' if critical_failures else '#16a34a'};
">
    {len(critical_failures)}
</td>

</tr>


<tr>

<td style="color:#64748b;">
    SLA Breaches
</td>

<td style="
    font-weight:700;
    color:
    {'#d97706' if sla_breaches else '#16a34a'};
">
    {len(sla_breaches)}
</td>

</tr>

</table>

</div>

</td>

</tr>


<!-- ======================================================
     CRITICAL FAILURES
====================================================== -->

<tr>

<td style="padding:0 30px;">

    {_build_critical_failures(summary)}

</td>

</tr>


<!-- ======================================================
     FAILURE DETAILS
====================================================== -->

<tr>

<td style="padding:0 30px;">

    {_build_failure_details(results)}

</td>

</tr>


<!-- ======================================================
     API OVERVIEW
====================================================== -->

<tr>

<td style="padding:0 30px 30px 30px;">

    {_build_api_summary(results)}

</td>

</tr>


<!-- ======================================================
     FOOTER
====================================================== -->

<tr>

<td style="
    background:#0f172a;
    padding:20px 30px;
    text-align:center;
">

<div style="
    color:#ffffff;
    font-size:13px;
    font-weight:700;
">
    HRMS API Health Suite
</div>

<div style="
    color:#94a3b8;
    font-size:11px;
    margin-top:6px;
">
    Automated monitoring • API availability • Response time • SLA
</div>

<div style="
    color:#64748b;
    font-size:10px;
    margin-top:10px;
">
    This is an automated health monitoring notification.
</div>

</td>

</tr>


</table>

</td>

</tr>

</table>

</body>

</html>
"""


# ============================================================
# ATTACHMENT
# ============================================================

def _prepare_attachment(
    file_path: str | None,
    label: str,
):
    """
    Reads a local file and returns a Resend-compatible
    base64 attachment dictionary.
    """

    if not file_path:
        print(
            f"[health-suite] WARNING: "
            f"No {label} path was received."
        )
        return None

    absolute_path = os.path.abspath(
        file_path
    )

    if not os.path.isfile(absolute_path):
        print(
            f"[health-suite] WARNING: "
            f"{label} does not exist: "
            f"{absolute_path}"
        )
        return None

    try:

        with open(
            absolute_path,
            "rb",
        ) as file:

            file_bytes = file.read()

        encoded = base64.b64encode(
            file_bytes
        ).decode("utf-8")

        filename = os.path.basename(
            absolute_path
        )

        print(
            f"[health-suite] Preparing "
            f"{label} attachment..."
        )

        print(
            f"[health-suite] {label} path: "
            f"{absolute_path}"
        )

        print(
            f"[health-suite] {label} filename: "
            f"{filename}"
        )

        print(
            f"[health-suite] {label} size: "
            f"{len(file_bytes)} bytes"
        )

        return {
            "filename": filename,
            "content": encoded,
        }

    except Exception as exc:

        print(
            f"[health-suite] WARNING: "
            f"Failed to prepare {label}: "
            f"{type(exc).__name__}: {exc}"
        )

        return None


# ============================================================
# SEND EMAIL
# ============================================================

def send_health_email(
    summary,
    results,
    report_path=None,
    summary_path=None,
):
    """
    Send the HRMS API health dashboard using Resend.
    """

    if not RESEND_API_KEY:
        raise RuntimeError(
            "RESEND_API_KEY environment variable "
            "is not configured."
        )

    if not TO_EMAIL:
        raise RuntimeError(
            "HEALTH_MAIL_TO environment variable "
            "is not configured."
        )

    resend.api_key = RESEND_API_KEY

    percentage = _get_health_percentage(
        summary
    )

    overall = _overall_status(
        summary
    )

    subject = (
        f"{overall['emoji']} "
        f"{overall['label']} | "
        f"HRMS API Health | "
        f"{percentage}% Healthy"
    )

    html_body = build_health_email(
        summary=summary,
        results=results,
        environment=ENVIRONMENT,
    )

    params = {
        "from": FROM_EMAIL,
        "to": [TO_EMAIL],
        "subject": subject,
        "html": html_body,
    }

    # ========================================================
    # ATTACHMENTS
    # ========================================================

    attachments = []

    # Excel report
    excel_attachment = _prepare_attachment(
        report_path,
        "Excel report",
    )

    if excel_attachment:
        attachments.append(
            excel_attachment
        )

    # JSON summary
    json_attachment = _prepare_attachment(
        summary_path,
        "JSON summary",
    )

    if json_attachment:
        attachments.append(
            json_attachment
        )

    if attachments:

        params["attachments"] = attachments

        print(
            "[health-suite] "
            f"Total attachments: "
            f"{len(attachments)}"
        )

        for attachment in attachments:
            print(
                "[health-suite] "
                f"Attachment: "
                f"{attachment.get('filename')}"
            )

    else:

        print(
            "[health-suite] WARNING: "
            "No attachments were prepared."
        )

    # ========================================================
    # SEND
    # ========================================================

    print(
        "[health-suite] "
        "Sending health dashboard email..."
    )

    try:

        response = resend.Emails.send(
            params
        )

        print(
            "[health-suite] "
            "Resend email sent successfully."
        )

        print(
            "[health-suite] "
            f"Resend response: {response}"
        )

        return response

    except Exception as exc:

        print(
            "[health-suite] "
            f"Resend email failed: "
            f"{type(exc).__name__}: {exc}"
        )

        raise


# ============================================================
# COMPATIBILITY WRAPPER
# ============================================================

def notify_resend(
    summary,
    results,
    report_path=None,
    summary_path=None,
):
    """
    Backward-compatible wrapper.

    Existing callers can continue using:

        notify_resend(
            summary,
            results,
            report_path=...,
            summary_path=...,
        )
    """

    try:

        return send_health_email(
            summary=summary,
            results=results,
            report_path=report_path,
            summary_path=summary_path,
        )

    except Exception as exc:

        print(
            "[health-suite] "
            f"Resend notification failed: "
            f"{type(exc).__name__}: {exc}"
        )

        return None