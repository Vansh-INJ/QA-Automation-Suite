# api_framework/validations/generator.py

from api_framework.validators.case_builder import build_field_cases
from api_framework.validators.schema import FIELD_SCHEMA


def generate_all_validation_cases(base_payload):

    all_cases = []

    for field, config in FIELD_SCHEMA.items():
        field_cases = build_field_cases(field, config, base_payload)
        all_cases.extend(field_cases)

    return all_cases


def generate_pairwise_cases(base_payload):

    """
    Lightweight combination testing (2-field interaction faults)
    """

    import copy

    cases = []
    fields = list(FIELD_SCHEMA.keys())

    for i in range(len(fields)):
        for j in range(i + 1, len(fields)):

            f1, f2 = fields[i], fields[j]

            payload = copy.deepcopy(base_payload)

            payload[f1] = None
            payload[f2] = "INVALID"

            cases.append({
                "field": f"{f1}+{f2}",
                "mutation": "pairwise",
                "payload": payload,
                "expected_status": 422
            })

    return cases