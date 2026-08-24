"""
Reporting for the API Health Suite — v5.

Same as v3's column set and Excel logic, PLUS a write_summary_json() method
so n8n (or anything else) can consume results as structured JSON instead of
having to parse an Excel file.
"""

import os
import json
from datetime import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
except ImportError as e:
    raise ImportError(
        "openpyxl is required for health reporting. Add `openpyxl` to requirements.txt"
    ) from e


PASS_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
FAIL_FILL = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
SLA_WARN_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True)

MASKED_HEADER_KEYS = ("authorization", "cookie", "set-cookie")

import re

_ILLEGAL_CHARACTERS_RE = re.compile(
    r'[\000-\010]|[\013-\014]|[\016-\037]'
)

def _sanitize_for_excel(value):
    """
    Strip control characters openpyxl refuses to write into a cell
    (commonly present in raw backend error dumps / stack traces).
    Leaves non-string values (numbers, None) untouched aside from
    turning None into an empty string for display purposes.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        return value
    return _ILLEGAL_CHARACTERS_RE.sub("", value)

def _mask_headers(headers: dict) -> dict:
    masked = {}
    for k, v in (headers or {}).items():
        if k.lower() in MASKED_HEADER_KEYS:
            masked[k] = (v[:15] + "...MASKED") if isinstance(v, str) else "MASKED"
        else:
            masked[k] = v
    return masked


def _pretty(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return json.dumps(parsed, indent=2)
        except (ValueError, TypeError):
            return value
    return str(value)


class HealthReporter:
    def __init__(self, run_folder: str):
        self.run_folder = run_folder
        self.results = []

    def record(
        self,
        name: str,
        action: str,
        method: str,
        path: str,
        params: dict | None,
        status_code: int | None,
        expected_status: int,
        passed: bool,
        elapsed_ms: float | None,
        sla_ms: int,
        api_message: str = "",
        request_headers: dict | None = None,
        request_payload: dict | None = None,
        response_body=None,
        candidate_name: str = "",
        candidate_email: str = "",
        error: str = "",
        critical: bool = False,
    ):
        sla_status = "N/A"
        if elapsed_ms is not None and sla_ms:
            sla_status = "WITHIN SLA" if elapsed_ms <= sla_ms else "SLA BREACH"

        self.results.append({
            "name": name,
            "candidate_name": candidate_name or "N/A",
            "candidate_email": candidate_email or "N/A",
            "action": action,
            "method": method,
            "endpoint": path,
            "params": params or {},
            "status_code": status_code,
            "expected_status": expected_status,
            "passed": passed,
            "elapsed_ms": elapsed_ms,
            "sla_ms": sla_ms,
            "sla_status": sla_status,
            "api_message": api_message,
            "request_headers": _mask_headers(request_headers),
            "request_payload": request_payload or {},
            "response_body": response_body,
            "screenshot": "N/A (API-only check)",
            "error": error,
            "critical": critical,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })

    @property
    def summary(self) -> dict:
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        sla_breaches = [r["action"] for r in self.results if r["sla_status"] == "SLA BREACH"]
        critical_failed = [r["action"] for r in self.results if r["critical"] and not r["passed"]]
        failed_endpoints = [
            {"name": r["name"], "action": r["action"], "status_code": r["status_code"],
             "expected_status": r["expected_status"], "error": r["error"],
             "api_message": r["api_message"]}
            for r in self.results if not r["passed"]
        ]
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / total) * 100, 1) if total else 0,
            "critical_failed": critical_failed,
            "sla_breaches": sla_breaches,
            "failed_endpoints": failed_endpoints,
            "run_time": datetime.now().isoformat(timespec="seconds"),
        }

    def write_excel(self) -> str:
        wb = Workbook()

        ws = wb.active
        ws.title = "Summary"
        s = self.summary
        rows = [
            ("Run Time", s["run_time"]),
            ("Total Endpoints", s["total"]),
            ("Passed", s["passed"]),
            ("Failed", s["failed"]),
            ("Pass Rate", f"{s['pass_rate']}%"),
            ("Critical Failures", ", ".join(s["critical_failed"]) or "None"),
            ("SLA Breaches", ", ".join(s["sla_breaches"]) or "None"),
        ]
        for i, (label, value) in enumerate(rows, start=1):
            ws.cell(row=i, column=1, value=label).font = Font(bold=True)
            ws.cell(row=i, column=2, value=_sanitize_for_excel(value))
        ws.column_dimensions["A"].width = 22
        ws.column_dimensions["B"].width = 70

        wd = wb.create_sheet("Details")
        headers = [
            "Candidate Name", "Candidate Email", "Action", "Method", "Endpoint",
            "API Status", "Expected Status", "Duration (ms)", "SLA (ms)", "SLA Status",
            "API Message", "Request Headers", "Request Payload", "Response Body",
            "Screenshot", "Error", "Timestamp",
        ]
        wd.append(headers)
        for col in range(1, len(headers) + 1):
            cell = wd.cell(row=1, column=col)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")
        wd.freeze_panes = "A2"

        for r in self.results:
            row_idx = wd.max_row + 1
            wd.append([
                _sanitize_for_excel(r["candidate_name"]),
                _sanitize_for_excel(r["candidate_email"]),
                _sanitize_for_excel(r["action"]),
                _sanitize_for_excel(r["method"]),
                _sanitize_for_excel(r["endpoint"]),
                r["status_code"],
                r["expected_status"],
                r["elapsed_ms"],
                r["sla_ms"],
                _sanitize_for_excel(r["sla_status"]),
                _sanitize_for_excel(r["api_message"]),
                _sanitize_for_excel(_pretty(r["request_headers"])),
                _sanitize_for_excel(_pretty(r["request_payload"])),
                _sanitize_for_excel(_pretty(r["response_body"])),
                _sanitize_for_excel(r["screenshot"]),
                _sanitize_for_excel(r["error"]),
                _sanitize_for_excel(r["timestamp"]),
            ])
            pass_fill = PASS_FILL if r["passed"] else FAIL_FILL
            for col in range(1, len(headers) + 1):
                wd.cell(row=row_idx, column=col).fill = pass_fill
                wd.cell(row=row_idx, column=col).alignment = Alignment(vertical="top", wrap_text=True)
            if r["sla_status"] == "SLA BREACH":
                wd.cell(row=row_idx, column=10).fill = SLA_WARN_FILL

        widths = {"A": 18, "B": 24, "C": 26, "D": 8, "E": 32, "F": 11, "G": 13,
                "H": 13, "I": 10, "J": 13, "K": 30, "L": 34, "M": 34, "N": 40,
                "O": 20, "P": 40, "Q": 20}
        for col_letter, width in widths.items():
            wd.column_dimensions[col_letter].width = width

        out_path = os.path.join(self.run_folder, "api_health_report.xlsx")
        wb.save(out_path)
        return out_path
def write_summary_json(self) -> str:
    """
    Writes a compact JSON summary (not the full per-row detail) —
    this is what n8n's HTTP Request node will actually parse to decide
    pass/fail branching and compose the notification message.
    """
    out_path = os.path.join(self.run_folder, "summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(self.summary, f, indent=2)
    return out_path
