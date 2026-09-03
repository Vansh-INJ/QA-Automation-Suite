# AI-SDET Layer — Phase 1

## Objective

Add an independent AI-SDET layer without modifying the existing onboarding,
add-employee, health, Playwright, or Pytest implementation.

Phase 1 does **schema discovery only**.

## Current architecture

Existing:

- Playwright
- Pytest
- CandidateFormFiller
- AddEmployeePage
- Dynamic form validator
- API framework / TokenManager
- API Health Suite

New:

text
ai_form_testing/
├── config.py
├── models.py
├── schema_discovery.py
├── gemini_client.py
├── cache.py
├── qa_rules.py
├── run_schema_discovery.py
└── case_cache/


Nothing existing is imported by the normal test suite unless this new package
is explicitly invoked.

## Setup

Add the contents of `requirements-ai.txt` to the existing requirements file:

text
google-genai
pydantic>=2


Put the Gemini key in `.env`:

text
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.7-flash


Do NOT commit `.env`.

## Phase 1 command

From the project root:

bash
python -m ai_form_testing.run_schema_discovery --api


Expected behavior:

1. Existing `TokenManager` obtains an HRMS bearer token.
2. GET `/api/onboarding/meta/form-schema`.
3. Save the raw response plus normalized field schema.
4. Calculate a deterministic schema hash.
5. Print discovered fields.
6. Make no UI changes.
7. Submit no employee/onboarding data.
8. Do not call Gemini.

## Why the first run does not call Gemini

We need to see the actual live schema response first.

The Postman collection confirms that `GET /api/onboarding/meta/form-schema`
exists and is bearer-authenticated, but the collection does not contain a
saved example response. Therefore the normalizer intentionally preserves the
raw payload and uses conservative best-effort discovery.

After the first real run, we should inspect `form_schema.json` and tighten
`normalize_api_schema()` to the actual backend contract.

## Phase 2

Once the schema is verified:

text
form_schema.json
      ↓
GeminiCaseGenerator
      ↓
structured GeneratedCaseSet
      ↓
CaseCache


The Gemini adapter already exists in this package, but it is not invoked by
Phase 1.

## Safety boundary

Gemini does not:

- click buttons
- submit forms
- create employees
- mutate HRMS data
- determine final PASS/FAIL
- replace Playwright
- replace existing POM/fillers

Later, Gemini will generate test intelligence. Existing deterministic
automation will execute and judge it.
