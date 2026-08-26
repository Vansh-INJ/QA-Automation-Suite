"""Configuration for the additive AI-SDET layer."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AIConfig:
    gemini_api_key: str | None
    gemini_model: str
    base_url: str
    schema_endpoint: str
    request_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "AIConfig":
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.7-flash"),
            base_url=os.getenv(
                "BASE_URL",
                "https://injin.injtechnologies.com",
            ).rstrip("/"),
            schema_endpoint=os.getenv(
                "AI_FORM_SCHEMA_ENDPOINT",
                "/api/onboarding/meta/form-schema",
            ),
            request_timeout_seconds=int(
                os.getenv("AI_FORM_SCHEMA_TIMEOUT", "30")
            ),
        )
