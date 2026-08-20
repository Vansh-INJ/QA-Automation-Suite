"""
Sends a failure alert (Slack incoming webhook by default) after a health run.
Silent when everything passes — you should only be interrupted when
something's actually broken.

Wire this into a session finish hook (see test/health/conftest.py's
health_reporter fixture teardown, or a pytest_sessionfinish hook) once
you have a webhook URL. Left as a standalone callable for now so it can
also be invoked from a CI step independent of pytest internals.
"""

import os
import requests


def notify_if_failed(summary: dict, report_path: str = ""):
    """
    summary: the dict returned by HealthReporter.summary
    """
    if summary["failed"] == 0:
        return  # all green, stay quiet

    webhook_url = os.getenv("HEALTH_SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("[health-suite] Failures detected but HEALTH_SLACK_WEBHOOK_URL not set; skipping alert.")
        return

    lines = [
        f"*API Health Check — {summary['passed']}/{summary['total']} passed "
        f"({summary['pass_rate']}%)*",
    ]
    if summary["critical_failed"]:
        lines.append(f":rotating_light: Critical endpoint(s) down: {', '.join(summary['critical_failed'])}")
    lines.append(f"Run time: {summary['run_time']}")
    if report_path:
        lines.append(f"Report: `{report_path}` (attach via CI artifact link)")

    payload = {"text": "\n".join(lines)}
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except requests.RequestException as e:
        print(f"[health-suite] Failed to send Slack alert: {e}")
