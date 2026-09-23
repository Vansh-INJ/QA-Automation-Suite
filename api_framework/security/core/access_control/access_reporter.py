"""
access_reporter.py -- FIXED: sanitizes all string cell values before writing
to Excel. openpyxl rejects certain control characters (0x00-0x08, 0x0B, 0x0C,
0x0E-0x1F) that can appear in raw API response bodies/error messages -- these
were leaking through r.message / leaked_fields into cells and crashing the
writer with IllegalCharacterError.
"""

import json
import re
from collections import defaultdict
from openpyxl import Workbook

# Matches the exact control-character range openpyxl disallows in cells
_ILLEGAL_CHARACTERS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def _sanitize(value):
    """Strip Excel-illegal control characters from any string value.
    Non-strings pass through unchanged."""
    if isinstance(value, str):
        return _ILLEGAL_CHARACTERS_RE.sub('', value)
    return value


class AccessControlReporter:
    def __init__(self):
        self.results = []  # list[AccessControlResult]

    def record(self, result):
        self.results.append(result)

    def summary(self) -> dict:
        total = len(self.results)
        by_verdict = defaultdict(int)
        by_vuln_type = defaultdict(lambda: {"total": 0, "failed": 0})

        for r in self.results:
            by_verdict[r.result] += 1
            by_vuln_type[r.vulnerability_type]["total"] += 1
            if r.result == "FAIL":
                by_vuln_type[r.vulnerability_type]["failed"] += 1

        failed = [r for r in self.results if r.result == "FAIL"]
        high_conf_failed = [r for r in failed if r.confidence == "HIGH"]

        return {
            "total": total,
            "pass": by_verdict.get("PASS", 0),
            "fail": by_verdict.get("FAIL", 0),
            "blocked": by_verdict.get("BLOCKED", 0),
            "error": by_verdict.get("ERROR", 0),
            "high_confidence_vulnerabilities": len(high_conf_failed),
            "by_vulnerability_type": dict(by_vuln_type),
            "owasp_category": "A01:2021-Broken Access Control",
        }

    def write_summary_json(self, path="access_control_summary.json"):
        with open(path, "w") as f:
            json.dump(self.summary(), f, indent=2)

    def write_excel(self, path="access_control_report.xlsx"):
        wb = Workbook()
        ws = wb.active
        ws.title = "Access Control Report"
        headers = [
            "Endpoint", "Method", "Vulnerability Type", "Acting Profile",
            "Target Owner Profile", "Resource ID", "Expected Status", "Actual Status",
            "Result", "Confidence", "OWASP Category", "Leaked Fields", "Message", "Duration (ms)",
        ]
        ws.append(headers)
        for r in self.results:
            row = [
                r.endpoint, r.method, r.vulnerability_type, r.acting_profile,
                r.target_owner_profile, r.resource_id, r.expected_status, r.actual_status,
                r.result, r.confidence, r.owasp_category,
                ", ".join(r.leaked_fields) if r.leaked_fields else "",
                r.message, r.duration_ms,
            ]
            ws.append([_sanitize(v) for v in row])
        wb.save(path)