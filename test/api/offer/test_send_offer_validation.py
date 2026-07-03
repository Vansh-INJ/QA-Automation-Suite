# pyrefly: ignore [missing-import]

import time
import pytest
from utils.file_sanitizer import safe_filename
from api_framework.payloads.offer_payloads import OfferPayloads


from api_framework.helpers.validation_helpers import (
    apply_validation_case,
    assert_validation_error
)
from api_framework.validators.generator import generate_all_validation_cases
from utils.api_logger import log_api_execution


# ======================================
# BASE PAYLOAD
# ======================================

BASE_PAYLOAD = OfferPayloads.valid()


# ======================================
# AUTO-GENERATED CASES
# ======================================

VALIDATION_CASES = generate_all_validation_cases(BASE_PAYLOAD)


# ======================================
# TEST
# ======================================

@pytest.mark.parametrize(
    "case",
    VALIDATION_CASES,
    ids=lambda case: (
        f"{case['field']}__{case['mutation']}"
    )
)
def test_send_offer_validation(
        authenticated_offer_client,
        case
):

    payload = OfferPayloads.valid()

    # ======================================
    # APPLY MUTATION
    # ======================================

    apply_validation_case(payload, case)

    # ======================================
    # EXECUTE API
    # ======================================

    start = time.time()

    response = authenticated_offer_client.send_offer(payload)

    try:
        body = response.json()
    except Exception:
        body = {
            "raw": response.text,
            "error": "Invalid or empty JSON response"
        }

    # ======================================
    # STATUS VALIDATION
    # ======================================

    expected_status = case.get("expected_status", 422)
    actual_status = response.status_code

    result = (
        "PASS"
        if actual_status == expected_status
        else "FAIL"
    )

    # ======================================
    # ERROR MESSAGE (STRICT DEBUGGING)
    # ======================================

    error_message = ""

    if result == "FAIL":

        field = case.get("field")
        value_sent = (
            payload.get(field)
            if field
            else payload
        )

        error_message = (
            f"Backend validation failure. "
            f"Field '{field}' accepted invalid value '{value_sent}'. "
            f"Expected HTTP {expected_status} "
            f"but received HTTP {actual_status}."
        )

    # ======================================
    # LOGGING
    # ======================================

    print("\nERROR MESSAGE:")
    print(error_message)

    log_api_execution(
        test_name=f"{case['field']} | {case['mutation']}",
        method="POST",
        endpoint="/api/hr/offers/send",
        payload=payload,
        response=response,
        start_time=start,
        expected_status=expected_status,
        error=error_message
    )

    # ======================================
    # DEBUG OUTPUT
    # ======================================

    print(f"\n[{case['field']} | {case['mutation']}]")
    print("Status:", response.status_code)
    print("Response:", body)

    # ======================================
    # ASSERT STATUS
    # ======================================

    assert actual_status == expected_status, (
        f"\nValidation Failed\n"
        f"------------------------------\n"
        f"Field         : {case.get('field')}\n"
        f"Mutation      : {case.get('mutation')}\n"
        f"Expected HTTP : {expected_status}\n"
        f"Actual HTTP   : {actual_status}\n"
        f"Response      : {body}\n"
    )

    # ======================================
    # CONTRACT VALIDATION
    # ======================================

    if expected_status == 422:
        assert_validation_error(body, case)