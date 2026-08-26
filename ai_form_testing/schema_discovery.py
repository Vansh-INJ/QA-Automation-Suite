"""
Phase 1: discover and normalize the live onboarding form schema.

Preferred source:

    GET /api/onboarding/meta/form-schema

Fallback:

    Playwright DOM introspection.

This module does not call Gemini and does not submit or mutate HRMS data.

The API schema is treated as the authoritative source of truth. We preserve
field-level validation metadata and section-level business rules so later
deterministic and AI-assisted QA layers can reason from the actual HRMS
contract rather than guessing.
"""

from __future__ import annotations

from pathlib import Path

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

import requests
from playwright.sync_api import Page

from .config import AIConfig
from .models import FieldSchema, FormSchema


def _clean(value: Any) -> Any:
    """Recursively make values safe for JSON serialization."""
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_clean(v) for v in value]

    return value


def _hash_fields(fields: list[FieldSchema]) -> str:
    """
    Create a stable hash from normalized fields.

    Raw payload data is intentionally excluded because it can contain
    transport/source details that should not affect the normalized contract hash.
    """
    canonical = [
        field.model_dump(exclude={"raw"})
        for field in sorted(
            fields,
            key=lambda item: (
                str(item.raw.get("section_path", "")),
                item.name,
                str(item.raw.get("path", "")),
            ),
        )
    ]

    payload = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _infer_input_type(
    input_type: str | None,
    tag: str | None = None,
    role: str | None = None,
) -> str:
    """
    Normalize HTML/DOM/API field types into our internal QA categories.

    IMPORTANT:
    The HRMS API explicitly returns values such as:
        type = "select"
        type = "avatar"
        type = "date"
        type = "checkbox"

    Therefore API types must be handled here instead of being marked unknown.
    """
    value = (input_type or "").strip().lower()
    normalized_tag = (tag or "").strip().lower()
    normalized_role = (role or "").strip().lower()

    mapping = {
        # Standard HTML inputs
        "text": "text",
        "email": "email",
        "number": "number",
        "tel": "tel",
        "url": "url",
        "date": "date",
        "datetime": "datetime",
        "datetime-local": "datetime",
        "time": "time",
        "month": "month",
        "week": "week",
        "password": "password",
        "checkbox": "checkbox",
        "radio": "radio",
        "file": "file",

        # HRMS API schema types
        "select": "dropdown",
        "dropdown": "dropdown",
        "combobox": "dropdown",
        "multi_select": "multi_select",
        "multiselect": "multi_select",
        "textarea": "textarea",
        "avatar": "file",
        "image": "file",
        "upload": "file",
    }

    if value in mapping:
        return mapping[value]

    if normalized_role == "combobox":
        return "dropdown"

    if normalized_role == "checkbox":
        return "checkbox"

    if normalized_role == "radio":
        return "radio"

    if normalized_tag == "textarea":
        return "textarea"

    if normalized_tag == "select":
        return "dropdown"

    return "unknown"


def discover_from_dom(
    page: Page,
    form_name: str = "onboarding_add_employee",
) -> FormSchema:
    """
    Inspect the currently rendered form without submitting it.

    DOM discovery remains a fallback. The API schema is preferred whenever
    available because it contains validation and business-rule metadata.
    """
    raw_fields = page.locator(
        "input:not([type='hidden']), textarea, select, "
        "[role='combobox'], [role='checkbox'], [role='radio']"
    )

    fields: list[FieldSchema] = []

    for index in range(raw_fields.count()):
        element = raw_fields.nth(index)

        try:
            tag = element.evaluate("(el) => el.tagName.toLowerCase()")
            field_id = element.get_attribute("id")
            name = element.get_attribute("name")
            role = element.get_attribute("role")
            html_type = element.get_attribute("type")
            placeholder = element.get_attribute("placeholder")

            required = bool(
                element.get_attribute("required") is not None
                or element.get_attribute("aria-required") == "true"
            )

            field_name = name or field_id or f"unnamed_field_{index}"

            options: list[str] = []

            if tag == "select":
                options = element.locator("option").all_text_contents()

            elif role == "combobox":
                options = element.locator(
                    "[role='option']"
                ).all_text_contents()

            options = [
                text.strip()
                for text in options
                if text.strip()
                and text.strip().lower()
                not in {
                    "select",
                    "select...",
                    "select option",
                    "choose",
                    "choose...",
                }
            ]

            max_length = element.get_attribute("maxlength")
            min_length = element.get_attribute("minlength")
            minimum = element.get_attribute("min")
            maximum = element.get_attribute("max")
            pattern = element.get_attribute("pattern")

            label = None

            if field_id:
                label_locator = page.locator(
                    f"label[for='{field_id}']"
                ).first

                if label_locator.count():
                    label = label_locator.inner_text().strip()

            fields.append(
                FieldSchema(
                    name=field_name,
                    field_id=field_id,
                    label=label,
                    input_type=_infer_input_type(
                        html_type,
                        tag,
                        role,
                    ),
                    required=required,
                    min_length=(
                        int(min_length)
                        if min_length and min_length.isdigit()
                        else None
                    ),
                    max_length=(
                        int(max_length)
                        if max_length and max_length.isdigit()
                        else None
                    ),
                    minimum=(
                        float(minimum)
                        if _is_number(minimum)
                        else None
                    ),
                    maximum=(
                        float(maximum)
                        if _is_number(maximum)
                        else None
                    ),
                    pattern=pattern,
                    options=options,
                    placeholder=placeholder,
                    source="dom",
                    raw={
                        "dom_index": index,
                        "tag": tag,
                        "role": role,
                        "html_type": html_type,
                    },
                )
            )

        except Exception as exc:
            # Discovery should report a bad element but continue.
            fields.append(
                FieldSchema(
                    name=f"discovery_error_{index}",
                    input_type="unknown",
                    source="dom",
                    raw={
                        "error": str(exc),
                        "dom_index": index,
                    },
                )
            )

    return _finalize(
        form_name=form_name,
        source="dom",
        fields=fields,
    )


def fetch_schema_api(
    config: AIConfig | None = None,
) -> dict[str, Any]:
    """
    Fetch the backend schema using the existing project's token manager.
    """
    config = config or AIConfig.from_env()

    try:
        from api_framework.auth.token_manager import TokenManager

        headers = TokenManager.get_headers()

    except Exception as exc:
        raise RuntimeError(
            "Could not obtain HRMS API headers through the existing "
            "TokenManager. Use DOM discovery if API schema access is unavailable."
        ) from exc

    url = f"{config.base_url}{config.schema_endpoint}"

    response = requests.get(
        url,
        headers=headers,
        timeout=config.request_timeout_seconds,
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError(
            "Form schema endpoint returned "
            f"{type(payload).__name__}, expected object."
        )

    return payload


def normalize_api_schema(
    payload: dict[str, Any],
    form_name: str = "onboarding_add_employee",
) -> FormSchema:
    """
    Normalize the known HRMS form-schema API contract.

    Expected shape:

        {
            "status": "success",
            "data": {
                "sections": [
                    {
                        "key": "...",
                        "title": "...",
                        "repeatable": false,
                        "section_rules": [...],
                        "fields": [...]
                    }
                ]
            }
        }

    We intentionally preserve all useful field metadata in raw so future
    QA engines can use:
        validation
        constraints
        options_key
        lookup_key
        ui_config
        cross_validations
        conditions
        messages

    Section context is also retained so duplicate field names such as:

        addresses.current.line1
        addresses.permanent.line1

    remain distinguishable.
    """
    fields: list[FieldSchema] = []

    data = payload.get("data")

    if not isinstance(data, dict):
        raise ValueError(
            "Unexpected form schema API response: missing object at 'data'."
        )

    sections = data.get("sections")

    if not isinstance(sections, list):
        raise ValueError(
            "Unexpected form schema API response: missing list at "
            "'data.sections'."
        )

    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            continue

        section_key = str(
            section.get("key")
            or f"section_{section_index}"
        )

        section_title = (
            str(section.get("title"))
            if section.get("title") is not None
            else section_key
        )

        repeatable = bool(section.get("repeatable", False))

        section_rules = section.get("section_rules")

        if not isinstance(section_rules, list):
            section_rules = []

        section_fields = section.get("fields")

        if not isinstance(section_fields, list):
            continue

        for field_index, node in enumerate(section_fields):
            if not isinstance(node, dict):
                continue

            field = _field_from_api_node(
                node=node,
                path=(
                    f"data.sections[{section_index}]"
                    f".fields[{field_index}]"
                ),
                section_key=section_key,
                section_title=section_title,
                repeatable=repeatable,
                section_rules=section_rules,
            )

            if field:
                fields.append(field)

    if not fields:
        raise ValueError(
            "No fields were discovered from data.sections[].fields[]."
        )

    # Do NOT de-duplicate solely by field.name.
    #
    # Example:
    #   addresses.current.line1
    #   addresses.permanent.line1
    #
    # Both are valid separate fields in different sections.
    unique: dict[str, FieldSchema] = {}

    for field in fields:
        section_path = str(
            field.raw.get("section_key", "")
        )

        canonical_key = (
            f"{section_path}::{field.name}::"
            f"{field.raw.get('path', '')}"
        )

        unique.setdefault(canonical_key, field)

    return _finalize(
        form_name=form_name,
        source="api",
        fields=list(unique.values()),
        raw_schema=_clean(payload),
    )


def _field_from_api_node(
    node: dict[str, Any],
    path: str,
    section_key: str,
    section_title: str,
    repeatable: bool,
    section_rules: list[Any],
) -> FieldSchema | None:
    """
    Convert one HRMS API field definition into FieldSchema.

    The normalized model fields cover common deterministic properties.
    Rich HRMS-specific metadata is retained in raw until the AI-SDET model
    layer explicitly exposes those properties.
    """
    name = (
        node.get("name")
        or node.get("field_name")
        or node.get("key")
        or node.get("slug")
    )

    if not name:
        return None

    raw_type = (
        node.get("input_type")
        or node.get("field_type")
        or node.get("data_type")
        or node.get("type")
    )

    normalized_type = _infer_input_type(
        str(raw_type) if raw_type else None
    )

    validation = node.get("validation")

    pattern = _extract_pattern(
        validation=validation,
        fallback=node.get("pattern"),
    )

    options = _extract_options(
        node.get("options")
        or node.get("choices")
        or []
    )

    raw_metadata = {
        "path": path,
        "section_key": section_key,
        "section_title": section_title,
        "repeatable": repeatable,
        "section_rules": _clean(section_rules),

        # Exact API contract details
        "api_type": raw_type,
        "validation": _clean(validation),
        "constraints": _clean(node.get("constraints") or {}),
        "options_key": _clean(node.get("options_key")),
        "lookup_key": _clean(node.get("lookup_key")),
        "ui_config": _clean(node.get("ui_config") or {}),
        "cross_validations": _clean(
            node.get("cross_validations") or []
        ),
        "conditions": _clean(node.get("conditions") or []),
        "messages": _clean(node.get("messages") or {}),

        # Preserve the complete original field definition.
        "api_field": _clean(node),
    }

    return FieldSchema(
        name=str(name),
        field_id=(
            str(node.get("id"))
            if node.get("id") is not None
            else None
        ),
        label=(
            str(node.get("label"))
            if node.get("label") is not None
            else None
        ),
        input_type=normalized_type,  # type: ignore[arg-type]
        required=bool(
            node.get(
                "required",
                node.get("mandatory", False),
            )
        ),
        min_length=_as_int(
            node.get(
                "min_length",
                node.get("minlength"),
            )
        ),
        max_length=_as_int(
            node.get(
                "max_length",
                node.get("maxlength"),
            )
        ),
        minimum=_as_float(
            node.get(
                "minimum",
                node.get("min"),
            )
        ),
        maximum=_as_float(
            node.get(
                "maximum",
                node.get("max"),
            )
        ),
        pattern=pattern,
        options=options,
        placeholder=(
            str(node.get("placeholder"))
            if node.get("placeholder") is not None
            else None
        ),
        source="api",
        raw=raw_metadata,
    )


def _extract_pattern(
    validation: Any,
    fallback: Any = None,
) -> str | None:
    """
    Extract a regex from values such as:

        regex:/^\\d{10}$/

    We preserve the regex body without the API's 'regex:/' wrapper.
    """
    candidate = validation if validation is not None else fallback

    if candidate is None:
        return None

    if not isinstance(candidate, str):
        return str(candidate)

    value = candidate.strip()

    if value.startswith("regex:/"):
        value = value[len("regex:/"):]

        if value.endswith("/"):
            value = value[:-1]

        return value

    return value


def _extract_options(
    options_raw: Any,
) -> list[str]:
    """
    Extract inline options if the API provides them.

    The current schema primarily provides options_key rather than actual
    option values, so those keys are preserved separately in raw metadata.
    """
    options: list[str] = []

    if not isinstance(options_raw, list):
        return options

    for option in options_raw:
        if isinstance(option, dict):
            value = (
                option.get("label")
                or option.get("name")
                or option.get("value")
                or option.get("id")
            )

            if value is not None:
                options.append(str(value))

        elif option is not None:
            options.append(str(option))

    return options


def _finalize(
    form_name: str,
    source: str,
    fields: list[FieldSchema],
    raw_schema: dict[str, Any] | None = None,
) -> FormSchema:
    return FormSchema(
        form_name=form_name,
        source=source,  # type: ignore[arg-type]
        fetched_at=datetime.now(timezone.utc).isoformat(),
        fields=fields,
        schema_hash=_hash_fields(fields),
        raw_schema=raw_schema,
    )


def _is_number(
    value: str | None,
) -> bool:
    if value is None:
        return False

    try:
        float(value)
        return True

    except (TypeError, ValueError):
        return False


def _as_int(
    value: Any,
) -> int | None:
    if value is None:
        return None

    try:
        return int(value)

    except (TypeError, ValueError):
        return None


def _as_float(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def save_schema(
    schema: FormSchema,
    path: str = "ai_form_testing/form_schema.json",
) -> None:
    """
    Save both the normalized QA schema and the raw authoritative API schema.

    `raw` is intentionally INCLUDED here. Previously it was excluded, which
    meant options_key, cross_validations, conditions, section_rules and other
    critical metadata became unavailable to the next development phase.
    """
    output = {
        "form_name": schema.form_name,
        "source": schema.source,
        "fetched_at": schema.fetched_at,
        "schema_hash": schema.schema_hash,
        "fields": [
            field.model_dump()
            for field in schema.fields
        ],
        "raw_schema": schema.raw_schema,
    }

    target = Path(path)
    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )