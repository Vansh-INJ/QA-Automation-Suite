"""
security_headers_checker.py

Checks HTTP response headers for common security misconfigurations
(OWASP A05:2021-Security Misconfiguration). This is the cheapest test
category to add: it can piggyback on responses you're ALREADY capturing
in the health check suite -- no new requests needed, just inspect
`resp.headers` on responses you already have.
"""

from dataclasses import dataclass, field


@dataclass
class HeaderCheckResult:
    endpoint: str
    result: str            # PASS / FAIL / WARN
    missing_headers: list = field(default_factory=list)
    misconfigured_headers: dict = field(default_factory=dict)
    owasp_category: str = "A05:2021-Security Misconfiguration"


# Headers that should be present. "expected" is a substring check when set;
# None means "just needs to exist".
REQUIRED_HEADERS = {
    "Strict-Transport-Security": "max-age=",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": None,          # DENY or SAMEORIGIN
    "Content-Security-Policy": None,
    "Referrer-Policy": None,
}

# Headers that should NOT leak implementation details
DISCOURAGED_HEADERS = ["X-Powered-By", "Server"]


def check_headers(endpoint: str, response_headers: dict) -> HeaderCheckResult:
    # Normalize header keys to handle case-insensitivity
    normalized = {k.lower(): v for k, v in response_headers.items()}

    missing = []
    misconfigured = {}

    for header, expected_substr in REQUIRED_HEADERS.items():
        key = header.lower()
        if key not in normalized:
            missing.append(header)
        elif expected_substr and expected_substr.lower() not in normalized[key].lower():
            misconfigured[header] = normalized[key]

    leaked_info = {
        h: normalized[h.lower()] for h in DISCOURAGED_HEADERS if h.lower() in normalized
    }
    if leaked_info:
        misconfigured.update(leaked_info)

    result = "PASS" if not missing and not misconfigured else "FAIL"

    return HeaderCheckResult(
        endpoint=endpoint,
        result=result,
        missing_headers=missing,
        misconfigured_headers=misconfigured,
    )