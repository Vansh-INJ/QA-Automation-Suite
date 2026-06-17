import os
import json
from datetime import datetime

from utils.run_manager import (
    get_run_folder
)


def save_api_failure(
        test_name,
        method,
        endpoint,
        expected_status,
        actual_status,
        duration,
        payload,
        response,
        error=""
):

    run_folder = get_run_folder()

    failure_folder = os.path.join(
        run_folder,
        "api_failures"
    )

    os.makedirs(
        failure_folder,
        exist_ok=True
    )

    timestamp = (
        datetime.now()
        .strftime(
            "%Y%m%d_%H%M%S"
        )
    )

    filename = os.path.join(
        failure_folder,
        f"{test_name}_{timestamp}.json"
    )

    try:
        response_body = (
            response.json()
        )
    except Exception:
        response_body = (
            response.text
        )

    data = {
        "timestamp":
            str(
                datetime.now()
            ),

        "test_name":
            test_name,

        "method":
            method,

        "endpoint":
            endpoint,

        "expected_status":
            expected_status,

        "actual_status":
            actual_status,

        "duration_ms":
            duration,

        "request_payload":
            payload,

        "response_body":
            response_body,

        "error":
            error
    }

    with open(
            filename,
            "w",
            encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            default=str
        )

    print(
        f"\n[API FAILURE SAVED]"
        f"\n{filename}"
    )