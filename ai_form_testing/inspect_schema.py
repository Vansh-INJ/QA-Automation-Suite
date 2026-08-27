import hashlib
import json
from pathlib import Path


SCHEMA_PATH = Path("ai_form_testing/form_schema.json")


def calculate_schema_hash(data: dict) -> str:
    """
    Calculate the schema hash using the exact same canonical
    representation as schema_discovery._hash_fields().
    """

    fields = data.get("fields", [])

    canonical = [
        {
            key: value
            for key, value in field.items()
            if key != "raw"
        }
        for field in sorted(
            fields,
            key=lambda item: (
                item.get("qualified_name")
                or item.get("name")
            ),
        )
    ]

    payload = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def main() -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}"
        )

    data = json.loads(
        SCHEMA_PATH.read_text(encoding="utf-8")
    )

    fields = data.get("fields", [])

    stored_hash = data.get("schema_hash")
    calculated_hash = calculate_schema_hash(data)

    qualified_names = [
        field.get("qualified_name")
        or field.get("name")
        for field in fields
    ]

    duplicates = sorted(
        {
            name
            for name in qualified_names
            if qualified_names.count(name) > 1
        }
    )

    required_count = sum(
        1 for field in fields
        if field.get("required") is True
    )

    optional_count = len(fields) - required_count

    repeatable_count = sum(
        1 for field in fields
        if field.get("repeatable") is True
    )

    validation_count = sum(
        1 for field in fields
        if field.get("validation")
    )

    regex_count = sum(
        1 for field in fields
        if field.get("pattern")
    )

    options_count = sum(
        1 for field in fields
        if field.get("options")
    )

    options_key_count = sum(
        1 for field in fields
        if field.get("options_key")
    )

    lookup_key_count = sum(
        1 for field in fields
        if field.get("lookup_key")
    )

    cross_validation_count = sum(
        len(field.get("cross_validations") or [])
        for field in fields
    )

    condition_count = sum(
        len(field.get("conditions") or [])
        for field in fields
    )

    section_rule_count = sum(
        len(field.get("section_rules") or [])
        for field in fields
    )

    print("=" * 80)
    print("AI-SDET SCHEMA INSPECTION")
    print("=" * 80)

    print(f"Form                 : {data.get('form_name')}")
    print(f"Source               : {data.get('source')}")
    print(f"Stored Schema Hash   : {stored_hash}")
    print(f"Calculated Hash      : {calculated_hash}")
    print(
        f"Hash matches         : "
        f"{stored_hash == calculated_hash}"
    )

    print()
    print("-" * 80)
    print("SCHEMA SUMMARY")
    print("-" * 80)

    print(f"Total fields         : {len(fields)}")
    print(f"Unique qualified     : {len(set(qualified_names))}")
    print(f"Duplicate qualified  : {len(duplicates)}")
    print(f"Required fields      : {required_count}")
    print(f"Optional fields      : {optional_count}")
    print(f"Repeatable fields    : {repeatable_count}")
    print(f"With validation      : {validation_count}")
    print(f"With regex           : {regex_count}")
    print(f"With options list    : {options_count}")
    print(f"With options key     : {options_key_count}")
    print(f"With lookup key      : {lookup_key_count}")
    print(f"Cross-validations    : {cross_validation_count}")
    print(f"Conditions           : {condition_count}")
    print(f"Section rules        : {section_rule_count}")

    if duplicates:
        print()
        print("Duplicate qualified names:")
        for name in duplicates:
            print(f"  - {name}")

    print()
    print("-" * 80)
    print("INPUT TYPE SUMMARY")
    print("-" * 80)

    type_counts: dict[str, int] = {}

    for field in fields:
        field_type = field.get("input_type", "unknown")
        type_counts[field_type] = (
            type_counts.get(field_type, 0) + 1
        )

    for field_type, count in sorted(type_counts.items()):
        print(f"{field_type:<20} : {count}")

    print()
    print("-" * 80)
    print("SECTION SUMMARY")
    print("-" * 80)

    sections: dict[str, list[dict]] = {}

    for field in fields:
        section = (
            field.get("section_key")
            or "unknown"
        )

        sections.setdefault(section, []).append(field)

    for section_name, section_fields in sections.items():
        repeatable = any(
            field.get("repeatable") is True
            for field in section_fields
        )

        print(
            f"{section_name:<30} "
            f"fields={len(section_fields):<3} "
            f"repeatable={repeatable}"
        )

    print()
    print("-" * 80)
    print("BUSINESS RULE DETAILS")
    print("-" * 80)

    print("Cross-validations:")

    for field in fields:
        for rule in field.get("cross_validations") or []:
            rule_name = (
                rule.get("name")
                or rule.get("rule")
                or rule.get("key")
                or "unnamed"
            )

            qualified_name = (
                field.get("qualified_name")
                or field.get("name")
            )

            print(
                f"  - {rule_name} "
                f"({qualified_name})"
            )

    print()
    print("Conditions:")

    for field in fields:
        for rule in field.get("conditions") or []:
            rule_name = (
                rule.get("name")
                or rule.get("rule")
                or rule.get("key")
                or "unnamed"
            )

            qualified_name = (
                field.get("qualified_name")
                or field.get("name")
            )

            print(
                f"  - {rule_name} "
                f"({qualified_name})"
            )

    print()
    print("Section rules:")

    for field in fields:
        for rule in field.get("section_rules") or []:
            rule_name = (
                rule.get("name")
                or rule.get("rule")
                or rule.get("key")
                or "unnamed"
            )

            qualified_name = (
                field.get("qualified_name")
                or field.get("name")
            )

            print(
                f"  - {rule_name} "
                f"({qualified_name})"
            )

    print()
    print("=" * 80)
    print("FIELD DETAILS")
    print("=" * 80)

    for index, field in enumerate(fields, start=1):
        qualified_name = (
            field.get("qualified_name")
            or field.get("name")
        )

        print(f"{index:02d}. {qualified_name}")
        print(f"    name           : {field.get('name')}")
        print(f"    type           : {field.get('input_type')}")
        print(f"    required       : {field.get('required')}")
        print(f"    repeatable     : {field.get('repeatable')}")
        print(f"    validation     : {field.get('validation')}")
        print(f"    regex          : {field.get('pattern')}")
        print(f"    options        : {field.get('options')}")
        print(f"    options_key    : {field.get('options_key')}")
        print(f"    lookup_key     : {field.get('lookup_key')}")
        print(
            f"    cross_validate : "
            f"{len(field.get('cross_validations') or [])}"
        )
        print(
            f"    conditions     : "
            f"{len(field.get('conditions') or [])}"
        )
        print(
            f"    section_rules  : "
            f"{len(field.get('section_rules') or [])}"
        )
        print()


if __name__ == "__main__":
    main()