"""
Sends the health-check run results to an n8n Webhook instead of emailing
directly via SMTP (blocked by org network policy).

n8n receives this POST and handles email (via Gmail/Outlook API — HTTPS,
not SMTP) and Slack alerting on its side. This script's only job is to
package and deliver the data reliably.

Config via env vars:
    N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/api-health-report
    N8N_WEBHOOK_ENABLED=true

Payload sent to n8n:
{
    "summary": { total, passed, failed, pass_rate, critical_failed,
                 sla_breaches, run_time },
    "report_filename": "api_health_report.xlsx",
    "report_base64": "<base64-encoded excel file>",
    "failures": [ { "endpoint": ..., "action": ..., "status_code": ...,
                     "error": ... }, ... ]
}
"""

import os
import base64
import requests


def notify_n8n(summary: dict, report_path: str, failures: list = None):
    if os.getenv("N8N_WEBHOOK_ENABLED", "false").lower() != "true":
        print("[health-suite] N8N_WEBHOOK_ENABLED not true — skipping n8n notification.")
        return

    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    if not webhook_url:
        print("[health-suite] N8N_WEBHOOK_URL not set — skipping n8n notification.")
        return

    report_base64 = ""
    report_filename = ""
    if report_path and os.path.exists(report_path):
        with open(report_path, "rb") as f:
            report_base64 = base64.b64encode(f.read()).decode("utf-8")
        report_filename = os.path.basename(report_path)
    else:
        print(f"[health-suite] Warning: report file not found at {report_path}, "
              f"sending notification without attachment.")

    payload = {
        "summary": summary,
        "report_filename": report_filename,
        "report_base64": report_base64,
        "failures": failures or [],
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=60)
        if resp.status_code == 200:
            print(f"[health-suite] n8n notified successfully (status {resp.status_code}).")
        else:
            print(f"[health-suite] n8n webhook returned unexpected status "
                  f"{resp.status_code}: {resp.text[:300]}")
    except requests.RequestException as e:
        print(f"[health-suite] Failed to notify n8n: {type(e).__name__}: {e}")
