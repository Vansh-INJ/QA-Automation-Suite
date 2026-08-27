"""
Schema validation layer for AI-SDET.

Validates the normalized FormSchema before it is consumed by:
    - QA rule generation
    - option resolution
    - test generation
    - Gemini
    - test execution

This module does NOT execute UI/API tests.
It only verifies that the discovered schema is internally consistent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .models import FieldSchema, FormSchema


# ============================================================
# RESULT CONTRACT
# ============================================================


@dataclass
class ValidationIssue:
    severity: str
    code: str
    message: str
    field: str | None = None


@dataclass
class SchemaValidationResult:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    total_fields: int = 0
    unique_qualified_names: int = 0
    repeatable_fields: int = 0
    fields_with_validation: int = 0
    fields_with_regex: int = 0
    fields_with_options: int = 0
    fields_with_options_key: int = 0
    cross_validations: int = 0
    fields_with_conditions: int = 0
    conditions: int = 0
    fields_with_section_rules: int = 0
    section_rules: int = 0

    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "ERROR"]

    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "WARNING"]


# ============================================================
# VALIDATOR
# ============================================================


class SchemaValidator:
    """Validates a normalized AI-SDET FormSchema."""

    VALID_INPUT_TYPES = {
        "text",
        "textarea",
        "email",
        "number",
        "integer",
        "tel",
        "url",
        "date",
        "datetime",
        "time",
        "month",
        "week",
        "password",
        "dropdown",
        "multi_select",
        "checkbox",
        "radio",
        "file",
        "unknown",
    }

    VALID_CROSS_TYPES = {
        "not_equal",
        "equal",
        "greater_than",
        "less_than",
        "greater_than_or_equal",
        "less_than_or_equal",
    }

    VALID_SCOPES = {
        "local",
        "global",
    }

    def __init__(self, schema: FormSchema):
        self.schema = schema
        self.issues: list[ValidationIssue] = []

        self.fields_by_qualified_name = {
            field.qualified_name or field.name: field
            for field in schema.fields
        }

    # --------------------------------------------------------
    # PUBLIC
    # --------------------------------------------------------

    def validate(self) -> SchemaValidationResult:
        """Run all schema validation checks."""

        self._validate_form_metadata()
        self._validate_fields()
        self._validate_unique_names()
        self._validate_regex()
        self._validate_cross_validations()
        self._validate_conditions()
        self._validate_section_rules()
        self._validate_references()

        return self._build_result()

    # --------------------------------------------------------
    # FORM
    # --------------------------------------------------------

    def _validate_form_metadata(self) -> None:
        if not self.schema.form_name:
            self._error(
                "MISSING_FORM_NAME",
                "Form schema is missing form_name.",
            )

        if not self.schema.source:
            self._error(
                "MISSING_SOURCE",
                "Form schema is missing source.",
            )

        if not self.schema.fields:
            self._error(
                "NO_FIELDS",
                "Form schema contains no fields.",
            )

        if not self.schema.schema_hash:
            self._error(
                "MISSING_SCHEMA_HASH",
                "Form schema is missing schema_hash.",
            )

    # --------------------------------------------------------
    # FIELDS
    # --------------------------------------------------------

    def _validate_fields(self) -> None:
        for field in self.schema.fields:

            qualified_name = field.qualified_name or field.name

            if not field.name:
                self._error(
                    "MISSING_FIELD_NAME",
                    "Field is missing name.",
                    qualified_name,
                )

            if field.input_type not in self.VALID_INPUT_TYPES:
                self._error(
                    "INVALID_INPUT_TYPE",
                    f"Unsupported input type: {field.input_type}",
                    qualified_name,
                )

            if field.required and field.input_type == "unknown":
                self._warning(
                    "REQUIRED_UNKNOWN_TYPE",
                    "Required field has unknown input type.",
                    qualified_name,
                )

            if field.options_key and field.options:
                self._warning(
                    "STATIC_AND_DYNAMIC_OPTIONS",
                    "Field contains both options and options_key.",
                    qualified_name,
                )

            if field.minimum is not None and field.maximum is not None:
                if field.minimum > field.maximum:
                    self._error(
                        "INVALID_RANGE",
                        "minimum is greater than maximum.",
                        qualified_name,
                    )

            if field.min_length is not None and field.max_length is not None:
                if field.min_length > field.max_length:
                    self._error(
                        "INVALID_LENGTH_RANGE",
                        "min_length is greater than max_length.",
                        qualified_name,
                    )

    # --------------------------------------------------------
    # UNIQUE NAMES
    # --------------------------------------------------------

    def _validate_unique_names(self) -> None:
        names: dict[str, int] = {}

        for field in self.schema.fields:
            name = field.qualified_name or field.name
            names[name] = names.get(name, 0) + 1

        for name, count in names.items():
            if count > 1:
                self._error(
                    "DUPLICATE_QUALIFIED_NAME",
                    f"Qualified field name appears {count} times.",
                    name,
                )

    # --------------------------------------------------------
    # REGEX
    # --------------------------------------------------------

    def _validate_regex(self) -> None:
        for field in self.schema.fields:

            if not field.pattern:
                continue

            qualified_name = field.qualified_name or field.name

            try:
                re.compile(field.pattern)
            except re.error as exc:
                self._error(
                    "INVALID_REGEX",
                    f"Regex cannot be compiled: {exc}",
                    qualified_name,
                )

    # --------------------------------------------------------
    # CROSS VALIDATIONS
    # --------------------------------------------------------

    def _validate_cross_validations(self) -> None:

        for field in self.schema.fields:

            qualified_name = field.qualified_name or field.name

            for rule in field.cross_validations:

                rule_type = rule.get("type")

                if rule_type not in self.VALID_CROSS_TYPES:
                    self._error(
                        "INVALID_CROSS_VALIDATION_TYPE",
                        f"Unsupported cross-validation type: {rule_type}",
                        qualified_name,
                    )

                scope = rule.get("scope")

                if scope not in self.VALID_SCOPES:
                    self._error(
                        "INVALID_CROSS_VALIDATION_SCOPE",
                        f"Unsupported cross-validation scope: {scope}",
                        qualified_name,
                    )

                compare_to = rule.get("compare_to_field")

                if not compare_to:
                    self._error(
                        "MISSING_COMPARE_FIELD",
                        "Cross-validation is missing compare_to_field.",
                        qualified_name,
                    )

    # --------------------------------------------------------
    # CONDITIONS
    # --------------------------------------------------------

    def _validate_conditions(self) -> None:

        for field in self.schema.fields:

            qualified_name = field.qualified_name or field.name

            for condition in field.conditions:

                if not condition.get("id"):
                    self._error(
                        "CONDITION_MISSING_ID",
                        "Condition is missing id.",
                        qualified_name,
                    )

                trigger = condition.get("trigger")

                if not isinstance(trigger, dict):
                    self._error(
                        "CONDITION_MISSING_TRIGGER",
                        "Condition must contain a trigger object.",
                        qualified_name,
                    )
                    continue

                if not trigger.get("event"):
                    self._error(
                        "CONDITION_MISSING_EVENT",
                        "Condition trigger is missing event.",
                        qualified_name,
                    )

                if "operator" not in trigger:
                    self._error(
                        "CONDITION_MISSING_OPERATOR",
                        "Condition trigger is missing operator.",
                        qualified_name,
                    )

                actions = condition.get("actions")

                if not isinstance(actions, list) or not actions:
                    self._error(
                        "CONDITION_MISSING_ACTIONS",
                        "Condition must contain at least one action.",
                        qualified_name,
                    )

    # --------------------------------------------------------
    # SECTION RULES
    # --------------------------------------------------------

    def _validate_section_rules(self) -> None:

        for field in self.schema.fields:

            qualified_name = field.qualified_name or field.name

            for rule in field.section_rules:

                if not rule.get("id"):
                    self._error(
                        "SECTION_RULE_MISSING_ID",
                        "Section rule is missing id.",
                        qualified_name,
                    )

                if not rule.get("type"):
                    self._error(
                        "SECTION_RULE_MISSING_TYPE",
                        "Section rule is missing type.",
                        qualified_name,
                    )

    # --------------------------------------------------------
    # REFERENCES
    # --------------------------------------------------------

    def _validate_references(self) -> None:

        for field in self.schema.fields:

            qualified_name = field.qualified_name or field.name

            # ----------------------------------------------
            # Cross-validation references
            # ----------------------------------------------

            for rule in field.cross_validations:

                compare_to = rule.get("compare_to_field")

                if not compare_to:
                    continue

                resolved = self._resolve_reference(
                    field,
                    compare_to,
                    rule.get("scope"),
                )

                if resolved is None:
                    self._error(
                        "INVALID_FIELD_REFERENCE",
                        f"compare_to_field '{compare_to}' "
                        f"cannot be resolved.",
                        qualified_name,
                    )

            # ----------------------------------------------
            # Condition section references
            # ----------------------------------------------

            for condition in field.conditions:

                for action in condition.get("actions", []):

                    source_section = action.get("source_section")
                    target_section = action.get("target_section")

                    if source_section and not self._section_exists(
                        source_section
                    ):
                        self._error(
                            "INVALID_SOURCE_SECTION",
                            f"Unknown source section '{source_section}'.",
                            qualified_name,
                        )

                    if target_section and not self._section_exists(
                        target_section
                    ):
                        self._error(
                            "INVALID_TARGET_SECTION",
                            f"Unknown target section '{target_section}'.",
                            qualified_name,
                        )

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------

    def _resolve_reference(
        self,
        source_field: FieldSchema,
        reference: str,
        scope: str | None,
    ) -> FieldSchema | None:

        # Global reference:
        #
        # communication.primary_phone
        #
        if scope == "global" or "." in reference:
            return self.fields_by_qualified_name.get(reference)

        # Local reference:
        #
        # primary_phone
        #
        source_section = source_field.section_key

        if source_section:
            local_name = f"{source_section}.{reference}"

            return self.fields_by_qualified_name.get(local_name)

        return self.fields_by_qualified_name.get(reference)

    def _section_exists(self, section_key: str) -> bool:

        return any(
            field.section_key == section_key
            for field in self.schema.fields
        )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    def _build_result(self) -> SchemaValidationResult:

        fields = self.schema.fields

        result = SchemaValidationResult(
            valid=not any(
                issue.severity == "ERROR"
                for issue in self.issues
            ),
            issues=self.issues,
            total_fields=len(fields),
            unique_qualified_names=len(
                {
                    field.qualified_name or field.name
                    for field in fields
                }
            ),
            repeatable_fields=sum(
                1 for field in fields if field.repeatable
            ),
            fields_with_validation=sum(
                1 for field in fields if field.validation
            ),
            fields_with_regex=sum(
                1 for field in fields if field.pattern
            ),
            fields_with_options=sum(
                1 for field in fields if field.options
            ),
            fields_with_options_key=sum(
                1 for field in fields if field.options_key
            ),
            cross_validations=sum(
                len(field.cross_validations)
                for field in fields
            ),
            fields_with_conditions=sum(
                1 for field in fields if field.conditions
            ),
            conditions=sum(
                len(field.conditions)
                for field in fields
            ),
            fields_with_section_rules=sum(
                1 for field in fields if field.section_rules
            ),
            section_rules=self._count_unique_section_rules(),
        )

        return result

    def _count_unique_section_rules(self) -> int:

        rule_ids: set[str] = set()

        for field in self.schema.fields:
            for rule in field.section_rules:
                rule_id = rule.get("id")

                if rule_id:
                    rule_ids.add(rule_id)

        return len(rule_ids)

    # --------------------------------------------------------
    # ISSUE HELPERS
    # --------------------------------------------------------

    def _error(
        self,
        code: str,
        message: str,
        field: str | None = None,
    ) -> None:

        self.issues.append(
            ValidationIssue(
                severity="ERROR",
                code=code,
                message=message,
                field=field,
            )
        )

    def _warning(
        self,
        code: str,
        message: str,
        field: str | None = None,
    ) -> None:

        self.issues.append(
            ValidationIssue(
                severity="WARNING",
                code=code,
                message=message,
                field=field,
            )
        )


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================


def validate_schema(schema: FormSchema) -> SchemaValidationResult:
    """Validate a FormSchema in one call."""
    return SchemaValidator(schema).validate()


# ============================================================
# CLI
# ============================================================

def main() -> None:
    import json
    from pathlib import Path

    schema_path = Path("ai_form_testing/form_schema.json")

    if not schema_path.exists():
        print(f"[ERROR] Schema file not found: {schema_path}")
        raise SystemExit(1)

    try:
        data = json.loads(
            schema_path.read_text(encoding="utf-8")
        )

        schema = FormSchema.model_validate(data)

    except Exception as exc:
        print("=" * 80)
        print("AI-SDET SCHEMA VALIDATION")
        print("=" * 80)
        print(f"[ERROR] Could not load schema:")
        print(exc)
        raise SystemExit(1)

    result = validate_schema(schema)

    print("=" * 80)
    print("AI-SDET SCHEMA VALIDATION")
    print("=" * 80)

    print(f"Form                 : {schema.form_name}")
    print(f"Source               : {schema.source}")
    print(f"Schema Hash          : {schema.schema_hash}")
    print()

    print("-" * 80)
    print("VALIDATION SUMMARY")
    print("-" * 80)

    print(f"Valid                : {result.valid}")
    print(f"Total fields         : {result.total_fields}")
    print(f"Unique qualified     : {result.unique_qualified_names}")
    print(f"Repeatable fields    : {result.repeatable_fields}")
    print(f"With validation      : {result.fields_with_validation}")
    print(f"With regex           : {result.fields_with_regex}")
    print(f"With options         : {result.fields_with_options}")
    print(f"With options key     : {result.fields_with_options_key}")
    print(f"Cross-validations    : {result.cross_validations}")
    print(f"Fields with conditions: {result.fields_with_conditions}")
    print(f"Conditions           : {result.conditions}")
    print(f"Fields with rules    : {result.fields_with_section_rules}")
    print(f"Section rules        : {result.section_rules}")
    print()

    print("-" * 80)
    print("ISSUES")
    print("-" * 80)

    if not result.issues:
        print("No validation issues found.")
    else:
        for issue in result.issues:
            location = f" [{issue.field}]" if issue.field else ""

            print(
                f"{issue.severity:<8} "
                f"{issue.code:<35} "
                f"{issue.message}{location}"
            )

    print()
    print("=" * 80)

    if result.valid:
        print("RESULT: SCHEMA VALID")
    else:
        print("RESULT: SCHEMA INVALID")

    print("=" * 80)

    if not result.valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()