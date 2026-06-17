import json
import time

from utils.helpers import (
    write_api_log
)

from utils.api_failure_logger import (
    save_api_failure
)

import os

from utils.run_manager import (
    get_run_folder
)


def log_api_execution(
        test_name,
        method,
        endpoint,
        payload,
        response,
        start_time,
        expected_status=""
):

    duration = round(
        (
            time.time()
            - start_time
        ) * 1000,
        2
    )

    run_folder = os.path.basename(
        get_run_folder()
    )

    environment = os.getenv(
        "TEST_ENV",
        "SIT"
    )

    username = os.getenv(
        "TEST_USER",
        "amit.sharma@company.com"
    )

    sla = 1000

    sla_status = (
        "PASS"
        if duration <= sla
        else "FAIL"
    )

    result = (
        "PASS"
        if response.status_code
        == expected_status
        else "FAIL"
    )

    if result == "FAIL":

        save_api_failure(
            test_name=test_name,
            method=method,
            endpoint=endpoint,
            expected_status=expected_status,
            actual_status=response.status_code,
            duration=duration,
            payload=payload,
            response=response,
            error=(
                f"Expected "
                f"{expected_status} "
                f"but got "
                f"{response.status_code}"
            )
        )

    try:

        request_payload = (
            json.dumps(
                payload,
                indent=4,
                default=str
            )
        )

    except Exception:

        request_payload = str(
            payload
        )

    try:

        response_body = (
            json.dumps(
                response.json(),
                indent=4
            )
        )

    except Exception:

        response_body = (
            response.text
        )

    
        print("\n===== LOG API EXECUTION =====")
    print("run_folder =", run_folder)
    print("environment =", environment)
    print("username =", username)
    print("sla =", sla)
    print("sla_status =", sla_status)
    print("result =", result)
    print("=============================\n")

    write_api_log(
        run_id=run_folder,
        environment=environment,
        username=username,
        test_name=test_name,
        method=method,
        endpoint=endpoint,
        status_code=response.status_code,
        expected_status=expected_status,
        actual_status=response.status_code,
        duration=duration,
        sla=sla,
        sla_status=sla_status,
        result=result,
        request_payload=request_payload,
        response_body=response_body
    )