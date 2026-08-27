"""Typed contracts for the AI-SDET form intelligence layer.

These models are intentionally independent from the existing HRMS
automation framework.

They define the contract between:

    schema discovery
    deterministic QA rules
    Gemini generation
    test execution
    caching
    reporting

The schema model is deliberately rich because it represents the
actual HRMS form-testing contract, not merely the DOM structure.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


InputType = Literal[
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
]


class FieldSchema(BaseModel):
    """Normalized representation of one form field."""

    # ---------------------------------------------------------
    # IDENTITY
    # ---------------------------------------------------------

    name: str

    qualified_name: str | None = None

    field_id: str | None = None

    label: str | None = None

    # ---------------------------------------------------------
    # SECTION CONTEXT
    # ---------------------------------------------------------

    section_key: str | None = None

    section_title: str | None = None

    section_index: int | None = None

    field_index: int | None = None

    section_path: str | None = None

    # ---------------------------------------------------------
    # FIELD BEHAVIOUR
    # ---------------------------------------------------------

    input_type: InputType = "unknown"

    required: bool = False

    repeatable: bool = False

    # ---------------------------------------------------------
    # DETERMINISTIC VALIDATION
    # ---------------------------------------------------------

    min_length: int | None = None

    max_length: int | None = None

    minimum: float | None = None

    maximum: float | None = None

    pattern: str | None = None

    validation: str | None = None

    # ---------------------------------------------------------
    # OPTIONS / LOOKUPS
    # ---------------------------------------------------------

    options: list[str] = Field(default_factory=list)

    options_key: str | None = None

    lookup_key: str | None = None

    # ---------------------------------------------------------
    # UI METADATA
    # ---------------------------------------------------------

    placeholder: str | None = None

    ui_config: dict[str, Any] = Field(
        default_factory=dict
    )

    # ---------------------------------------------------------
    # BUSINESS RULES
    # ---------------------------------------------------------

    constraints: dict[str, Any] = Field(
        default_factory=dict
    )

    cross_validations: list[dict[str, Any]] = Field(
        default_factory=list
    )

    conditions: list[dict[str, Any]] = Field(
        default_factory=list
    )

    section_rules: list[dict[str, Any]] = Field(
        default_factory=list
    )

    messages: dict[str, Any] = Field(
        default_factory=dict
    )

    # ---------------------------------------------------------
    # SOURCE / DEBUG
    # ---------------------------------------------------------

    source: Literal["api", "dom", "merged"] = "dom"

    raw: dict[str, Any] = Field(
        default_factory=dict
    )


class FormSchema(BaseModel):
    """Complete normalized form schema."""

    form_name: str

    source: Literal["api", "dom", "merged"]

    fetched_at: str

    fields: list[FieldSchema]

    schema_hash: str

    raw_schema: dict[str, Any] | None = None


# =============================================================
# AI GENERATED TEST CONTRACT
# =============================================================


CaseCategory = Literal[
    "POSITIVE",
    "NEGATIVE",
    "BOUNDARY",
    "FORMAT",
    "EMPTY_NULL",
    "SPECIAL_UNICODE",
    "SECURITY_ROBUSTNESS",
    "BUSINESS_RULE",
]


ExpectedAction = Literal[
    "accept",
    "reject",
    "observe_only",
]


class GeneratedCase(BaseModel):
    """One generated test scenario."""

    case_id: str

    # Qualified field identity should be used here.
    field: str

    category: CaseCategory

    title: str

    value: Any

    expected_action: ExpectedAction

    expectation_source: Literal[
        "schema",
        "qa_rule",
        "gemini_review",
    ]

    rationale: str

    applicable: bool = True


class GeneratedCaseSet(BaseModel):
    """Complete generated case collection for one field."""

    form_name: str

    field_name: str

    schema_hash: str

    generated_by: str

    model: str

    cases: list[GeneratedCase]