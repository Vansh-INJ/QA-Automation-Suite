# api_framework/validations/schema.py

FIELD_SCHEMA = {
    "first_name": {
        "type": "string",
        "required": True,
        "rules": ["not_empty"]
    },
    "middle_name": {
        "type": "string",
        "required": False,
        "rules": []
    },
    "last_name": {
        "type": "string",
        "required": True,
        "rules": ["not_empty"]
    },
    "email": {
        "type": "string",
        "required": True,
        "rules": ["email_format"]
    },
    "function_id": {
        "type": "uuid",
        "required": True,
        "rules": ["uuid_format", "exists"]
    },
    "sub_function_id": {
        "type": "uuid",
        "required": True,
        "rules": ["uuid_format", "exists"]
    },
    "job_title_id": {
        "type": "uuid",
        "required": True,
        "rules": ["uuid_format", "exists"]
    },
    "reporting_manager_uuid": {
        "type": "uuid",
        "required": True,
        "rules": ["uuid_format", "exists"]
    },
    "hierarchy_level_uuid": {
        "type": "uuid",
        "required": True,
        "rules": ["uuid_format"]
    },
    "proposed_joining_date": {
        "type": "date",
        "required": True,
        "rules": ["future_only"]
    },
    "employment_type": {
        "type": "enum",
        "required": True,
        "allowed": ["Full Time", "Part Time", "Contract"]
    },
    "gross_monthly_salary": {
        "type": "number",
        "required": True,
        "rules": ["positive"]
    },
    "variable_components": {
        "type": "object",
        "required": False,
        "rules": ["numeric_map"]
    }
}