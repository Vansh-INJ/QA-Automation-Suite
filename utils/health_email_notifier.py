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

import os
import html
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

    return round(
        (passed / total) * 100,
        1,
    )


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

        name = _safe(
            result.get(
                "name",
                "Unknown API",
            )
        )

        action = _safe(
            result.get(
                "action",
                name,
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
                    🔴 {_safe(action)}
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
# API SUMMARY
# ============================================================

def _build_api_summary(results):

    if not results:
        return ""

    rows = ""

    for result in results:

        passed = result.get(
            "passed",
            False,
        )

        status_color = _status_color(
            passed
        )

        status_text = _status_label(
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
            result.get(
                "method",
                "",
            )
        )

        endpoint = _safe(
            result.get(
                "endpoint",
                "",
            )
        )

        status = _format_status(
            result.get("status_code")
        )

        duration = _format_duration(
            result.get("elapsed_ms")
        )

        rows += f"""
        <tr>

            <td style="
                padding:9px;
                border-bottom:1px solid #e2e8f0;
                font-weight:600;
            ">
                {action}
            </td>

            <td style="
                padding:9px;
                border-bottom:1px solid #e2e8f0;
                font-family:monospace;
                font-size:11px;
            ">
                {method}
            </td>

            <td style="
                padding:9px;
                border-bottom:1px solid #e2e8f0;
                font-family:monospace;
                font-size:11px;
            ">
                {endpoint}
            </td>

            <td style="
                padding:9px;
                border-bottom:1px solid #e2e8f0;
                font-weight:700;
            ">
                {status}
            </td>

            <td style="
                padding:9px;
                border-bottom:1px solid #e2e8f0;
            ">
                {duration}
            </td>

            <td style="
                padding:9px;
                border-bottom:1px solid #e2e8f0;
                color:{status_color};
                font-weight:700;
            ">
                {status_text}
            </td>

        </tr>
        """

    return f"""
    <div style="margin-top:25px;">

        <div style="
            font-size:18px;
            font-weight:700;
            color:#0f172a;
            margin-bottom:12px;
        ">
            📊 API Health Overview
        </div>

        <div style="
            overflow-x:auto;
            border:1px solid #e2e8f0;
            border-radius:8px;
        ">

            <table
                width="100%"
                cellpadding="0"
                cellspacing="0"
                style="
                    border-collapse:collapse;
                    font-family:Arial,sans-serif;
                    font-size:12px;
                "
            >

                <thead>

                    <tr style="
                        background:#f1f5f9;
                    ">

                        <th align="left" style="padding:10px;">
                            API
                        </th>

                        <th align="left" style="padding:10px;">
                            Method
                        </th>

                        <th align="left" style="padding:10px;">
                            Endpoint
                        </th>

                        <th align="left" style="padding:10px;">
                            Status
                        </th>

                        <th align="left" style="padding:10px;">
                            Time
                        </th>

                        <th align="left" style="padding:10px;">
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
# COMPLETE EMAIL
# ============================================================

def build_health_email(
    summary,
    results,
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
    <title>HRMS API Health Monitor</title>
</head>

<body style="
    margin:0;
    padding:0;
    background:#f1f5f9;
    font-family:Arial,Helvetica,sans-serif;
    color:#0f172a;
">

<table width="100%"
       cellpadding="0"
       cellspacing="0"
       style="
           background:#f1f5f9;
           padding:25px 10px;
       ">

<tr>

<td align="center">

<table width="900"
       cellpadding="0"
       cellspacing="0"
       style="
           max-width:900px;
           width:100%;
           background:#ffffff;
           border-radius:12px;
           overflow:hidden;
       ">

<!-- HEADER -->

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


<!-- STATUS -->

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


<!-- METRICS -->

<tr>

<td style="
    padding:5px 30px 20px 30px;
">

<table width="100%"
       cellpadding="0"
       cellspacing="8">

<tr>

<td width="25%"
    style="
        background:#f8fafc;
        border-radius:8px;
        padding:18px;
        text-align:center;
    ">

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


<td width="25%"
    style="
        background:#f0fdf4;
        border-radius:8px;
        padding:18px;
        text-align:center;
    ">

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


<td width="25%"
    style="
        background:#fef2f2;
        border-radius:8px;
        padding:18px;
        text-align:center;
    ">

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


<td width="25%"
    style="
        background:#fffbeb;
        border-radius:8px;
        padding:18px;
        text-align:center;
    ">

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


<!-- RUN INFORMATION -->

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

<table width="100%"
       cellpadding="4"
       cellspacing="0"
       style="font-size:13px;">

<tr>

<td style="
    color:#64748b;
    width:140px;
">
    Environment
</td>

<td style="font-weight:700;">
    {_safe(ENVIRONMENT)}
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
    color:{'#dc2626' if critical_failures else '#16a34a'};
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
    color:{'#d97706' if sla_breaches else '#16a34a'};
">
    {len(sla_breaches)}
</td>

</tr>

</table>

</div>

</td>

</tr>


<!-- CRITICAL FAILURES -->

<tr>

<td style="padding:0 30px;">

{_build_critical_failures(summary)}

</td>

</tr>


<!-- FAILURE DETAILS -->

<tr>

<td style="padding:0 30px;">

{_build_failure_details(results)}

</td>

</tr>


<!-- API OVERVIEW -->

<tr>

<td style="padding:0 30px 30px 30px;">

{_build_api_summary(results)}

</td>

</tr>


<!-- FOOTER -->

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
    Prepare a Resend attachment.

    IMPORTANT:
    We deliberately use the local file path instead of manually
    Base64 encoding the file.

    This allows the Resend SDK to handle the attachment.
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

    if not os.path.isfile(
        absolute_path
    ):

        print(
            f"[health-suite] WARNING: "
            f"{label} does not exist: "
            f"{absolute_path}"
        )

        return None

    try:

        file_size = os.path.getsize(
            absolute_path
        )

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
            f"{file_size} bytes"
        )

        return {
            "path": absolute_path,
            "filename": filename,
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
    environment="Development",
    report_path=None,
    summary_path=None,
):

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

    # Excel
    excel_attachment = _prepare_attachment(
        report_path,
        "Excel report",
    )

    if excel_attachment:
        attachments.append(
            excel_attachment
        )

    # JSON
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
            f"[health-suite] "
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