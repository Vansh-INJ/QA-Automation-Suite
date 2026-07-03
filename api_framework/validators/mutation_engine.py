# api_framework/validations/mutation_engine.py

def generate_invalid_value(field_type):

    if field_type == "string":
        return 12345

    if field_type == "uuid":
        return "not-a-valid-uuid"

    if field_type == "number":
        return "invalid_number"

    if field_type == "date":
        return "31-99-9999"

    if field_type == "enum":
        return "INVALID_ENUM"

    if field_type == "object":
        return "INVALID_OBJECT"

    return "???"