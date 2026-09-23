import os
import copy
import time
import uuid as uuid_module

from urllib.parse import parse_qs, urlparse

import pytest

from api_framework.clients.auth_client import AuthClient
from api_framework.clients.offer_client import OfferClient
from api_framework.clients.onboarding_client import OnboardingClient

from api_framework.config.settings import Settings

from api_framework.payloads.offer_payloads import OfferPayloads
from api_framework.payloads.onboarding_payloads import OnboardingPayloads

from api_framework.utils.master_data import MasterData


# ============================================================================
# SQL INJECTION SECURITY FRAMEWORK IMPORTS
# ============================================================================

from api_framework.security.core.sqli_payloads import (
    CLASSIC_SQLI_PAYLOADS,
    COMMENT_STYLE_SQLI_PAYLOADS,
    UNION_SQLI_PAYLOADS,
    TIME_BASED_SQLI_PAYLOADS,
    BOOLEAN_BLIND_PAIRS,
    TIME_BASED_THRESHOLD_SECONDS,
    ERROR_BASED_SQLI_PAYLOADS,
    ENCODING_OBFUSCATION_PAYLOADS,
    LOGIN_BYPASS_CREDENTIALS,
)

from api_framework.security.core.sqli_fields import (
    INJECTABLE_FIELDS,
)

from api_framework.security.core.sqli_analyzer import (
    build_response_signature,
)

from api_framework.security.core.sqli_reporter import (
    log_sqli_evidence,
)

from api_framework.security.core.sqli_assertions import (
    assert_sqli_safe,
)

from api_framework.security.core.sqli_engine import (
    find_sql_error_signatures,
    find_sensitive_leaks,
    find_version_string_leaks,
)


# ============================================================================
# TEST DOCUMENT CONFIGURATION
# ============================================================================

TEST_DOCUMENT_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "test_data",
        "test_document.pdf",
    )
)


REQUIRED_DOCUMENT_TYPES = [
    "aadhar",
    "cancelled_cheque",
    "experience_certificate",
    "pan",
    "relieving_certificate",
    "resume",
    "x_marksheet",
    "xii_marksheet",
]


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def module_offer_client():
    """
    Function-scoped OfferClient used for creating real offers.
    Fetches fresh headers per test to avoid token expiration.
    """

    from api_framework.auth.token_manager import TokenManager

    return OfferClient(
        base_url=Settings.BASE_URL,
        headers=TokenManager.get_headers(),
    )


@pytest.fixture
def module_onboarding_client():
    """
    Function-scoped OnboardingClient.
    """

    return OnboardingClient(
        base_url=Settings.BASE_URL,
    )


# ============================================================================
# FRESH ONBOARDING CONTEXT
# ============================================================================

@pytest.fixture
def fresh_onboarding_context(
    module_offer_client,
    module_onboarding_client,
):
    """
    Create a completely fresh onboarding context for ONE SQL injection test.

    Flow:
        1. Create fresh offer
        2. Accept offer
        3. Upload required documents
        4. Build clean onboarding payload

    IMPORTANT:
        The onboarding payload is NOT submitted here.

    Every SQL injection test receives its own fresh onboarding request.
    """

    # ------------------------------------------------------------------------
    # STEP 1: CREATE FRESH OFFER
    # ------------------------------------------------------------------------

    master = MasterData(module_offer_client)

    offer_payload = _build_live_offer_payload(
        master
    )

    send_response = module_offer_client.send_offer(
        offer_payload
    )

    assert send_response.status_code in (200, 201), (
        "Failed to create fresh offer.\n"
        f"Status: {send_response.status_code}\n"
        f"Response: {send_response.text}"
    )

    try:
        response_json = send_response.json()
    except ValueError as exc:
        raise AssertionError(
            "Fresh offer creation returned non-JSON response.\n"
            f"Response: {send_response.text}"
        ) from exc

    invite_link = (
        response_json
        .get("data", {})
        .get("invite_link")
    )

    assert invite_link, (
        "Offer created but invite_link missing.\n"
        f"Response: {send_response.text}"
    )

    offer_uuid, token = _parse_invite_link(
        invite_link
    )

    print(
        "\n"
        "========================================\n"
        "FRESH SQLI TEST CONTEXT CREATED\n"
        "========================================\n"
        f"Offer UUID: {offer_uuid}\n"
    )

    # ------------------------------------------------------------------------
    # STEP 2: ACCEPT OFFER
    # ------------------------------------------------------------------------

    accept_response = (
        module_onboarding_client.accept_offer(
            offer_uuid,
            token,
        )
    )

    assert accept_response.status_code in (200, 201), (
        "Failed to accept fresh offer.\n"
        f"Status: {accept_response.status_code}\n"
        f"Response: {accept_response.text}"
    )

    # ------------------------------------------------------------------------
    # STEP 3: UPLOAD REQUIRED DOCUMENTS
    # ------------------------------------------------------------------------

    assert os.path.exists(TEST_DOCUMENT_PATH), (
        "Test document not found.\n"
        f"Expected path: {TEST_DOCUMENT_PATH}"
    )

    uploaded_documents = {}

    print(
        "\n"
        "[FRESH CONTEXT] Uploading required documents..."
    )

    for document_type in REQUIRED_DOCUMENT_TYPES:

        response = (
            module_onboarding_client.upload_document(
                offer_uuid=offer_uuid,
                token=token,
                file_path=TEST_DOCUMENT_PATH,
                document_type=document_type,
            )
        )

        assert response.status_code in (200, 201), (
            f"Document upload failed: {document_type}\n"
            f"Status: {response.status_code}\n"
            f"Response: {response.text}"
        )

        try:
            response_json = response.json()
        except ValueError as exc:
            raise AssertionError(
                f"Document upload returned non-JSON response "
                f"for {document_type}.\n"
                f"Response: {response.text}"
            ) from exc

        document_uuid = (
            response_json
            .get("data", {})
            .get("uuid")
        )

        assert document_uuid, (
            f"Document UUID missing for: {document_type}\n"
            f"Response: {response.text}"
        )

        uploaded_documents[
            document_type
        ] = document_uuid

    print(
        "[FRESH CONTEXT] All documents uploaded successfully."
    )

    # ------------------------------------------------------------------------
    # STEP 4: BUILD CLEAN PAYLOAD
    # ------------------------------------------------------------------------

    onboarding_payload = copy.deepcopy(
        OnboardingPayloads.valid()
    )

    onboarding_payload["documents"] = copy.deepcopy(
        uploaded_documents
    )

    # ------------------------------------------------------------------------
    # RETURN FRESH CONTEXT
    # ------------------------------------------------------------------------

    return {
        "offer_uuid": offer_uuid,
        "token": token,
        "payload": onboarding_payload,
    }


# ============================================================================
# LEGACY FIXTURES
# These are temporarily retained for the other SQLi categories.
# They will be migrated to fresh_onboarding_context one by one.
# ============================================================================

@pytest.fixture(scope="module")
def accepted_offer_context(
    module_offer_client,
    module_onboarding_client,
):
    """
    Create a real offer, extract offer UUID/token and accept it.
    """

    master = MasterData(module_offer_client)

    offer_payload = _build_live_offer_payload(
        master
    )

    send_response = module_offer_client.send_offer(
        offer_payload
    )

    assert send_response.status_code in (200, 201), (
        "Failed to create offer for test setup: "
        f"status={send_response.status_code}, "
        f"body={send_response.text}"
    )

    try:
        response_json = send_response.json()
    except ValueError as exc:
        raise AssertionError(
            "Offer creation returned a non-JSON response: "
            f"{send_response.text!r}"
        ) from exc

    invite_link = (
        response_json
        .get("data", {})
        .get("invite_link")
    )

    assert invite_link, (
        "Offer creation succeeded but response did not "
        "contain data.invite_link.\n"
        f"Response: {send_response.text}"
    )

    offer_uuid, token = _parse_invite_link(
        invite_link
    )

    accept_response = (
        module_onboarding_client.accept_offer(
            offer_uuid,
            token,
        )
    )

    assert accept_response.status_code in (200, 201), (
        "Failed to accept offer for test setup: "
        f"status={accept_response.status_code}, "
        f"body={accept_response.text}"
    )

    print(
        "\n"
        "========================================\n"
        "OFFER CREATED AND ACCEPTED\n"
        "========================================\n"
        f"Offer UUID: {offer_uuid}\n"
    )

    return offer_uuid, token


# ============================================================================
# DOCUMENT UPLOAD FIXTURE
# ============================================================================

@pytest.fixture(scope="module")
def uploaded_documents(
    module_onboarding_client,
    accepted_offer_context,
):
    """
    Upload all mandatory onboarding documents once.

    Used temporarily by legacy SQLi tests.
    """

    offer_uuid, token = accepted_offer_context

    assert os.path.exists(TEST_DOCUMENT_PATH), (
        "Test document not found.\n"
        f"Expected path: {TEST_DOCUMENT_PATH}"
    )

    print(
        "\n"
        "========================================\n"
        "UPLOADING REQUIRED ONBOARDING DOCUMENTS\n"
        "========================================"
    )

    uploaded = {}

    for document_type in REQUIRED_DOCUMENT_TYPES:

        print(
            f"\n[DOCUMENT UPLOAD] Uploading: {document_type}"
        )

        response = (
            module_onboarding_client.upload_document(
                offer_uuid=offer_uuid,
                token=token,
                file_path=TEST_DOCUMENT_PATH,
                document_type=document_type,
            )
        )

        print(
            f"[DOCUMENT UPLOAD] "
            f"Type={document_type} | "
            f"Status={response.status_code}"
        )

        assert response.status_code in (200, 201), (
            f"Failed to upload required document: "
            f"{document_type}\n"
            f"Status: {response.status_code}\n"
            f"Response: {response.text}"
        )

        response_json = response.json()

        document_uuid = (
            response_json
            .get("data", {})
            .get("uuid")
        )

        assert document_uuid, (
            f"Document upload succeeded but UUID missing "
            f"for {document_type}.\n"
            f"Response: {response.text}"
        )

        uploaded[document_type] = document_uuid

    print(
        "\n"
        "[LEGACY CONTEXT] All required documents uploaded."
    )

    return uploaded


# ============================================================================
# VALIDATED BASELINE ONBOARDING PAYLOAD
# ============================================================================

@pytest.fixture(scope="module")
def validated_onboarding_payload(
    module_onboarding_client,
    accepted_offer_context,
    uploaded_documents,
):
    """
    LEGACY fixture.

    Retained temporarily for categories not yet migrated.
    """

    offer_uuid, token = accepted_offer_context

    baseline_payload = copy.deepcopy(
        OnboardingPayloads.valid()
    )

    baseline_payload["documents"] = copy.deepcopy(
        uploaded_documents
    )

    print(
        "\n"
        "========================================\n"
        "VALIDATING SQLI BASELINE PAYLOAD\n"
        "========================================"
    )

    baseline_response = (
        module_onboarding_client.submit_onboarding(
            offer_uuid,
            token,
            copy.deepcopy(baseline_payload),
        )
    )

    _assert_baseline_payload_is_valid(
        baseline_response
    )

    print(
        "\n"
        "[BASELINE PAYLOAD VALIDATED]\n"
        f"Status: {baseline_response.status_code}\n"
        f"Response: {baseline_response.text[:1000]}\n"
    )

    return baseline_payload


# ============================================================================
# LIVE OFFER PAYLOAD
# ============================================================================

def _build_live_offer_payload(
    master: MasterData,
) -> dict:
    """
    Build offer payload using fresh active master-data IDs.

    A UUID suffix is appended to the email to guarantee
    uniqueness across every call, preventing 409 conflicts
    when many tests run in the same session.
    """

    payload = copy.deepcopy(
        OfferPayloads.valid()
    )

    # Force a globally-unique email to avoid 409 conflicts.
    unique_suffix = uuid_module.uuid4().hex[:8]
    base_email = payload.get("email", "sqli@injpartners.com")
    local, _, domain = base_email.partition("@")
    payload["email"] = f"{local}_{unique_suffix}@{domain}"

    function = master.get_function(
        "Pre Sales"
    )

    sub_function = master.get_sub_function(
        function["uuid"],
        "Client Solutions",
    )

    job_titles = master.get_job_titles()

    legal_entities = (
        master.get_legal_entities()
    )

    work_locations = (
        master.get_work_locations()
    )

    if not job_titles:
        raise AssertionError(
            "No active job titles returned."
        )

    if not legal_entities:
        raise AssertionError(
            "No active legal entities returned."
        )

    if not work_locations:
        raise AssertionError(
            "No active work locations returned."
        )

    job_title = job_titles[0]
    legal_entity = legal_entities[0]
    work_location = work_locations[0]

    hierarchy_level = (
        master.get_hierarchy_level(
            "Manager"
        )
    )

    salary_structure = (
        master.get_salary_structure(
            "SAL_NOIDA",
            legal_entity_uuid=legal_entity["uuid"],
            work_location_uuid=work_location["uuid"],
        )
    )

    reporting_manager = (
        master.get_reporting_manager(
            "Amit Kumar Sharma"
        )
    )

    payload.update(
        {
            "function_id": function["uuid"],
            "sub_function_id": sub_function["uuid"],
            "job_title_id": job_title["uuid"],
            "legal_entity_id": legal_entity["uuid"],
            "work_location_id": work_location["uuid"],
            "reporting_manager_uuid": (
                reporting_manager["uuid"]
            ),
            "hierarchy_level_uuid": (
                hierarchy_level["uuid"]
            ),
            "salary_structure_uuid": (
                salary_structure["uuid"]
            ),
        }
    )

    return payload


# ============================================================================
# INVITE LINK PARSING
# ============================================================================

def _parse_invite_link(
    invite_link: str,
):
    """
    Extract (offer_uuid, token) from invite link.
    """

    if not invite_link:
        raise AssertionError(
            "invite_link is empty or missing."
        )

    parsed = urlparse(invite_link)

    path_parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    if not path_parts:
        raise AssertionError(
            "Could not parse offer_uuid from invite link: "
            f"{invite_link!r}"
        )

    offer_uuid = path_parts[-1]

    query = parse_qs(
        parsed.query
    )

    token_values = query.get(
        "token",
        [],
    )

    if not token_values or not token_values[0]:
        raise AssertionError(
            "Could not parse token from invite link: "
            f"{invite_link!r}"
        )

    token = token_values[0]

    return offer_uuid, token


# ============================================================================
# PREREQUISITE DIAGNOSTIC
# ============================================================================

@pytest.mark.negative
def test_offer_creation_prerequisite(
    authenticated_offer_client,
):
    """
    Diagnostic test for offer creation.
    """

    master = MasterData(
        authenticated_offer_client
    )

    offer_payload = _build_live_offer_payload(
        master
    )

    print(
        f"[PREREQ] Sending offer payload: "
        f"{offer_payload}"
    )

    response = (
        authenticated_offer_client.send_offer(
            offer_payload
        )
    )

    print(
        f"[PREREQ] status={response.status_code} "
        f"body={response.text}"
    )

    assert response.status_code in (200, 201), (
        "Offer creation failed with status "
        f"{response.status_code}: {response.text}"
    )


# ============================================================================
# FRESH CONTEXT DIAGNOSTIC
# ============================================================================

@pytest.mark.negative
def test_fresh_onboarding_context_debug(
    fresh_onboarding_context,
):
    """
    Diagnostic test to verify fresh context creation.
    """

    offer_uuid = fresh_onboarding_context[
        "offer_uuid"
    ]

    token = fresh_onboarding_context[
        "token"
    ]

    payload = fresh_onboarding_context[
        "payload"
    ]

    print(
        "\n"
        "========================================\n"
        "FRESH CONTEXT DEBUG\n"
        "========================================\n"
        f"Offer UUID: {offer_uuid}\n"
        f"Token Available: {bool(token)}\n"
        f"Document Count: "
        f"{len(payload.get('documents', {}))}\n"
    )

    assert offer_uuid
    assert token

    assert len(
        payload.get("documents", {})
    ) == len(REQUIRED_DOCUMENT_TYPES)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _build_payload(
    field_name: str,
    malicious_value,
    baseline_payload: dict,
) -> dict:
    """
    Create deep copy and inject malicious value.
    """

    payload = copy.deepcopy(
        baseline_payload
    )

    setter = INJECTABLE_FIELDS.get(
        field_name
    )

    if setter is None:
        raise AssertionError(
            f"No injectable field setter registered for: "
            f"{field_name}"
        )

    setter(
        payload,
        malicious_value,
    )

    return payload


def _log_evidence(
    category: str,
    field_name: str,
    payload,
    response,
    elapsed=None,
):
    """
    Wrapper around centralized SQLi reporter.
    """

    return log_sqli_evidence(
        category,
        field_name,
        payload,
        response,
        elapsed,
    )


def _assert_safe_response(
    response,
    payload,
    field_name: str,
):
    """
    Wrapper around centralized SQLi assertions.
    """

    return assert_sqli_safe(
        response,
        payload,
        field_name,
    )


def _response_signature(
    response,
) -> dict:
    """
    Build response signature.
    """

    return build_response_signature(
        response
    )


def _extract_error_message(
    response,
) -> str:

    response_text = getattr(
        response,
        "text",
        "",
    ) or ""

    try:
        response_json = response.json()

        if isinstance(
            response_json,
            dict,
        ):
            message = response_json.get(
                "message"
            )

            if message:
                return str(message)

            errors = response_json.get(
                "errors"
            )

            if errors:
                return str(errors)

    except (
        ValueError,
        TypeError,
        AttributeError,
    ):
        pass

    return response_text[:2000]


def _assert_baseline_payload_is_valid(
    response,
):
    """
    Verify clean baseline does not cause server error.
    """

    status = getattr(
        response,
        "status_code",
        None,
    )

    response_text = getattr(
        response,
        "text",
        "",
    ) or ""

    error_message = _extract_error_message(
        response
    )

    print(
        "\n[BASELINE PAYLOAD CHECK]\n"
        f"Status   : {status}\n"
        f"Response : {response_text[:2000]!r}\n"
    )

    assert status is not None, (
        "Baseline onboarding prerequisite did not "
        "receive an HTTP response."
    )

    assert status < 500, (
        "\n\n"
        "========================================\n"
        "SQL INJECTION TEST SETUP FAILURE\n"
        "========================================\n"
        "The clean baseline onboarding payload itself "
        "caused a server-side error.\n\n"
        f"HTTP Status : {status}\n"
        f"API Message : {error_message}\n\n"
        "SQL injection testing has NOT started yet.\n"
        "========================================"
    )

    assert "missing required document" not in (
        response_text.lower()
    ), (
        "DOCUMENT PREREQUISITE FAILURE\n"
        f"Response: {response_text}"
    )


# ============================================================================
# CLASSIC SQL INJECTION TESTS
# ============================================================================

@pytest.mark.negative
@pytest.mark.parametrize(
    "field_name",
    list(INJECTABLE_FIELDS.keys()),
)
@pytest.mark.parametrize(
    "payload",
    CLASSIC_SQLI_PAYLOADS,
)
def test_sql_injection_classic_payloads(
    module_onboarding_client,
    fresh_onboarding_context,
    field_name,
    payload,
):
    """
    Test classic SQL injection payloads.

    Every parametrized test gets a completely fresh onboarding
    request and submits exactly once.
    """

    offer_uuid = fresh_onboarding_context[
        "offer_uuid"
    ]

    token = fresh_onboarding_context[
        "token"
    ]

    baseline_payload = fresh_onboarding_context[
        "payload"
    ]

    print(
        "\n"
        "========================================\n"
        "SQLI CLASSIC PAYLOAD TEST\n"
        "========================================\n"
        f"Offer UUID : {offer_uuid}\n"
        f"Field      : {field_name}\n"
        f"Payload    : {payload!r}\n"
    )

    onboarding_payload = _build_payload(
        field_name,
        payload,
        baseline_payload,
    )

    response = (
        module_onboarding_client.submit_onboarding(
            offer_uuid,
            token,
            onboarding_payload,
        )
    )

    _log_evidence(
        "classic_payloads",
        field_name,
        payload,
        response,
    )

    print(
        "\n"
        "[SQLI RESPONSE]\n"
        f"Status   : {response.status_code}\n"
        f"Response : {response.text[:2000]}\n"
    )

    _assert_safe_response(
        response,
        payload,
        field_name,
    )


# ============================================================================
# COMMENT STYLE SQL INJECTION TESTS
# ============================================================================

@pytest.mark.negative
@pytest.mark.parametrize(
    "field_name",
    list(INJECTABLE_FIELDS.keys()),
)
@pytest.mark.parametrize(
    "payload",
    COMMENT_STYLE_SQLI_PAYLOADS,
)
def test_sql_injection_comment_style_payloads(
    module_onboarding_client,
    fresh_onboarding_context,
    field_name,
    payload,
):
    """
    Test comment-style SQL injection payloads.
    Uses a fresh onboarding context per test to avoid resubmission errors.
    """

    offer_uuid = fresh_onboarding_context["offer_uuid"]
    token = fresh_onboarding_context["token"]
    baseline_payload = fresh_onboarding_context["payload"]

    onboarding_payload = _build_payload(
        field_name,
        payload,
        baseline_payload,
    )

    response = (
        module_onboarding_client.submit_onboarding(
            offer_uuid,
            token,
            onboarding_payload,
        )
    )

    _log_evidence(
        "comment_style_payloads",
        field_name,
        payload,
        response,
    )

    _assert_safe_response(
        response,
        payload,
        field_name,
    )


# ============================================================================
# UNION BASED SQL INJECTION TESTS
# ============================================================================

@pytest.mark.negative
@pytest.mark.parametrize(
    "field_name",
    list(INJECTABLE_FIELDS.keys()),
)
@pytest.mark.parametrize(
    "payload",
    UNION_SQLI_PAYLOADS,
)
def test_sql_injection_union_based(
    module_onboarding_client,
    fresh_onboarding_context,
    field_name,
    payload,
):
    """
    Test UNION-based SQL injection payloads.

    Also performs a deep scan of the response for sensitive data
    patterns and DB version strings that would indicate successful
    data extraction.
    """

    offer_uuid = fresh_onboarding_context["offer_uuid"]
    token = fresh_onboarding_context["token"]
    baseline_payload = fresh_onboarding_context["payload"]

    onboarding_payload = _build_payload(
        field_name,
        payload,
        baseline_payload,
    )

    response = (
        module_onboarding_client.submit_onboarding(
            offer_uuid,
            token,
            onboarding_payload,
        )
    )

    _log_evidence(
        "union_based",
        field_name,
        payload,
        response,
    )

    _assert_safe_response(
        response,
        payload,
        field_name,
    )

    body_text = (
        getattr(
            response,
            "text",
            "",
        ) or ""
    )

    # Deep scan: sensitive field names
    sensitive_hits = find_sensitive_leaks(body_text)
    assert not sensitive_hits, (
        f"Sensitive data pattern(s) detected in response after "
        f"UNION-based payload {payload!r} on field '{field_name}': "
        f"{sensitive_hits}"
    )

    # Deep scan: DB version strings
    version_hits = find_version_string_leaks(body_text)
    assert not version_hits, (
        f"DB version string(s) leaked in response after "
        f"UNION-based payload {payload!r} on field '{field_name}': "
        f"{version_hits}"
    )


# ============================================================================
# TIME BASED BLIND SQL INJECTION TESTS
# ============================================================================

@pytest.mark.negative
@pytest.mark.parametrize(
    "field_name",
    list(INJECTABLE_FIELDS.keys()),
)
@pytest.mark.parametrize(
    "payload",
    TIME_BASED_SQLI_PAYLOADS,
)
def test_sql_injection_time_based_blind(
    module_onboarding_client,
    fresh_onboarding_context,
    field_name,
    payload,
):
    """
    Test time-based blind SQL injection payloads across ALL injectable fields.

    If response time exceeds TIME_BASED_THRESHOLD_SECONDS, the payload
    may have triggered a real delay in the backend database — possible
    blind SQL injection vulnerability.
    """

    offer_uuid = fresh_onboarding_context["offer_uuid"]
    token = fresh_onboarding_context["token"]
    baseline_payload = fresh_onboarding_context["payload"]

    onboarding_payload = _build_payload(
        field_name,
        payload,
        baseline_payload,
    )

    start = time.monotonic()

    response = (
        module_onboarding_client.submit_onboarding(
            offer_uuid,
            token,
            onboarding_payload,
        )
    )

    elapsed = time.monotonic() - start

    _log_evidence(
        "time_based_blind",
        field_name,
        payload,
        response,
        elapsed,
    )

    assert elapsed < TIME_BASED_THRESHOLD_SECONDS, (
        f"Response took {elapsed:.2f}s "
        f"(threshold {TIME_BASED_THRESHOLD_SECONDS}s) "
        f"for time-based payload {payload!r} on field '{field_name}' — "
        "possible blind SQL injection vulnerability."
    )

    _assert_safe_response(
        response,
        payload,
        field_name,
    )


# ============================================================================
# BOOLEAN BASED BLIND SQL INJECTION TESTS
# ============================================================================

@pytest.mark.negative
@pytest.mark.parametrize(
    "field_name",
    list(INJECTABLE_FIELDS.keys()),
)
@pytest.mark.parametrize(
    "true_payload,false_payload",
    BOOLEAN_BLIND_PAIRS,
)
def test_sql_injection_boolean_blind_possibility(
    module_onboarding_client,
    fresh_onboarding_context,
    field_name,
    true_payload,
    false_payload,
):
    """
    Test boolean-based blind SQL injection by comparing TRUE vs FALSE responses.

    Checks for:
        - SQL error differences between TRUE and FALSE responses
        - Differing response lengths that may indicate data-dependent output
    """

    offer_uuid = fresh_onboarding_context["offer_uuid"]
    token = fresh_onboarding_context["token"]
    baseline_payload = fresh_onboarding_context["payload"]

    true_payload_body = _build_payload(
        field_name,
        true_payload,
        baseline_payload,
    )

    false_payload_body = _build_payload(
        field_name,
        false_payload,
        baseline_payload,
    )

    true_response = (
        module_onboarding_client.submit_onboarding(
            offer_uuid,
            token,
            true_payload_body,
        )
    )

    false_response = (
        module_onboarding_client.submit_onboarding(
            offer_uuid,
            token,
            false_payload_body,
        )
    )

    _log_evidence(
        "boolean_blind_TRUE",
        field_name,
        true_payload,
        true_response,
    )

    _log_evidence(
        "boolean_blind_FALSE",
        field_name,
        false_payload,
        false_response,
    )

    _assert_safe_response(
        true_response,
        true_payload,
        field_name,
    )

    _assert_safe_response(
        false_response,
        false_payload,
        field_name,
    )

    true_signature = _response_signature(
        true_response
    )

    false_signature = _response_signature(
        false_response
    )

    sql_error_diff = (
        true_signature["sql_error_signatures"]
        != false_signature["sql_error_signatures"]
    )

    print(
        "\n[EVIDENCE] Boolean Blind Comparison\n"
        f"Field                 : {field_name}\n"
        f"TRUE Payload          : {true_payload!r}\n"
        f"FALSE Payload         : {false_payload!r}\n"
        f"TRUE Status           : {true_signature['status']}\n"
        f"FALSE Status          : {false_signature['status']}\n"
        f"TRUE SQL Errors       : "
        f"{true_signature['sql_error_signatures']}\n"
        f"FALSE SQL Errors      : "
        f"{false_signature['sql_error_signatures']}\n"
        f"Response Lengths      : "
        f"{true_signature['response_length']} vs "
        f"{false_signature['response_length']}\n"
    )

    assert not sql_error_diff, (
        f"Possible SQL injection behavior difference detected "
        f"on field '{field_name}'."
    )


# ============================================================================
# LOGIN SQL INJECTION BYPASS
# ============================================================================

@pytest.mark.negative
@pytest.mark.parametrize(
    "credentials",
    LOGIN_BYPASS_CREDENTIALS,
)
def test_sql_injection_login_bypass_attempt(
    credentials,
):
    """
    Test SQL injection authentication bypass attempts.

    Covers comment truncation, tautology, HAVING, stacked queries,
    double-quote variants, and null byte bypasses.
    """

    auth_client = AuthClient(
        base_url=Settings.BASE_URL,
    )

    response = auth_client.login(
        credentials["username"],
        credentials["password"],
    )

    _log_evidence(
        "login_bypass_attempt",
        "username/password",
        credentials,
        response,
    )

    status = getattr(
        response,
        "status_code",
        None,
    )

    response_text = getattr(
        response,
        "text",
        "",
    ) or ""

    leaked = find_sql_error_signatures(
        response_text
    )

    print(
        "\n[DEBUG] Login SQLi Response\n"
        f"Credentials : {credentials!r}\n"
        f"Status      : {status}\n"
        f"Response    : {response_text[:2000]!r}\n"
        f"SQL Errors  : "
        f"{leaked if leaked else 'none'}\n"
    )

    assert status is not None, (
        "Login SQL injection test did not receive "
        "an HTTP status code."
    )

    assert status not in (200, 201), (
        "Auth bypass may have succeeded with credentials "
        f"{credentials!r} "
        f"(status {status})."
    )

    assert not leaked, (
        "SQL/database error signature leaked during "
        "login SQL injection attempt. "
        f"Credentials={credentials!r}, "
        f"leaks={leaked}"
    )

    response_json = {}

    try:
        response_json = response.json()
    except ValueError:
        pass

    response_data = (
        response_json
        if isinstance(response_json, dict)
        else {}
    )

    possible_token_keys = (
        "token",
        "access_token",
        "refresh_token",
        "jwt",
    )

    returned_tokens = []

    def _find_tokens(data):

        if isinstance(data, dict):

            for key, value in data.items():

                if (
                    key.lower() in possible_token_keys
                    and value
                ):
                    returned_tokens.append(
                        key
                    )

                if isinstance(
                    value,
                    (dict, list),
                ):
                    _find_tokens(value)

        elif isinstance(data, list):

            for item in data:
                _find_tokens(item)

    _find_tokens(
        response_data
    )

    assert not returned_tokens, (
        "Authentication token data was returned during "
        "SQL injection login-bypass attempt. "
        f"Credentials={credentials!r}, "
        f"token_fields={returned_tokens}"
    )


# ============================================================================
# ERROR BASED SQL INJECTION TESTS
# ============================================================================

@pytest.mark.negative
@pytest.mark.parametrize(
    "field_name",
    list(INJECTABLE_FIELDS.keys()),
)
@pytest.mark.parametrize(
    "payload",
    ERROR_BASED_SQLI_PAYLOADS,
)
def test_sql_injection_error_based(
    module_onboarding_client,
    fresh_onboarding_context,
    field_name,
    payload,
):
    """
    Test error-based SQL injection payloads.

    These payloads attempt to force the database to return version
    information or table names inside error messages.

    Checks:
        - No SQL error signatures in the response
        - No DB version strings in the response
        - No sensitive schema names in the response
    """

    offer_uuid = fresh_onboarding_context["offer_uuid"]
    token = fresh_onboarding_context["token"]
    baseline_payload = fresh_onboarding_context["payload"]

    onboarding_payload = _build_payload(
        field_name,
        payload,
        baseline_payload,
    )

    response = (
        module_onboarding_client.submit_onboarding(
            offer_uuid,
            token,
            onboarding_payload,
        )
    )

    _log_evidence(
        "error_based",
        field_name,
        payload,
        response,
    )

    _assert_safe_response(
        response,
        payload,
        field_name,
    )

    body_text = getattr(response, "text", "") or ""

    version_hits = find_version_string_leaks(body_text)
    assert not version_hits, (
        f"DB version string leaked via error-based payload "
        f"{payload!r} on field '{field_name}': {version_hits}"
    )

    sensitive_hits = find_sensitive_leaks(body_text)
    assert not sensitive_hits, (
        f"Sensitive data pattern detected via error-based payload "
        f"{payload!r} on field '{field_name}': {sensitive_hits}"
    )


# ============================================================================
# ENCODING / OBFUSCATION SQL INJECTION TESTS
# ============================================================================

@pytest.mark.negative
@pytest.mark.parametrize(
    "field_name",
    list(INJECTABLE_FIELDS.keys()),
)
@pytest.mark.parametrize(
    "payload",
    ENCODING_OBFUSCATION_PAYLOADS,
)
def test_sql_injection_encoding_obfuscation(
    module_onboarding_client,
    fresh_onboarding_context,
    field_name,
    payload,
):
    """
    Test encoding and obfuscation SQL injection bypass techniques.

    These payloads check whether WAF rules or input sanitization
    can be bypassed by encoding the injection characters in
    URL-encoded, HTML-entity, Unicode, or CHAR() form.
    """

    offer_uuid = fresh_onboarding_context["offer_uuid"]
    token = fresh_onboarding_context["token"]
    baseline_payload = fresh_onboarding_context["payload"]

    onboarding_payload = _build_payload(
        field_name,
        payload,
        baseline_payload,
    )

    response = (
        module_onboarding_client.submit_onboarding(
            offer_uuid,
            token,
            onboarding_payload,
        )
    )

    _log_evidence(
        "encoding_obfuscation",
        field_name,
        payload,
        response,
    )

    _assert_safe_response(
        response,
        payload,
        field_name,
    )

    body_text = getattr(response, "text", "") or ""

    version_hits = find_version_string_leaks(body_text)
    assert not version_hits, (
        f"DB version string leaked via obfuscated payload "
        f"{payload!r} on field '{field_name}': {version_hits}"
    )


# ============================================================================
# HEADER INJECTION TESTS
# ============================================================================

_INJECTABLE_HEADERS = {
    "X-Forwarded-For": "127.0.0.1' OR '1'='1",
    "User-Agent": "Mozilla' OR '1'='1",
    "Referer": "https://example.com/' OR 1=1--",
    "X-Real-IP": "127.0.0.1' OR SLEEP(0)--",
}


@pytest.mark.negative
@pytest.mark.parametrize(
    "header_name,sqli_value",
    list(_INJECTABLE_HEADERS.items()),
)
def test_sql_injection_via_http_headers(
    module_onboarding_client,
    fresh_onboarding_context,
    header_name,
    sqli_value,
):
    """
    Test SQL injection via HTTP request headers.

    Some backends log or store request headers (IP, User-Agent, Referer)
    and pass them unsanitized to database queries. This test injects
    SQL payloads in common headers and checks the response for:
        - SQL error signatures
        - DB version string leaks
        - Unexpected 500 server errors
    """

    offer_uuid = fresh_onboarding_context["offer_uuid"]
    token = fresh_onboarding_context["token"]
    baseline_payload = fresh_onboarding_context["payload"]

    # Clone the client's existing headers and inject the SQLi header.
    injection_headers = {
        header_name: sqli_value,
    }

    print(
        "\n"
        "========================================\n"
        "SQLI HEADER INJECTION TEST\n"
        "========================================\n"
        f"Header : {header_name}\n"
        f"Value  : {sqli_value!r}\n"
    )

    response = module_onboarding_client.submit_onboarding(
        offer_uuid,
        token,
        copy.deepcopy(baseline_payload),
        extra_headers=injection_headers,
    )

    status = getattr(response, "status_code", None)
    body_text = getattr(response, "text", "") or ""

    sql_errors = find_sql_error_signatures(body_text)
    version_hits = find_version_string_leaks(body_text)

    print(
        f"[HEADER SQLI] header={header_name!r} "
        f"status={status} "
        f"sql_errors={sql_errors or 'none'} "
        f"version_leaks={version_hits or 'none'}"
    )

    assert not sql_errors, (
        f"SQL error signature leaked via header '{header_name}' "
        f"with value {sqli_value!r}: {sql_errors}"
    )

    assert not version_hits, (
        f"DB version string leaked via header '{header_name}' "
        f"with value {sqli_value!r}: {version_hits}"
    )

    assert status != 500, (
        f"Server error (500) triggered by SQL payload in header "
        f"'{header_name}' with value {sqli_value!r}. "
        "The backend may be passing this header unsanitized to a query."
    )