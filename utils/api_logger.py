import json
import time
import os

from utils.helpers import write_result
from utils.api_failure_logger import save_api_failure
from utils.run_manager import get_run_folder
from api_framework.config.settings import Settings


import re

def safe_filename(name: str) -> str:
    """
    Removes invalid Windows filename characters
    """
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def log_api_execution(
        test_name,
        method,
        endpoint,
        payload,
        response,
        start_time,
        expected_status=200,
        error=""
):
    """
    Central API execution logger.

    Responsibilities:
    1. Calculate duration
    2. Determine PASS / FAIL
    3. Save failure details
    4. Write execution report to Excel
    """

    # ==========================================
    # Duration
    # ==========================================
    duration_ms = round(
        (time.time() - start_time) * 1000,
        2
    )

    sla_ms = 1000

    sla_status = (
        "PASS"
        if duration_ms <= sla_ms
        else "FAIL"
    )

    # ==========================================
    # Response Body
    # ==========================================
    try:
        body = response.json()
    except Exception:
        body = {
            "raw": response.text,
            "error": "Invalid JSON response"
        }

    actual_status = response.status_code

    status = (
        "PASS"
        if actual_status == expected_status
        else "FAIL"
    )

    # ==========================================
    # Candidate Details
    # ==========================================
    candidate_name = (
        f"{payload.get('first_name', '')} "
        f"{payload.get('last_name', '')}"
    ).strip()

    candidate_email = payload.get(
        "email",
        ""
    )

    action = "Send Offer"

    api_message = (
        body.get("message")
        or body.get("status")
        or ""
    )

    request_headers = {
        "Authorization":
            "***REDACTED***",

        "Content-Type":
            "application/json"
    }

    # ==========================================
    # Preserve custom error
    # ==========================================
    if not error:

        if actual_status >= 400:
            error = response.text
        else:
            error = ""

    # ==========================================
    # Debug
    # ==========================================
    print("\nINSIDE LOGGER")
    print("STATUS :", status)
    print("ERROR  :", repr(error))

    # ==========================================
    # Failure Logger
    # ==========================================
    if status == "FAIL":

        save_api_failure(
            test_name=test_name,
            method=method,
            endpoint=endpoint,
            expected_status=expected_status,
            actual_status=actual_status,
            duration=duration_ms,
            payload=payload,
            response=response,
            error=error
        )

    # ==========================================
    # Excel Report
    # ==========================================
    write_result(
        test_name=test_name,

        status=status,

        candidate_name=candidate_name,

        candidate_email=candidate_email,

        action=action,

        run_id=os.path.basename(
            get_run_folder()
        ),

        environment="SIT",

        username=Settings.API_USERNAME,

        method=method,

        endpoint=endpoint,

        api_status=actual_status,

        expected_status=expected_status,

        duration=duration_ms,

        sla=sla_ms,

        sla_status=sla_status,

        api_message=api_message,

        request_headers=json.dumps(
            request_headers,
            indent=4
        ),

        request_payload=json.dumps(
            payload,
            indent=4,
            default=str
        ),

        response_body=json.dumps(
            body,
            indent=4,
            default=str
        ),

        error=error,

        screenshot=""
    )