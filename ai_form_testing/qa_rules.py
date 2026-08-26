"""Human-authored QA rules.

Gemini is never the authority for deterministic business expectations.
Add reviewed HRMS-specific rules here as the framework grows.
"""

QA_RULES: dict[str, dict[str, object]] = {
    # Examples from the existing QA knowledge base. These are deliberately
    # not wired into execution yet; Phase 1 only discovers the schema.
    "unicode_names_valid": {
        "description": "Unicode names are valid unless the field explicitly restricts them.",
        "fields": ["first_name", "middle_name", "last_name"],
    },
    "primary_phone_family_contact_distinct": {
        "description": "Primary phone and family contact should not be identical.",
        "fields": [
            "communication-primary_phone-0",
            "family_members-contact_number-0",
        ],
    },
}
