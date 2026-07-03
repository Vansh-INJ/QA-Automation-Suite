# api_framework/validations/case_builder.py

import copy

from api_framework.validators.mutation_engine import generate_invalid_value

def set_field(payload, field, value):
    p = copy.deepcopy(payload)
    p[field] = value
    return p


def delete_field(payload, field):
    p = copy.deepcopy(payload)
    p.pop(field, None)
    return p


def build_field_cases(field, config, base_payload):

    cases = []

    original = base_payload.get(field)

    # 1. Missing field
    if config.get("required"):
        cases.append({
            "field": field,
            "mutation": "missing",
            "payload": delete_field(base_payload, field),
            "expected_status": 422
        })

    # 2. Null value
    cases.append({
        "field": field,
        "mutation": "null",
        "payload": set_field(base_payload, field, None),
        "expected_status": 422
    })

    # 3. Empty string (string fields only)
    if config["type"] == "string":
        cases.append({
            "field": field,
            "mutation": "empty",
            "payload": set_field(base_payload, field, ""),
            "expected_status": 422
        })

    # 4. Wrong type injection
    cases.append({
        "field": field,
        "mutation": "wrong_type",
        "payload": set_field(
            base_payload,
            field,
            generate_invalid_value(config["type"])
        ),
        "expected_status": 422
    })

    # 5. Enum invalid
    if config["type"] == "enum":
        cases.append({
            "field": field,
            "mutation": "invalid_enum",
            "payload": set_field(base_payload, field, "FAKE_ENUM"),
            "expected_status": 422
        })

    return cases