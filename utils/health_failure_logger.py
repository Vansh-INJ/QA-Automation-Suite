"""
Writes one detailed file per FAILED endpoint into <run_folder>/api_failures/,
capturing the full request (method, URL, params, headers) and full response
(status, headers, body) — so a failure can be diagnosed without re-running
anything.

File naming: <endpoint_name>_<HHMMSS>.txt  (timestamp avoids collisions if
the same endpoint fails more than once conceptually, e.g. re-runs same day)
"""

import os
import json
from datetime import datetime


def _mask_sensitive_headers(headers: dict) -> dict:
    """Never write raw bearer tokens/secrets into a file on disk."""
    masked = {}
    for k, v in (headers or {}).items():
        if k.lower() in ("authorization", "cookie", "set-cookie"):
            masked[k] = (v[:15] + "...MASKED") if isinstance(v, str) else "MASKED"
        else:
            masked[k] = v
    return masked


class HealthFailureLogger:
    def __init__(self, run_folder: str):
        self.failures_dir = os.path.join(run_folder, "api_failures")
        os.makedirs(self.failures_dir, exist_ok=True)

    def log_failure(
        self,
        name: str,
        method: str,
        url: str,
        request_params: dict,
        request_headers: dict,
        status_code: int,
        response_headers: dict,
        response_body: str,
        error: str = "",
    ):
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{name}_{timestamp}.txt"
        filepath = os.path.join(self.failures_dir, filename)

        # Try to pretty-print JSON body; fall back to raw text if it isn't JSON
        try:
            parsed = json.loads(response_body)
            body_display = json.dumps(parsed, indent=2)
        except (ValueError, TypeError):
            body_display = response_body

        lines = [
            "=" * 80,
            f"ENDPOINT: {name}",
            f"TIMESTAMP: {datetime.now().isoformat(timespec='seconds')}",
            "=" * 80,
            "",
            "--- REQUEST ---",
            f"Method: {method}",
            f"URL: {url}",
            f"Params: {json.dumps(request_params or {}, indent=2)}",
            f"Headers: {json.dumps(_mask_sensitive_headers(request_headers), indent=2)}",
            "",
            "--- RESPONSE ---",
            f"Status Code: {status_code}",
            f"Headers: {json.dumps(dict(response_headers or {}), indent=2)}",
            "Body:",
            body_display,
            "",
        ]
        if error:
            lines += ["--- ERROR ---", error, ""]

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return filepath
