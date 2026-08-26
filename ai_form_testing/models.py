"""Typed contracts for the AI-SDET form intelligence layer.

These models are deliberately independent from the existing HRMS automation.
They define the contract between schema discovery, Gemini generation, caching,
execution, and reporting.
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
    "dropdown",
    "checkbox",
    "radio",
    "file",
    "unknown",
]


class FieldSchema(BaseModel):
    name: str
    field_id: str | None = None
    label: str | None = None
    input_type: InputType = "unknown"
    required: bool = False
    min_length: int | None = None
    max_length: int | None = None
    minimum: float | None = None
    maximum: float | None = None
    pattern: str | None = None
    options: list[str] = Field(default_factory=list)
    placeholder: str | None = None
    source: Literal["api", "dom", "merged"] = "dom"
    raw: dict[str, Any] = Field(default_factory=dict)


class FormSchema(BaseModel):
    form_name: str
    source: Literal["api", "dom", "merged"]
    fetched_at: str
    fields: list[FieldSchema]
    schema_hash: str
    raw_schema: dict[str, Any] | None = None


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


ExpectedAction = Literal["accept", "reject", "observe_only"]


class GeneratedCase(BaseModel):
    case_id: str
    field: str
    category: CaseCategory
    title: str
    value: Any
    expected_action: ExpectedAction
    expectation_source: Literal["schema", "qa_rule", "gemini_review"]
    rationale: str
    applicable: bool = True


class GeneratedCaseSet(BaseModel):
    form_name: str
    field_name: str
    schema_hash: str
    generated_by: str
    model: str
    cases: list[GeneratedCase]
