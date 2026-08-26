"""Reviewed, versionable cache for generated AI cases."""

from __future__ import annotations

import json
from pathlib import Path

from .models import GeneratedCaseSet


class CaseCache:
    def __init__(self, root: str | Path = "ai_form_testing/case_cache"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, form_name: str, field_name: str) -> Path:
        safe_form = "".join(c if c.isalnum() or c in "-_" else "_" for c in form_name)
        safe_field = "".join(c if c.isalnum() or c in "-_" else "_" for c in field_name)
        return self.root / f"{safe_form}__{safe_field}.json"

    def load_if_matching(
        self,
        form_name: str,
        field_name: str,
        schema_hash: str,
    ) -> GeneratedCaseSet | None:
        path = self.path_for(form_name, field_name)

        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cached = GeneratedCaseSet.model_validate(data)
        except (OSError, ValueError, json.JSONDecodeError):
            return None

        if cached.schema_hash != schema_hash:
            return None

        return cached

    def save(self, cases: GeneratedCaseSet) -> Path:
        path = self.path_for(cases.form_name, cases.field_name)
        path.write_text(
            cases.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return path
