"""
Builds the HTML email body — the "dashboard" the user sees directly in
their inbox, no Excel, no attachment required. Grouped by module
(User/HR/Admin/Finance/Other) so failures are immediately attributable.
"""

from datetime import datetime
from utils.health_module_map import classify_module, owner_for


def _status_pill(passed: bool) -> str:
    if passed:
        return '<span style="background:#C6EFCE;color:#0B6B0B;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:600;">WORKING</span>'
    return '<span style="background:#FFC7CE;color:#9C0006;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:600;">NOT WORKING</span>'


def build_dashboard_html(results: list, summary: dict) -> str:
    """
    results: the list of per-endpoint dicts from HealthReporter.results
              (each has name/action/method/endpoint/passed/status_code/
              expected_status/error/request_headers/response_body/etc.)
    summary: HealthReporter.summary dict
    """
    # Group by module
    by_module = {}
    for r in results:
        module = classify_module(r["endpoint"])
        by_module.setdefault(module, []).append(r)

    module_order = ["User", "HR", "Admin", "Finance", "Other"]

    overall_pill_color = "#0B6B0B" if summary["failed"] == 0 else "#9C0006"
    overall_text = "ALL SYSTEMS OPERATIONAL" if summary["failed"] == 0 else f"{summary['failed']} API(S) DOWN"

    html_parts = [f"""
    <html>
    <body style="font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; background:#f4f5f7; margin:0; padding:24px;">
      <div style="max-width:820px;margin:0 auto;background:#ffffff;border-radius:10px;overflow:hidden;border:1px solid #e2e4e8;">

        <div style="background:#1f2430;padding:24px 28px;">
          <div style="color:#ffffff;font-size:20px;font-weight:700;">INJIN HRMS — API Health Dashboard</div>
          <div style="color:#9aa1ae;font-size:13px;margin-top:4px;">Run: {summary['run_time']}</div>
        </div>

        <div style="padding:20px 28px;border-bottom:1px solid #eef0f3;">
          <span style="display:inline-block;background:{overall_pill_color};color:#fff;padding:6px 14px;border-radius:6px;font-weight:700;font-size:13px;">
            {overall_text}
          </span>
          <div style="margin-top:14px;display:flex;gap:24px;font-size:14px;color:#333;">
            <div><b>{summary['total']}</b> Total</div>
            <div style="color:#0B6B0B;"><b>{summary['passed']}</b> Working</div>
            <div style="color:#9C0006;"><b>{summary['failed']}</b> Not Working</div>
            <div><b>{summary['pass_rate']}%</b> Pass Rate</div>
          </div>
        </div>
    """]

    for module in module_order:
        rows = by_module.get(module)
        if not rows:
            continue
        module_failed = [r for r in rows if not r["passed"]]
        module_passed = [r for r in rows if r["passed"]]
        module_color = "#9C0006" if module_failed else "#0B6B0B"

        html_parts.append(f"""
        <div style="padding:18px 28px;border-bottom:1px solid #eef0f3;">
          <div style="font-size:15px;font-weight:700;color:#1f2430;">
            {module} Module
            <span style="font-size:12px;font-weight:500;color:{module_color};margin-left:8px;">
              {len(module_passed)}/{len(rows)} working
            </span>
          </div>
        """)

        if module_failed:
            owner = owner_for(module_failed[0]["endpoint"])
            html_parts.append(f"""
          <div style="margin-top:10px;font-size:12px;color:#666;">Assign to: <b>{owner}</b></div>
          <table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:13px;">
            <tr style="background:#fafbfc;text-align:left;">
              <th style="padding:6px 8px;border-bottom:1px solid #eef0f3;">API</th>
              <th style="padding:6px 8px;border-bottom:1px solid #eef0f3;">Method</th>
              <th style="padding:6px 8px;border-bottom:1px solid #eef0f3;">Endpoint</th>
              <th style="padding:6px 8px;border-bottom:1px solid #eef0f3;">Status</th>
              <th style="padding:6px 8px;border-bottom:1px solid #eef0f3;">Error</th>
            </tr>
          """)
            for r in module_failed:
                error_short = (r.get("error") or r.get("api_message") or "")[:140]
                html_parts.append(f"""
            <tr>
              <td style="padding:6px 8px;border-bottom:1px solid #f4f5f7;">{r['action']}</td>
              <td style="padding:6px 8px;border-bottom:1px solid #f4f5f7;">{r['method']}</td>
              <td style="padding:6px 8px;border-bottom:1px solid #f4f5f7;font-family:monospace;font-size:12px;">{r['endpoint']}</td>
              <td style="padding:6px 8px;border-bottom:1px solid #f4f5f7;">{_status_pill(False)} ({r.get('status_code','—')})</td>
              <td style="padding:6px 8px;border-bottom:1px solid #f4f5f7;color:#9C0006;font-size:12px;">{error_short}</td>
            </tr>
            """)
            html_parts.append("</table>")
        else:
            html_parts.append('<div style="font-size:13px;color:#0B6B0B;margin-top:6px;">All working — no action needed.</div>')

        html_parts.append("</div>")

    html_parts.append(f"""
        <div style="padding:16px 28px;font-size:12px;color:#9aa1ae;">
          Automated daily API health check — INJIN HRMS. Full request/response
          detail for each failure is available in the attached failure log
          (if applicable) or the suite's api_failures/ folder for this run.
        </div>
      </div>
    </body>
    </html>
    """)

    return "".join(html_parts)


def build_subject(summary: dict) -> str:
    if summary["failed"] == 0:
        return f"[API Health] ✅ All {summary['total']} APIs Working — {datetime.now().strftime('%d %b, %H:%M')}"
    return (
        f"[API Health] ⚠ {summary['failed']} API(s) Down "
        f"({summary['passed']}/{summary['total']} working) — {datetime.now().strftime('%d %b, %H:%M')}"
    )
