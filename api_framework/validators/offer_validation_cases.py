# api_framework/validations/offer_validation_cases.py

VALIDATION_CASES = [

    # ==========================================
    # Required Fields
    # ==========================================

    {
        "id": "VAL-001",
        "scenario": "Missing First Name",
        "field": "first_name",
        "operation": "delete",
        "expected_status": 422,
        "error_field": "first_name",
        "error_message": "Field is required"
    },

    {
        "id": "VAL-002",
        "scenario": "Missing Email",
        "field": "email",
        "operation": "delete",
        "expected_status": 422,
        "error_field": "email",
        "error_message": "Field is required"
    },

    # ==========================================
    # Format Validation
    # ==========================================

    {
        "id": "VAL-003",
        "scenario": "Invalid Email",
        "field": "email",
        "value": "abc",
        "expected_status": 422,
        "error_field": "email",
        "error_message": "Invalid email format"
    },

    # ==========================================
    # Business Validation
    # ==========================================

    {
        "id": "VAL-004",
        "scenario": "Negative Salary",
        "field": "gross_monthly_salary",
        "value": -1000,
        "expected_status": 422,
        "error_field": "gross_monthly_salary",
        "error_message": None
    }
]