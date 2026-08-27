"""
Deterministic QA case generator for AI-SDET.

This module generates test scenarios from authoritative FormSchema
metadata without using Gemini.

Design principle:
    Schema > Human QA rules > Gemini suggestions

Gemini must never replace deterministic expectations already defined
by the authoritative schema.
"""

from __future__ import annotations

import re
from typing import Any

from .models import (
    FieldSchema,
    FormSchema,
    GeneratedCase,
    GeneratedCaseSet,
)


# ============================================================
# GENERATOR
# ============================================================


class DeterministicCaseGenerator:
    """Generate deterministic QA cases from a normalized FormSchema."""

    def __init__(self, schema: FormSchema):
        self.schema = schema

    # --------------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------------

    def generate_for_field(
        self,
        field: FieldSchema,
    ) -> GeneratedCaseSet:
        """Generate deterministic cases for one field."""

        qualified_name = (
            field.qualified_name
            or field.name
        )

        cases: list[GeneratedCase] = []

        self._add_positive_cases(field, cases)
        self._add_required_cases(field, cases)
        self._add_pattern_cases(field, cases)
        self._add_length_cases(field, cases)
        self._add_range_cases(field, cases)
        self._add_type_cases(field, cases)
        self._add_option_cases(field, cases)
        self._add_business_rule_cases(field, cases)

        cases = self._deduplicate_cases(cases)

        return GeneratedCaseSet(
            form_name=self.schema.form_name,
            field_name=qualified_name,
            schema_hash=self.schema.schema_hash,
            generated_by="deterministic",
            model="schema-rules-v1",
            cases=cases,
        )

    def generate_all(self) -> dict[str, GeneratedCaseSet]:
        """Generate deterministic cases for every field."""

        result: dict[str, GeneratedCaseSet] = {}

        for field in self.schema.fields:
            qualified_name = (
                field.qualified_name
                or field.name
            )

            result[qualified_name] = self.generate_for_field(field)

        return result

    # --------------------------------------------------------
    # POSITIVE
    # --------------------------------------------------------

    def _add_positive_cases(
        self,
        field: FieldSchema,
        cases: list[GeneratedCase],
    ) -> None:

        value = self._positive_value(field)

        if value is None:
            return

        self._add_case(
            cases=cases,
            field=field,
            category="POSITIVE",
            title="Valid value is accepted",
            value=value,
            expected_action="accept",
            rationale=(
                "Value is generated from the field's authoritative "
                "schema metadata."
            ),
        )

    # --------------------------------------------------------
    # REQUIRED / EMPTY
    # --------------------------------------------------------

    def _add_required_cases(
        self,
        field: FieldSchema,
        cases: list[GeneratedCase],
    ) -> None:

        if not field.required:
            return

        for value, title in [
            ("", "Empty value is rejected"),
            (None, "Null value is rejected"),
        ]:
            self._add_case(
                cases=cases,
                field=field,
                category="EMPTY_NULL",
                title=title,
                value=value,
                expected_action="reject",
                rationale=(
                    "Field is marked required in the authoritative schema."
                ),
            )

    # --------------------------------------------------------
    # REGEX / PATTERN
    # --------------------------------------------------------

    def _add_pattern_cases(
        self,
        field: FieldSchema,
        cases: list[GeneratedCase],
    ) -> None:

        if not field.pattern:
            return

        valid = self._positive_value(field)

        if valid is None:
            return

        invalid_values = self._invalid_pattern_values(
            field.pattern,
            field.input_type,
            valid,
        )

        for index, value in enumerate(
            invalid_values,
            start=1,
        ):
            self._add_case(
                cases=cases,
                field=field,
                category="FORMAT",
                title=f"Invalid pattern format #{index}",
                value=value,
                expected_action="reject",
                rationale=(
                    f"Value intentionally violates the authoritative "
                    f"regex: {field.pattern}"
                ),
            )

    # --------------------------------------------------------
    # LENGTH
    # --------------------------------------------------------

    def _add_length_cases(
        self,
        field: FieldSchema,
        cases: list[GeneratedCase],
    ) -> None:

        if (
            field.min_length is None
            and field.max_length is None
        ):
            return

        if field.min_length is not None:
            below = max(field.min_length - 1, 0)

            self._add_case(
                cases=cases,
                field=field,
                category="BOUNDARY",
                title="Below minimum length",
                value="A" * below,
                expected_action="reject",
                rationale=(
                    "Value is one character below the schema-defined "
                    "minimum length."
                ),
            )

            self._add_case(
                cases=cases,
                field=field,
                category="BOUNDARY",
                title="Minimum allowed length",
                value="A" * field.min_length,
                expected_action="accept",
                rationale=(
                    "Value is exactly the schema-defined minimum length."
                ),
            )

        if field.max_length is not None:
            self._add_case(
                cases=cases,
                field=field,
                category="BOUNDARY",
                title="Maximum allowed length",
                value="A" * field.max_length,
                expected_action="accept",
                rationale=(
                    "Value is exactly the schema-defined maximum length."
                ),
            )

            self._add_case(
                cases=cases,
                field=field,
                category="BOUNDARY",
                title="Above maximum length",
                value="A" * (field.max_length + 1),
                expected_action="reject",
                rationale=(
                    "Value is one character above the schema-defined "
                    "maximum length."
                ),
            )

    # --------------------------------------------------------
    # NUMERIC RANGE
    # --------------------------------------------------------

    def _add_range_cases(
        self,
        field: FieldSchema,
        cases: list[GeneratedCase],
    ) -> None:

        if (
            field.minimum is None
            and field.maximum is None
        ):
            return

        if field.minimum is not None:
            self._add_case(
                cases=cases,
                field=field,
                category="BOUNDARY",
                title="Minimum numeric value",
                value=field.minimum,
                expected_action="accept",
                rationale=(
                    "Value equals the schema-defined minimum."
                ),
            )

            self._add_case(
                cases=cases,
                field=field,
                category="BOUNDARY",
                title="Below minimum numeric value",
                value=field.minimum - 1,
                expected_action="reject",
                rationale=(
                    "Value is below the schema-defined minimum."
                ),
            )

        if field.maximum is not None:
            self._add_case(
                cases=cases,
                field=field,
                category="BOUNDARY",
                title="Maximum numeric value",
                value=field.maximum,
                expected_action="accept",
                rationale=(
                    "Value equals the schema-defined maximum."
                ),
            )

            self._add_case(
                cases=cases,
                field=field,
                category="BOUNDARY",
                title="Above maximum numeric value",
                value=field.maximum + 1,
                expected_action="reject",
                rationale=(
                    "Value is above the schema-defined maximum."
                ),
            )

    # --------------------------------------------------------
    # INPUT TYPE
    # --------------------------------------------------------

    def _add_type_cases(
        self,
        field: FieldSchema,
        cases: list[GeneratedCase],
    ) -> None:

        if field.input_type == "email":
            self._add_case(
                cases,
                field,
                "FORMAT",
                "Invalid email format",
                "not-an-email",
                "reject",
                "Value does not follow email format.",
            )

        elif field.input_type == "url":
            self._add_case(
                cases,
                field,
                "FORMAT",
                "Invalid URL format",
                "not-a-url",
                "reject",
                "Value does not follow URL format.",
            )

        elif field.input_type in {
            "number",
            "integer",
        }:
            self._add_case(
                cases,
                field,
                "FORMAT",
                "Non-numeric value",
                "abc",
                "reject",
                "Value is incompatible with numeric input type.",
            )

        elif field.input_type == "date":
            self._add_case(
                cases,
                field,
                "FORMAT",
                "Invalid date format",
                "not-a-date",
                "reject",
                "Value does not represent a valid date format.",
            )

        elif field.input_type in {
            "text",
            "textarea",
            "password",
            "tel",
        }:
            self._add_case(
                cases,
                field,
                "SPECIAL_UNICODE",
                "Unicode value",
                "José Kumar",
                "observe_only",
                (
                    "Unicode handling should be verified unless the "
                    "schema explicitly restricts the character set."
                ),
            )

    # --------------------------------------------------------
    # OPTIONS
    # --------------------------------------------------------

    def _add_option_cases(
        self,
        field: FieldSchema,
        cases: list[GeneratedCase],
    ) -> None:

        if field.options:
            if field.options:
                self._add_case(
                    cases=cases,
                    field=field,
                    category="POSITIVE",
                    title="Valid configured option",
                    value=field.options[0],
                    expected_action="accept",
                    rationale=(
                        "Value is one of the authoritative configured "
                        "field options."
                    ),
                )

                self._add_case(
                    cases=cases,
                    field=field,
                    category="NEGATIVE",
                    title="Invalid configured option",
                    value="__INVALID_OPTION__",
                    expected_action="reject",
                    rationale=(
                        "Value is not present in the authoritative "
                        "options list."
                    ),
                )

        elif field.options_key:
            self._add_case(
                cases=cases,
                field=field,
                category="POSITIVE",
                title="Dynamic option resolution required",
                value=None,
                expected_action="observe_only",
                rationale=(
                    f"Field uses dynamic options_key "
                    f"'{field.options_key}'. Actual option values "
                    "must be resolved at runtime."
                ),
            )

    # --------------------------------------------------------
    # BUSINESS RULES
    # --------------------------------------------------------

    def _add_business_rule_cases(
        self,
        field: FieldSchema,
        cases: list[GeneratedCase],
    ) -> None:

        for rule in field.cross_validations:

            rule_type = rule.get("type")
            compare_to = rule.get("compare_to_field")

            if not compare_to:
                continue

            if rule_type == "not_equal":
                self._add_case(
                    cases=cases,
                    field=field,
                    category="BUSINESS_RULE",
                    title="Cross-field values must differ",
                    value={
                        "field": (
                            field.qualified_name
                            or field.name
                        ),
                        "compare_to": compare_to,
                        "scenario": "same_value",
                    },
                    expected_action="reject",
                    rationale=(
                        "Cross-validation requires the two fields "
                        "to contain different values."
                    ),
                )

            elif rule_type == "equal":
                self._add_case(
                    cases=cases,
                    field=field,
                    category="BUSINESS_RULE",
                    title="Cross-field values must match",
                    value={
                        "field": (
                            field.qualified_name
                            or field.name
                        ),
                        "compare_to": compare_to,
                        "scenario": "different_value",
                    },
                    expected_action="reject",
                    rationale=(
                        "Cross-validation requires matching values."
                    ),
                )

            else:
                self._add_case(
                    cases=cases,
                    field=field,
                    category="BUSINESS_RULE",
                    title=f"Cross-validation: {rule_type}",
                    value={
                        "field": (
                            field.qualified_name
                            or field.name
                        ),
                        "compare_to": compare_to,
                    },
                    expected_action="observe_only",
                    rationale=(
                        "Cross-field behaviour is defined by the "
                        "authoritative schema and requires runtime "
                        "evaluation."
                    ),
                )

        for rule in field.section_rules:

            rule_id = rule.get("id")

            self._add_case(
                cases=cases,
                field=field,
                category="BUSINESS_RULE",
                title=(
                    f"Section rule: {rule_id}"
                    if rule_id
                    else "Section business rule"
                ),
                value=rule,
                expected_action="observe_only",
                rationale=(
                    "Repeatable-section behaviour is defined by an "
                    "authoritative section rule and requires runtime "
                    "evaluation."
                ),
            )

    # --------------------------------------------------------
    # VALUE GENERATION
    # --------------------------------------------------------

    def _positive_value(
        self,
        field: FieldSchema,
    ) -> Any:

        if field.options:
            return field.options[0]

        if field.input_type == "checkbox":
            return True

        if field.input_type in {
            "number",
            "integer",
        }:
            if field.minimum is not None:
                return field.minimum

            return 1

        if field.input_type == "date":
            return "2000-01-01"

        if field.input_type == "email":
            return "qa@example.com"

        if field.input_type == "url":
            return "https://example.com"

        if field.input_type == "file":
            return None

        if field.input_type in {
            "dropdown",
            "multi_select",
            "radio",
        }:
            if field.options_key:
                return None

            return None

        if field.input_type in {
            "text",
            "textarea",
            "tel",
            "password",
            "unknown",
        }:
            return "Valid Test Value"

        return None

    # --------------------------------------------------------
    # INVALID PATTERN VALUES
    # --------------------------------------------------------

    def _invalid_pattern_values(
        self,
        pattern: str,
        input_type: str,
        valid_value: Any,
    ) -> list[Any]:

        values: list[Any] = []

        if input_type in {
            "number",
            "integer",
        }:
            values.extend([
                "abc",
                "12abc",
                "!@#",
            ])

        elif input_type == "date":
            values.extend([
                "01-01-2000",
                "2000/01/01",
                "not-a-date",
            ])

        else:
            values.extend([
                "",
                "INVALID",
                "12345678901234567890",
                "!!!@@@###",
            ])

        # Make sure the generated values actually violate the regex.
        result: list[Any] = []

        for value in values:
            try:
                if not re.fullmatch(
                    pattern,
                    str(value),
                ):
                    result.append(value)
            except re.error:
                # SchemaValidator should already catch invalid regex.
                pass

        return result

    # --------------------------------------------------------
    # CASE CREATION
    # --------------------------------------------------------

    def _add_case(
        self,
        cases: list[GeneratedCase],
        field: FieldSchema,
        category: str,
        title: str,
        value: Any,
        expected_action: str,
        rationale: str,
    ) -> None:

        qualified_name = (
            field.qualified_name
            or field.name
        )

        case_id = self._case_id(
            qualified_name,
            category,
            title,
        )

        cases.append(
            GeneratedCase(
                case_id=case_id,
                field=qualified_name,
                category=category,
                title=title,
                value=value,
                expected_action=expected_action,
                expectation_source="schema",
                rationale=rationale,
                applicable=True,
            )
        )

    # --------------------------------------------------------
    # DEDUPLICATION
    # --------------------------------------------------------

    def _deduplicate_cases(
        self,
        cases: list[GeneratedCase],
    ) -> list[GeneratedCase]:

        seen: set[tuple[str, str, str]] = set()
        result: list[GeneratedCase] = []

        for case in cases:
            key = (
                case.field,
                case.category,
                case.title,
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(case)

        return result

    # --------------------------------------------------------
    # CASE ID
    # --------------------------------------------------------

    @staticmethod
    def _case_id(
        field: str,
        category: str,
        title: str,
    ) -> str:

        safe_field = re.sub(
            r"[^a-zA-Z0-9]+",
            "_",
            field,
        ).strip("_").lower()

        safe_title = re.sub(
            r"[^a-zA-Z0-9]+",
            "_",
            title,
        ).strip("_").lower()

        return (
            f"{safe_field}__"
            f"{category.lower()}__"
            f"{safe_title}"
        )


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================


def generate_deterministic_cases(
    schema: FormSchema,
) -> dict[str, GeneratedCaseSet]:
    """Generate deterministic cases for the complete schema."""

    return DeterministicCaseGenerator(schema).generate_all()