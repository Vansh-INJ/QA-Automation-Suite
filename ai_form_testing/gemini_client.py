"""Thin Gemini adapter.

Gemini is an intelligence service only. It does not control Playwright,
does not decide the final deterministic PASS/FAIL result, and is never
required by the existing test suite.
"""

from __future__ import annotations

from google import genai
from google.genai import types

from .config import AIConfig
from .models import FieldSchema, GeneratedCaseSet


SYSTEM_INSTRUCTION = """
You are an expert QA/SDET test-design engine for an HRMS application.

Your job is to design meaningful field-level validation scenarios from
authoritative field metadata.

Rules:
1. Do not invent schema constraints.
2. Use the supplied field type, required flag, length/range/pattern/options.
3. Select only applicable categories.
4. Include useful boundary cases when a boundary is known.
5. For text fields consider whitespace, Unicode, special characters, and
   robustness where relevant.
6. For email/url/date/number fields, generate format-specific cases.
7. Do not generate destructive actions.
8. Generate values, not browser actions.
9. Never treat your own assumption as a schema fact.
10. Return only the requested structured JSON.
"""


class GeminiCaseGenerator:
    def __init__(self, config: AIConfig | None = None):
        self.config = config or AIConfig.from_env()

        if not self.config.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Set it in .env for local use or as a CI secret."
            )

        self.client = genai.Client(api_key=self.config.gemini_api_key)

    def generate_for_field(self, form_name: str, field: FieldSchema) -> GeneratedCaseSet:
        prompt = f"""
Generate a reviewed field-level QA test matrix for this HRMS field.

FORM:
{form_name}

FIELD:
{field.model_dump_json(indent=2)}

Applicable categories:
POSITIVE, NEGATIVE, BOUNDARY, FORMAT, EMPTY_NULL,
SPECIAL_UNICODE, SECURITY_ROBUSTNESS, BUSINESS_RULE.

Generate a compact but high-value set of cases. Do not create
cross-field cases here; those will be handled by a separate rule engine.
"""

        response = self.client.models.generate_content(
            model=self.config.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=GeneratedCaseSet.model_json_schema(),
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        result = GeneratedCaseSet.model_validate_json(response.text)

        # Safety check: the model cannot silently change the field/schema hash.
        if result.field_name != field.name:
            raise ValueError(
                f"Gemini returned field '{result.field_name}' "
                f"for requested field '{field.name}'."
            )

        return result
