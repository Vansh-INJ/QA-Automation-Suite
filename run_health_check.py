"""
Single entry point to run the API Health Suite.

Run manually, anytime:
    python run_health_check.py

This is also the script the Windows Scheduled Task calls every morning
(see setup_scheduler.py) — same code path either way, no special-casing
for "scheduled vs manual" runs.
"""

import sys
import subprocess
from datetime import datetime


def main():
    print(f"[health-suite] Run started: {datetime.now().isoformat(timespec='seconds')}")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "test/health", "-q", "--junitxml=junit-health.xml"],
        cwd=".",
    )

    print(f"[health-suite] Run finished with exit code {result.returncode}")
    # Exit code 0 = all passed, 1 = some tests failed (pytest convention).
    # We deliberately DON'T re-raise/fail the script on test failures —
    # the point of this script is "run and report", not "fail the job".
    # The Excel report + email + Slack alert already carry the failure signal.
    sys.exit(0)


if __name__ == "__main__":
    main()
