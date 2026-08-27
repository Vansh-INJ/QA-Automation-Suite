"""Phase 1: discover and normalize the live onboarding form schema.

Preferred source:
    GET /api/onboarding/meta/form-schema

Fallback:
    Playwright DOM introspection.

This module:
    - does not call Gemini
    - does not submit forms
    - does not create/update HRMS records
    - preserves the backend form contract
    - preserves section/rule/condition metadata
    - uses qualified_name as the canonical field identity

The normalized FormSchema is intended to become the single source of truth
for the future AI-SDET test-generation layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json

import requests
from playwright.sync_api import Page

from .config import AIConfig
from .models import FieldSchema, FormSchema


# ============================================================================
# Generic Helpers
# ============================================================================


def _clean(value: Any) -> Any:
    """Recursively make values safe for JSON serialization."""

    if isinstance(value, dict):
        return {
            str(key): _clean(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_clean(item) for item in value]

    return value


def _is_number(value: Any) -> bool:
    """Return True when value can safely be interpreted as a number."""

    if value is None:
        return False

    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _as_int(value: Any) -> int | None:
    """Safely convert a value to int."""

    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    """Safely convert a value to float."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================================
# Schema Hashing
# ============================================================================


def _hash_fields(fields: list[FieldSchema]) -> str:
    """
    Create a stable hash from the normalized QA contract.

    Raw transport metadata is excluded.

    The hash changes when any meaningful testing contract changes,
    including:

        field identity
        required status
        validation
        regex
        options key
        lookup
        repeatability
        conditions
        cross-validations
        section rules
        UI configuration
        messages
    """

    canonical = [
        field.model_dump(exclude={"raw"})
        for field in sorted(
            fields,
            key=lambda item: (
                item.qualified_name
                or item.name
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
# ============================================================================
# Input Type Normalization
# ============================================================================


def _infer_input_type(
    input_type: str | None,
    tag: str | None = None,
    role: str | None = None,
) -> str:
    """Normalize API/HTML field types into internal QA categories."""

    value = (input_type or "").strip().lower()
    normalized_tag = (tag or "").strip().lower()
    normalized_role = (role or "").strip().lower()

    mapping = {
        # Standard HTML
        "text": "text",
        "email": "email",
        "number": "number",
        "integer": "integer",
        "tel": "tel",
        "url": "url",
        "date": "date",
        "datetime": "datetime",
        "datetime-local": "datetime",
        "time": "time",
        "month": "month",
        "week": "week",
        "password": "password",

        # Boolean / choice
        "checkbox": "checkbox",
        "radio": "radio",

        # File
        "file": "file",
        "avatar": "file",
        "image": "file",
        "upload": "file",

        # HRMS/API
        "select": "dropdown",
        "dropdown": "dropdown",
        "combobox": "dropdown",

        "multi_select": "multi_select",
        "multiselect": "multi_select",

        "textarea": "textarea",
    }

    if value in mapping:
        return mapping[value]

    # DOM role fallbacks.
    if normalized_role == "combobox":
        return "dropdown"

    if normalized_role == "checkbox":
        return "checkbox"

    if normalized_role == "radio":
        return "radio"

    # DOM element fallbacks.
    if normalized_tag == "textarea":
        return "textarea"

    if normalized_tag == "select":
        return "dropdown"

    return "unknown"


# ============================================================================
# DOM Discovery
# ============================================================================


def discover_from_dom(
    page: Page,
    form_name: str = "onboarding_add_employee",
) -> FormSchema:
    """Inspect the currently rendered form without submitting it.

    DOM discovery is a fallback mechanism.

    API discovery remains authoritative because the backend schema contains
    validation/business-rule information that may not be exposed in HTML.
    """

    raw_fields = page.locator(
        "input:not([type='hidden']), textarea, select, "
        "[role='combobox'], [role='checkbox'], [role='radio']"
    )

    fields: list[FieldSchema] = []

    for index in range(raw_fields.count()):
        element = raw_fields.nth(index)

        try:
            tag = element.evaluate(
                "(el) => el.tagName.toLowerCase()"
            )

            field_id = element.get_attribute("id")
            name = element.get_attribute("name")
            role = element.get_attribute("role")
            html_type = element.get_attribute("type")
            placeholder = element.get_attribute("placeholder")

            required = bool(
                element.get_attribute("required") is not None
                or element.get_attribute("aria-required") == "true"
            )

            field_name = (
                name
                or field_id
                or f"unnamed_field_{index}"
            )

            # --------------------------------------------------------------
            # Options
            # --------------------------------------------------------------

            options: list[str] = []

            if tag == "select":
                options = element.locator(
                    "option"
                ).all_text_contents()

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

            # --------------------------------------------------------------
            # Validation attributes
            # --------------------------------------------------------------

            max_length = element.get_attribute("maxlength")
            min_length = element.get_attribute("minlength")
            minimum = element.get_attribute("min")
            maximum = element.get_attribute("max")
            pattern = element.get_attribute("pattern")

            # --------------------------------------------------------------
            # Label
            # --------------------------------------------------------------

            label = None

            if field_id:
                label_locator = page.locator(
                    f"label[for='{field_id}']"
                ).first

                if label_locator.count():
                    label = label_locator.inner_text().strip()

            # --------------------------------------------------------------
            # DOM qualified name
            # --------------------------------------------------------------

            qualified_name = (
                element.get_attribute("data-qualified-name")
                or element.get_attribute("data-field-path")
                or field_name
            )

            # --------------------------------------------------------------
            # Build FieldSchema
            # --------------------------------------------------------------

            fields.append(
                FieldSchema(
                    name=field_name,
                    qualified_name=qualified_name,
                    field_id=field_id,
                    label=label,

                    section_key=None,
                    section_title=None,
                    section_index=None,
                    field_index=index,
                    section_path=None,

                    input_type=_infer_input_type(
                        html_type,
                        tag,
                        role,
                    ),
                    required=required,
                    repeatable=False,

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
                    validation=pattern,

                    options=options,

                    options_key=None,
                    lookup_key=None,

                    placeholder=placeholder,

                    constraints={},
                    ui_config={},

                    cross_validations=[],
                    conditions=[],
                    section_rules=[],
                    messages={},

                    source="dom",

                    raw={
                        "dom_index": index,
                        "tag": tag,
                        "role": role,
                        "html_type": html_type,
                        "qualified_name": qualified_name,
                    },
                )
            )

        except Exception as exc:
            # Discovery should report a bad element but continue.
            fields.append(
                FieldSchema(
                    name=f"discovery_error_{index}",
                    qualified_name=f"discovery_error_{index}",
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


# ============================================================================
# API Fetch
# ============================================================================


def fetch_schema_api(
    config: AIConfig | None = None,
) -> dict[str, Any]:
    """Fetch the backend form schema using the existing TokenManager."""

    config = config or AIConfig.from_env()

    try:
        from api_framework.auth.token_manager import TokenManager

        headers = TokenManager.get_headers()

    except Exception as exc:
        raise RuntimeError(
            "Could not obtain HRMS API headers through the existing "
            "TokenManager. Use DOM discovery if API schema access is unavailable."
        ) from exc

    url = (
        f"{config.base_url.rstrip('/')}"
        f"/{config.schema_endpoint.lstrip('/')}"
    )

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


# ============================================================================
# API Schema Normalization
# ============================================================================


def normalize_api_schema(
    payload: dict[str, Any],
    form_name: str = "onboarding_add_employee",
) -> FormSchema:
    """Normalize the HRMS form-schema API contract.

    Expected shape:

        {
            "status": "success",
            "data": {
                "sections": [
                    {
                        "key": "...",
                        "title": "...",
                        "repeatable": false,
                        "section_rules": [],
                        "fields": [...]
                    }
                ]
            }
        }

    The important rule is:

        qualified_name = canonical identity

    NOT:

        name = canonical identity

    Therefore fields such as:

        addresses.current.line1
        addresses.permanent.line1

    remain separate fields.
    """

    data = payload.get("data")

    if not isinstance(data, dict):
        raise ValueError(
            "Unexpected form schema API response: "
            "missing object at 'data'."
        )

    sections = data.get("sections")

    if not isinstance(sections, list):
        raise ValueError(
            "Unexpected form schema API response: "
            "missing list at 'data.sections'."
        )

    fields: list[FieldSchema] = []

    for section_index, section in enumerate(sections):

        if not isinstance(section, dict):
            continue

        section_key = str(
            section.get("key")
            or section.get("name")
            or f"section_{section_index}"
        )

        section_title = (
            str(section.get("title"))
            if section.get("title") is not None
            else section_key
        )

        repeatable = bool(
            section.get("repeatable", False)
        )

        section_rules = section.get("section_rules")

        if not isinstance(section_rules, list):
            section_rules = []

        # --------------------------------------------------------------
        # Section path
        # --------------------------------------------------------------

        section_path = (
            section.get("path")
            or section.get("section_path")
            or section_key
        )

        section_path = str(section_path)

        # --------------------------------------------------------------
        # Section-level conditions
        # --------------------------------------------------------------

        section_conditions = section.get("conditions")

        if not isinstance(section_conditions, list):
            section_conditions = []

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
                section_index=section_index,
                field_index=field_index,
                repeatable=repeatable,
                section_rules=section_rules,
            )

            if field is not None:
                fields.append(field)

    if not fields:
        raise ValueError(
            "No fields were discovered from "
            "data.sections[].fields[]."
        )

    # ----------------------------------------------------------------------
    # IMPORTANT DEDUPLICATION RULE
    # ----------------------------------------------------------------------
    #
    # Never deduplicate using:
    #
    #     field.name
    #
    # or:
    #
    #     section_key + field.name + path
    #
    # when qualified_name exists.
    #
    # The API's qualified_name is the canonical field identity.
    # ----------------------------------------------------------------------

    unique: dict[str, FieldSchema] = {}

    for field in fields:
        identity = (
            field.qualified_name
            or field.name
        )

        unique.setdefault(
            identity,
            field,
        )

    normalized_fields = sorted(
        unique.values(),
        key=lambda field: (
            field.section_index
            if field.section_index is not None
            else 9999,

            field.field_index
            if field.field_index is not None
            else 9999,

            field.qualified_name
            or field.name,
        ),
    )

    return _finalize(
        form_name=form_name,
        source="api",
        fields=normalized_fields,
        raw_schema=_clean(payload),
    )


# ============================================================================
# API Field Normalization
# ============================================================================


def _field_from_api_node(
    node: dict[str, Any],
    path: str,
    section_key: str,
    section_title: str,
    section_index: int,
    field_index: int,
    repeatable: bool,
    section_rules: list[Any],
) -> FieldSchema | None:
    """
    Convert one HRMS API field definition into a rich FieldSchema.

    IMPORTANT:
    Do not throw away API metadata.

    The normalized schema is intended to become the single
    source of truth for deterministic QA and AI-generated tests.
    """

    name = (
        node.get("name")
        or node.get("field_name")
        or node.get("key")
        or node.get("slug")
    )

    if not name:
        return None

    name = str(name)

    # ---------------------------------------------------------
    # QUALIFIED FIELD NAME
    # ---------------------------------------------------------

    qualified_name = (
        node.get("qualified_name")
        or f"{section_key}.{name}"
    )

    qualified_name = str(qualified_name)

    # ---------------------------------------------------------
    # TYPE
    # ---------------------------------------------------------

    raw_type = (
        node.get("api_type")
        or node.get("input_type")
        or node.get("field_type")
        or node.get("data_type")
        or node.get("type")
    )

    normalized_type = _infer_input_type(
        str(raw_type)
        if raw_type is not None
        else None
    )

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    validation = node.get("validation")

    pattern = _extract_pattern(
        validation=validation,
        fallback=node.get("pattern"),
    )

    # ---------------------------------------------------------
    # OPTIONS
    # ---------------------------------------------------------

    options = _extract_options(
        node.get("options")
        or node.get("choices")
        or []
    )

    # ---------------------------------------------------------
    # MESSAGES
    # ---------------------------------------------------------

    messages = node.get("messages")

    if not isinstance(messages, dict):
        messages = {}

    # ---------------------------------------------------------
    # CONSTRAINTS
    # ---------------------------------------------------------

    constraints = node.get("constraints")

    if not isinstance(constraints, dict):
        constraints = {}

    # ---------------------------------------------------------
    # UI CONFIG
    # ---------------------------------------------------------

    ui_config = node.get("ui_config")

    if not isinstance(ui_config, dict):
        ui_config = {}

    # ---------------------------------------------------------
    # CROSS VALIDATIONS
    # ---------------------------------------------------------

    cross_validations = node.get(
        "cross_validations"
    )

    if not isinstance(cross_validations, list):
        cross_validations = []

    # ---------------------------------------------------------
    # CONDITIONS
    # ---------------------------------------------------------

    conditions = node.get("conditions")

    if not isinstance(conditions, list):
        conditions = []

    # ---------------------------------------------------------
    # SECTION RULES
    # ---------------------------------------------------------

    normalized_section_rules = [
        rule
        for rule in section_rules
        if isinstance(rule, dict)
    ]

    # ---------------------------------------------------------
    # RAW METADATA
    # ---------------------------------------------------------

    raw_metadata = {
        "path": path,

        "section_key": section_key,

        "section_title": section_title,

        "section_index": section_index,

        "field_index": field_index,

        "repeatable": repeatable,

        "api_type": raw_type,

        "validation": _clean(validation),

        "constraints": _clean(constraints),

        "options_key": _clean(
            node.get("options_key")
        ),

        "lookup_key": _clean(
            node.get("lookup_key")
        ),

        "ui_config": _clean(ui_config),

        "cross_validations": _clean(
            cross_validations
        ),

        "conditions": _clean(
            conditions
        ),

        "messages": _clean(
            messages
        ),

        # Complete original field definition.
        "api_field": _clean(node),
    }

    # ---------------------------------------------------------
    # FIELD
    # ---------------------------------------------------------

    return FieldSchema(
        name=name,

        qualified_name=qualified_name,

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

        section_key=section_key,

        section_title=section_title,

        section_index=section_index,

        field_index=field_index,

        section_path=section_key,

        input_type=normalized_type,  # type: ignore[arg-type]

        required=bool(
            node.get(
                "required",
                node.get(
                    "mandatory",
                    False,
                ),
            )
        ),

        repeatable=repeatable,

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

        validation=(
            str(validation)
            if validation is not None
            else None
        ),

        options=options,

        options_key=(
            str(node.get("options_key"))
            if node.get("options_key") is not None
            else None
        ),

        lookup_key=(
            str(node.get("lookup_key"))
            if node.get("lookup_key") is not None
            else None
        ),

        placeholder=(
            str(node.get("placeholder"))
            if node.get("placeholder") is not None
            else None
        ),

        constraints=constraints,

        ui_config=ui_config,

        cross_validations=cross_validations,

        conditions=conditions,

        section_rules=normalized_section_rules,

        messages=messages,

        source="api",

        raw=raw_metadata,
    )
# ============================================================================
# Validation Pattern Extraction
# ============================================================================


def _extract_pattern(
    validation: Any,
    fallback: Any = None,
) -> str | None:
    """Extract a regex/pattern from validation metadata.

    Examples:

        regex:/^\\d{10}$/

    becomes:

        ^\\d{10}$
    """

    candidate = (
        validation
        if validation is not None
        else fallback
    )

    if candidate is None:
        return None

    # Some APIs may provide structured validation metadata.
    if isinstance(candidate, dict):

        regex_value = (
            candidate.get("regex")
            or candidate.get("pattern")
            or candidate.get("value")
        )

        if regex_value is None:
            return None

        candidate = regex_value

    if not isinstance(candidate, str):
        return str(candidate)

    value = candidate.strip()

    if value.startswith("regex:/"):

        value = value[len("regex:/"):]

        if value.endswith("/"):
            value = value[:-1]

        return value

    return value


# ============================================================================
# Option Extraction
# ============================================================================


def _extract_options(
    options_raw: Any,
) -> list[str]:
    """Flatten API option definitions into display/value strings."""

    options: list[str] = []

    if isinstance(options_raw, dict):
        # Support APIs returning:
        #
        # {
        #     "male": "Male",
        #     "female": "Female"
        # }
        #
        for key, value in options_raw.items():

            if isinstance(value, dict):

                candidate = (
                    value.get("label")
                    or value.get("name")
                    or value.get("value")
                    or key
                )

            else:
                candidate = value

            if candidate is not None:
                options.append(str(candidate))

        return options

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


# ============================================================================
# Finalization
# ============================================================================


def _finalize(
    form_name: str,
    source: str,
    fields: list[FieldSchema],
    raw_schema: dict[str, Any] | None = None,
) -> FormSchema:
    """Build the final FormSchema object."""

    return FormSchema(
        form_name=form_name,

        source=source,  # type: ignore[arg-type]

        fetched_at=datetime.now(
            timezone.utc
        ).isoformat(),

        fields=fields,

        schema_hash=_hash_fields(fields),

        raw_schema=raw_schema,
    )


# ============================================================================
# Persistence
# ============================================================================


def save_schema(
    schema: FormSchema,
    path: str = "ai_form_testing/form_schema.json",
) -> None:
    """Persist normalized schema plus raw authoritative API schema."""

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

