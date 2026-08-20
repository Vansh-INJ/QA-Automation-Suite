"""
Emails the health report (Excel attached) after every run — pass or fail.

Config via env vars (set in .env or CI secrets):
    HEALTH_MAIL_ENABLED=true
    HEALTH_SMTP_HOST=smtp.gmail.com
    HEALTH_SMTP_PORT=587
    HEALTH_SMTP_USERNAME=you@company.com
    HEALTH_SMTP_PASSWORD=app_password_here      # use an app password, not your login password
    HEALTH_MAIL_FROM=you@company.com
    HEALTH_MAIL_TO=you@company.com,teammate@company.com   # comma-separated
    HEALTH_MAIL_SUBJECT_PREFIX=[API Health]      # optional

If HEALTH_MAIL_ENABLED is not "true", this is a silent no-op — safe to
leave the rest unconfigured while you're still setting things up.
"""

import os
import smtplib
from email.message import EmailMessage
from datetime import datetime


def send_health_report_email(summary: dict, report_path: str):
    if os.getenv("HEALTH_MAIL_ENABLED", "false").lower() != "true":
        return

    host = os.getenv("HEALTH_SMTP_HOST")
    port = int(os.getenv("HEALTH_SMTP_PORT", "587"))
    username = os.getenv("HEALTH_SMTP_USERNAME")
    password = os.getenv("HEALTH_SMTP_PASSWORD")
    mail_from = os.getenv("HEALTH_MAIL_FROM", username)
    mail_to_raw = os.getenv("HEALTH_MAIL_TO", "")
    subject_prefix = os.getenv("HEALTH_MAIL_SUBJECT_PREFIX", "[API Health]")

    mail_to = [addr.strip() for addr in mail_to_raw.split(",") if addr.strip()]

    missing = [n for n, v in [
        ("HEALTH_SMTP_HOST", host), ("HEALTH_SMTP_USERNAME", username),
        ("HEALTH_SMTP_PASSWORD", password), ("HEALTH_MAIL_TO", mail_to),
    ] if not v]
    if missing:
        print(f"[health-suite] Mail enabled but missing config: {missing}. Skipping email.")
        return

    status_word = "PASS" if summary["failed"] == 0 else "FAILURES DETECTED"
    subject = (
        f"{subject_prefix} {status_word} — {summary['passed']}/{summary['total']} "
        f"passed ({summary['pass_rate']}%) — {datetime.now().strftime('%d %b %Y %H:%M')}"
    )

    body_lines = [
        f"API Health Check Summary — {summary['run_time']}",
        "",
        f"Total endpoints checked : {summary['total']}",
        f"Passed                  : {summary['passed']}",
        f"Failed                  : {summary['failed']}",
        f"Pass rate               : {summary['pass_rate']}%",
    ]
    if summary["critical_failed"]:
        body_lines.append(f"CRITICAL failures        : {', '.join(summary['critical_failed'])}")
    body_lines += [
        "",
        "Full details are in the attached Excel report.",
        "Individual failure request/response dumps (if any) are in the run's api_failures/ folder.",
    ]

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = ", ".join(mail_to)
    msg.set_content("\n".join(body_lines))

    if report_path and os.path.exists(report_path):
        with open(report_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=os.path.basename(report_path),
            )

    try:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        print(f"[health-suite] Report emailed to: {', '.join(mail_to)}")
    except Exception as e:
        print(f"[health-suite] Failed to send email: {type(e).__name__}: {e}")
