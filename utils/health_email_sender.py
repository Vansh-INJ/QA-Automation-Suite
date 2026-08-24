"""
Sends the health dashboard email directly via Resend's HTTP API.
Pure HTTPS POST — no SMTP port involved anywhere, no n8n hop needed.

Setup:
    1. Sign up at https://resend.com, verify your sending domain
    2. Create an API key
    3. Set in .env:
        EMAIL_PROVIDER=resend
        RESEND_API_KEY=re_xxxxxxxxxxxx
        HEALTH_MAIL_FROM=alerts@yourverifieddomain.com
        HEALTH_MAIL_TO=you@yourcompany.com,teammate@yourcompany.com

If you'd rather use Brevo instead, set EMAIL_PROVIDER=brevo and
BREVO_API_KEY — see send_via_brevo() below, same interface either way.
"""

import os
import requests


def send_via_resend(subject: str, html_body: str, from_addr: str, to_addrs: list) -> bool:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("[health-suite] RESEND_API_KEY not set — skipping email.")
        return False

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": from_addr,
            "to": to_addrs,
            "subject": subject,
            "html": html_body,
        },
        timeout=30,
    )

    if resp.status_code in (200, 201):
        print(f"[health-suite] Email sent via Resend to: {', '.join(to_addrs)}")
        return True
    else:
        print(f"[health-suite] Resend API error {resp.status_code}: {resp.text[:300]}")
        return False


def send_via_brevo(subject: str, html_body: str, from_addr: str, to_addrs: list) -> bool:
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        print("[health-suite] BREVO_API_KEY not set — skipping email.")
        return False

    resp = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "sender": {"email": from_addr},
            "to": [{"email": addr} for addr in to_addrs],
            "subject": subject,
            "htmlContent": html_body,
        },
        timeout=30,
    )

    if resp.status_code in (200, 201):
        print(f"[health-suite] Email sent via Brevo to: {', '.join(to_addrs)}")
        return True
    else:
        print(f"[health-suite] Brevo API error {resp.status_code}: {resp.text[:300]}")
        return False


def send_dashboard_email(subject: str, html_body: str) -> bool:
    provider = os.getenv("EMAIL_PROVIDER", "resend").lower()
    from_addr = os.getenv("HEALTH_MAIL_FROM", "")
    to_raw = os.getenv("HEALTH_MAIL_TO", "")
    to_addrs = [a.strip() for a in to_raw.split(",") if a.strip()]

    if not from_addr or not to_addrs:
        print("[health-suite] HEALTH_MAIL_FROM / HEALTH_MAIL_TO not configured — skipping email.")
        return False

    if provider == "resend":
        return send_via_resend(subject, html_body, from_addr, to_addrs)
    elif provider == "brevo":
        return send_via_brevo(subject, html_body, from_addr, to_addrs)
    else:
        print(f"[health-suite] Unknown EMAIL_PROVIDER='{provider}' — must be 'resend' or 'brevo'.")
        return False
