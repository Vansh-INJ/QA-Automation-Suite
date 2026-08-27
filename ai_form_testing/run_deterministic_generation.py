"""
Run deterministic QA case generation against the discovered schema.
"""

from __future__ import annotations

import json
from pathlib import Path

from .deterministic_generator import generate_deterministic_cases
from .models import FormSchema


SCHEMA_PATH = Path("ai_form_testing/form_schema.json")
OUTPUT_PATH = Path(
    "ai_form_testing/deterministic_cases.json"
)


def main() -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema not found: {SCHEMA_PATH}"
        )

    data = json.loads(
        SCHEMA_PATH.read_text(
            encoding="utf-8"
        )
    )

    schema = FormSchema.model_validate(data)

    generated = generate_deterministic_cases(schema)

    output = {
        "form_name": schema.form_name,
        "schema_hash": schema.schema_hash,
        "generated_by": "deterministic",
        "model": "schema-rules-v1",
        "total_fields": len(generated),
        "total_cases": sum(
            len(case_set.cases)
            for case_set in generated.values()
        ),
        "fields": {
            field_name: case_set.model_dump(
                mode="json"
            )
            for field_name, case_set in generated.items()
        },
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("=" * 80)
    print("AI-SDET DETERMINISTIC CASE GENERATION")
    print("=" * 80)
    print(f"Form                 : {schema.form_name}")
    print(f"Schema Hash          : {schema.schema_hash}")
    print(f"Fields               : {len(generated)}")
    print(
        f"Generated cases      : "
        f"{output['total_cases']}"
    )
    print(
        f"Output               : "
        f"{OUTPUT_PATH}"
    )
    print("=" * 80)

    for field_name, case_set in generated.items():
        print(
            f"{field_name:<45} "
            f"{len(case_set.cases):>3} cases"
        )


if __name__ == "__main__":
    main()