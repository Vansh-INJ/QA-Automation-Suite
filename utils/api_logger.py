import json
import time
import os

from utils.helpers import write_api_log
from utils.api_failure_logger import save_api_failure
from utils.run_manager import get_run_folder


def log_api_execution(
        test_name,
        method,
        endpoint,
        payload,
        response,
        start_time,
        expected_status=200
):

    # =========================
    # DURATION
    # =========================
    duration = round(
        (time.time() - start_time) * 1000,
        2
    )

    # =========================
    # RUN CONTEXT (FIXED)
    # =========================
    run_id = os.path.basename(get_run_folder())   # 🔥 FIXED HERE

    environment = os.getenv("TEST_ENV", "SIT")
    username = os.getenv("TEST_USER", "amit.sharma@company.com")

    sla = 1000

    # =========================
    # SAFE EXPECTED STATUS
    # =========================
    try:
        expected_status = int(expected_status)
    except:
        expected_status = 200

    # =========================
    # SLA CHECK
    # =========================
    sla_status = "PASS" if duration <= sla else "FAIL"

    # =========================
    # RESULT CHECK
    # =========================
    actual_status = response.status_code

    result = "PASS" if actual_status == expected_status else "FAIL"

    # =========================
    # FAILURE LOGGING
    # =========================
    if result == "FAIL":
        save_api_failure(
            test_name=test_name,
            method=method,
            endpoint=endpoint,
            expected_status=expected_status,
            actual_status=actual_status,
            duration=duration,
            payload=payload,
            response=response,
            error=f"Expected {expected_status} but got {actual_status}"
        )

    # =========================
    # SERIALIZATION SAFETY
    # =========================
    try:
        request_payload = json.dumps(payload, indent=4, default=str)
    except:
        request_payload = str(payload)

    try:
        response_body = json.dumps(response.json(), indent=4)
    except:
        response_body = response.text

    # =========================
    # DEBUG LOGimport json
import time
from datetime import datetime

from utils.helpers import write_result
from utils.run_manager import get_run_folder
from api_framework.config.settings import Settings


def log_api_execution(
        test_name,
        method,
        endpoint,
        payload,
        response,
        start_time,
        expected_status=200
):

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

    try:
        body = response.json()
    except Exception:
        body = {}

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

    error = ""

    if response.status_code >= 400:
        error = response.text

    write_result(
        test_name=test_name,

        status=(
            "PASS"
            if response.status_code
            == expected_status
            else "FAIL"
        ),

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

        api_status=response.status_code,

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
            indent=4
        ),

        response_body=json.dumps(
            body,
            indent=4
        ),

        error=error,

        screenshot=""
    )