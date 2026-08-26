"""CLI for Phase 1 schema discovery.

Usage:
    python -m ai_form_testing.run_schema_discovery --api
    python -m ai_form_testing.run_schema_discovery --api --output ai_form_testing/form_schema.json

DOM mode is intentionally provided as a small helper for Phase 1 verification.
It requires an already authenticated Playwright page and is therefore normally
called from a pytest fixture rather than this CLI.
"""

from __future__ import annotations

import argparse
import json

from .config import AIConfig
from .schema_discovery import (
    fetch_schema_api,
    normalize_api_schema,
    save_schema,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover and normalize the HRMS dynamic onboarding form schema."
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Fetch /api/onboarding/meta/form-schema using the existing TokenManager.",
    )
    parser.add_argument(
        "--output",
        default="ai_form_testing/form_schema.json",
        help="Output JSON path.",
    )
    args = parser.parse_args()

    if not args.api:
        parser.error(
            "Phase 1 CLI currently requires --api. "
            "DOM discovery is exposed as a Python function because it needs "
            "the existing Playwright page/session."
        )

    config = AIConfig.from_env()
    payload = fetch_schema_api(config)
    schema = normalize_api_schema(payload)

    save_schema(schema, args.output)

    print("\n[AI-SDET] Schema discovery complete")
    print(f"[AI-SDET] Source       : {schema.source}")
    print(f"[AI-SDET] Form         : {schema.form_name}")
    print(f"[AI-SDET] Fields       : {len(schema.fields)}")
    print(f"[AI-SDET] Schema hash  : {schema.schema_hash}")
    print(f"[AI-SDET] Output       : {args.output}")

    for field in schema.fields:
        print(
            f"  - {field.name:<45} "
            f"type={field.input_type:<10} "
            f"required={field.required}"
        )

    if not schema.fields:
        print(
            "\n[AI-SDET][WARNING] No field-like objects were recognized.\n"
            "The raw API response has still been saved. We should inspect its "
            "actual structure and tighten the normalizer before Phase 2."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
