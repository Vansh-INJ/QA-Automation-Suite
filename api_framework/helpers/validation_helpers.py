# api_framework/helpers/validation_helpers.py

import copy

from api_framework.validators.mutation_engine import generate_invalid_value


def apply_validation_case(payload: dict, case: dict):

    field = case.get("field")

    mutation = case.get("mutation")
    value = case.get("value")  # may not exist anymore

    # ------------------------------
    # CASE 1: FULL PAYLOAD PROVIDED (NEW SYSTEM)
    # ------------------------------
    if "payload" in case:
        payload.clear()
        payload.update(case["payload"])
        return payload

    # ------------------------------
    # CASE 2: OLD SYSTEM SUPPORT (BACKWARD COMPAT)
    # ------------------------------
    if value is not None:
        payload[field] = value
        return payload

    # ------------------------------
    # CASE 3: MUTATION-BASED SYSTEM
    # ------------------------------

    if mutation == "missing":
        payload.pop(field, None)

    elif mutation == "null":
        payload[field] = None

    elif mutation == "empty":
        payload[field] = ""

    elif mutation == "wrong_type":
        payload[field] = generate_invalid_value("string")

    elif mutation == "invalid_enum":
        payload[field] = "INVALID_ENUM"

    return payload


def assert_validation_error(response_body: dict, case: dict):

    # basic safe check (adjust based on your API format)
    assert response_body is not None, "Response body is empty"

    expected_field = case.get("field")

    # flexible validation (adjust to your backend response format)
    errors = response_body.get("errors", {})

    if expected_field:
        assert (
            expected_field in str(errors)
            or expected_field in response_body
        ), (
            f"Expected validation error for field '{expected_field}' "
            f"but got: {response_body}"
        )