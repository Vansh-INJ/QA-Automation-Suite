# api_framework/validations/test_offer_validation.py

import pytest
from api_framework.validators.generator import generate_all_validation_cases, generate_pairwise_cases

BASE_PAYLOAD = {
    "first_name": "hii",
    "middle_name": "ji",
    "last_name": "bigi",
    "email": "test@injpartners.com",
    "function_id": "42c5444f-838b-4abd-a4d1-9255022ddd48",
    "sub_function_id": "b95ffda6-fe48-4064-863e-9e342c69cd3b",
    "job_title_id": "326f67ca-be9e-4c31-863b-065335066e40",
    "reporting_manager_uuid": "9237229d-0732-11f1-bd63-40d13383313b",
    "hierarchy_level_uuid": "9237229d-0732-11f1-bd63-40d13383313b",
    "proposed_joining_date": "2026-05-18",
    "employment_type": "Full Time",
    "gross_monthly_salary": 30000,
    "variable_components": {
        "INSURANCE": 4000,
        "INCENTIVE": 2000
    }
}

# FULL FIELD VALIDATION CASES
FIELD_CASES = generate_all_validation_cases(BASE_PAYLOAD)

# OPTIONAL: PAIRWISE CASES (enable when needed)
PAIRWISE_CASES = generate_pairwise_cases(BASE_PAYLOAD)


@pytest.mark.parametrize("case", FIELD_CASES)
def test_field_validations(case, api_client):

    response = api_client.post(case["payload"])

    assert response.status_code == case["expected_status"]


@pytest.mark.parametrize("case", PAIRWISE_CASES)
def test_pairwise_validations(case, api_client):

    response = api_client.post(case["payload"])

    assert response.status_code == 422