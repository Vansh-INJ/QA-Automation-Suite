"""
Registers (or updates) a Windows Scheduled Task that runs the API Health
Suite daily, at a time YOU control — set once in .env, change anytime.

WHY THIS EXISTS instead of a raw `schtasks` command you type once:
    Windows Task Scheduler doesn't read from your .env file. This script
    is the bridge: it reads HEALTH_RUN_TIME from .env and (re)creates the
    scheduled task to match. Change the time in .env, rerun this script,
    done — no need to remember schtasks syntax or dig through the Task
    Scheduler GUI.

SETUP (one-time):
    1. Set HEALTH_RUN_TIME in .env, e.g.:
           HEALTH_RUN_TIME=11:30
    2. Run this script ONCE from an elevated (Run as Administrator) PowerShell:
           python setup_scheduler.py

TO CHANGE THE TIME LATER:
    1. Edit HEALTH_RUN_TIME in .env
    2. Rerun: python setup_scheduler.py
       (it deletes and recreates the task with the new time)

TO RUN MANUALLY, ANYTIME, OUTSIDE THE SCHEDULE:
    python run_health_check.py
    (this never touches the scheduled task — completely independent)

TO REMOVE THE SCHEDULED TASK:
    schtasks /Delete /TN "APIHealthCheck" /F
"""

import os
import sys
import subprocess

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # falls back to already-exported env vars if python-dotenv isn't installed

TASK_NAME = "APIHealthCheck"


def get_configured_time() -> str:
    run_time = os.getenv("HEALTH_RUN_TIME", "07:00").strip()
    # Basic sanity check: expects HH:MM 24-hour format
    parts = run_time.split(":")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        print(f"[setup_scheduler] HEALTH_RUN_TIME='{run_time}' doesn't look like HH:MM. "
              f"Falling back to 07:00.")
        return "07:00"
    hh, mm = int(parts[0]), int(parts[1])
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        print(f"[setup_scheduler] HEALTH_RUN_TIME='{run_time}' out of range. Falling back to 07:00.")
        return "07:00"
    return f"{hh:02d}:{mm:02d}"


def main():
    run_time = get_configured_time()
    python_exe = sys.executable
    script_path = os.path.abspath("run_health_check.py")
    working_dir = os.path.abspath(".")

    # Delete existing task first (ignore error if it doesn't exist yet)
    subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True,
    )

    # /TR needs the working directory baked in since Task Scheduler doesn't
    # otherwise run from the repo folder.
    task_run_command = (
        f'cmd /c "cd /d {working_dir} && \"{python_exe}\" \"{script_path}\""'
    )

    result = subprocess.run(
        [
            "schtasks", "/Create",
            "/TN", TASK_NAME,
            "/TR", task_run_command,
            "/SC", "DAILY",
            "/ST", run_time,
            "/F",  # overwrite if exists
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"[setup_scheduler] Scheduled Task '{TASK_NAME}' created — runs daily at {run_time}.")
        print(f"[setup_scheduler] Command: {task_run_command}")
        print("[setup_scheduler] View/edit it anytime in Task Scheduler (taskschd.msc), "
              f"or change HEALTH_RUN_TIME in .env and rerun this script.")
    else:
        print("[setup_scheduler] Failed to create scheduled task.")
        print(result.stdout)
        print(result.stderr)
        print("[setup_scheduler] Make sure you're running this from an elevated "
              "(Run as Administrator) terminal.")


if __name__ == "__main__":
    main()
