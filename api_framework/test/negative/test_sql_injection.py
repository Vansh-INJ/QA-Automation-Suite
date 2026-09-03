import os
import copy
import time

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
# SQL INJECTION SECURITY FRAMEWORK
# ============================================================================
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
)

from api_framework.security.core.sqli_fields import (
    INJECTABLE_FIELDS,
)

from api_framework.security.core.sqli_engine import (
    build_injected_payload,
    find_sql_error_signatures,
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

@pytest.fixture(scope="module")
def module_offer_client():
    """
    Module-scoped OfferClient used for creating the real offer required
    by the SQL injection tests.
    """

    from api_framework.auth.token_manager import TokenManager

    return OfferClient(
        base_url=Settings.BASE_URL,
        headers=TokenManager.get_headers(),
    )


@pytest.fixture(scope="module")
def module_onboarding_client():
    """
    Module-scoped onboarding client used by the setup fixture.
    """

    return OnboardingClient(
        base_url=Settings.BASE_URL,
    )


@pytest.fixture(scope="module")
def accepted_offer_context(
    module_offer_client,
    module_onboarding_client,
):
    """
    Create a real offer, extract offer UUID/token, accept the offer,
    and reuse the same context for all SQL injection tests in this module.

    Returns:
        tuple[str, str]: (offer_uuid, token)
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
        "Offer creation succeeded but response did not contain "
        f"data.invite_link. Response: {send_response.text}"
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

    Returns:

        dict:
        {
            "aadhar": "<uploaded-file-uuid>",
            "pan": "<uploaded-file-uuid>",
            ...
        }
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

        print(
            f"[DOCUMENT UPLOAD] "
            f"Response={response.text[:1000]}"
        )

        assert response.status_code in (200, 201), (
            f"Failed to upload required document: {document_type}\n"
            f"Status: {response.status_code}\n"
            f"Response: {response.text}"
        )

        try:

            response_json = response.json()

        except ValueError as exc:

            raise AssertionError(
                f"Document upload returned non-JSON response "
                f"for document type '{document_type}': "
                f"{response.text!r}"
            ) from exc

        document_uuid = (
            response_json
            .get("data", {})
            .get("uuid")
        )

        assert document_uuid, (
            f"Document upload succeeded but UUID was missing "
            f"for document type '{document_type}'.\n"
            f"Response: {response.text}"
        )

        uploaded[document_type] = document_uuid

        print(
            f"[DOCUMENT UPLOAD SUCCESS] "
            f"{document_type} -> {document_uuid}"
        )

    print(
        "\n"
        "========================================\n"
        "ALL REQUIRED DOCUMENTS UPLOADED\n"
        "========================================"
    )

    for document_type, document_uuid in uploaded.items():

        print(
            f"{document_type}: {document_uuid}"
        )

    return uploaded


# ============================================================================
# DOCUMENT DEBUG TEST
# ============================================================================

@pytest.mark.negative
def test_document_upload_debug(
    module_onboarding_client,
    accepted_offer_context,
):
    """
    Standalone diagnostic test.

    Run:

        pytest test/negative/test_sql_injection.py \
            -k document_upload_debug -v -s
    """

    offer_uuid, token = accepted_offer_context

    response = (
        module_onboarding_client.upload_document(
            offer_uuid=offer_uuid,
            token=token,
            file_path=TEST_DOCUMENT_PATH,
            document_type="aadhar",
        )
    )

    print("\n[DOCUMENT UPLOAD DEBUG]")

    print(
        f"File Path: {TEST_DOCUMENT_PATH}"
    )

    print(
        f"Status: {response.status_code}"
    )

    print(
        f"Response: {response.text}"
    )

    assert response.status_code in (200, 201)


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
    Create and validate one clean baseline onboarding payload.

    Every SQL injection test uses a deep copy of this validated payload.
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

    print(
        "\n[BASELINE DOCUMENT UUIDS]"
    )

    for document_type, document_uuid in (
        baseline_payload["documents"].items()
    ):

        print(
            f"{document_type}: {document_uuid}"
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
    Build an offer payload using fresh, active master-data IDs.
    """

    payload = copy.deepcopy(
        OfferPayloads.valid()
    )

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
            "No active job titles returned by MasterData."
        )

    if not legal_entities:

        raise AssertionError(
            "No active legal entities returned by MasterData."
        )

    if not work_locations:

        raise AssertionError(
            "No active work locations returned by MasterData."
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

            "sub_function_id": (
                sub_function["uuid"]
            ),

            "job_title_id": (
                job_title["uuid"]
            ),

            "legal_entity_id": (
                legal_entity["uuid"]
            ),

            "work_location_id": (
                work_location["uuid"]
            ),

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
    Extract (offer_uuid, token) from invite_link.
    """

    if not invite_link:

        raise AssertionError(
            "invite_link is empty or missing."
        )

    parsed = urlparse(
        invite_link
    )

    path_parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    if not path_parts:

        raise AssertionError(
            "Could not parse offer_uuid from invite_link: "
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
            "Could not parse token from invite_link: "
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

    offer_payload = (
        _build_live_offer_payload(
            master
        )
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
# HELPER FUNCTIONS
# ============================================================================

def _build_payload(
    field_name: str,
    malicious_value,
    baseline_payload: dict,
) -> dict:
    """
    Create a deep copy of the validated baseline payload and inject
    a malicious value into the specified field.
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
    Wrapper around centralized SQLi evidence reporter.
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
    Wrapper around centralized SQLi assertion utility.
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
    Build a response signature for boolean blind comparison.
    """

    return build_response_signature(
        response
    )


def _extract_error_message(
    response,
) -> str:
    """
    Extract readable error message.
    """

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
    Verify clean onboarding payload does not cause server failure.
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

    error_message = (
        _extract_error_message(
            response
        )
    )

    print(
        "\n[BASELINE PAYLOAD CHECK]\n"
        f"Status   : {status}\n"
        f"Response : {response_text[:2000]!r}\n"
    )

    assert status is not None, (
        "Baseline onboarding prerequisite did not receive "
        "an HTTP response."
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
        "The malicious payload is not responsible for "
        "this failure.\n"
        "========================================"
    )

    missing_document_message = (
        "missing required document"
    )

    assert missing_document_message not in (
        response_text.lower()
    ), (
        "\n"
        "========================================\n"
        "DOCUMENT PREREQUISITE FAILURE\n"
        "========================================\n"
        "The onboarding API still reports missing documents "
        "even though upload requests completed.\n\n"
        f"Response: {response_text}\n"
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
    accepted_offer_context,
    validated_onboarding_payload,
    field_name,
    payload,
):

    offer_uuid, token = accepted_offer_context

    onboarding_payload = _build_payload(
        field_name,
        payload,
        validated_onboarding_payload,
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
    accepted_offer_context,
    validated_onboarding_payload,
    field_name,
    payload,
):

    offer_uuid, token = accepted_offer_context

    onboarding_payload = _build_payload(
        field_name,
        payload,
        validated_onboarding_payload,
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
    accepted_offer_context,
    validated_onboarding_payload,
    field_name,
    payload,
):

    offer_uuid, token = accepted_offer_context

    onboarding_payload = _build_payload(
        field_name,
        payload,
        validated_onboarding_payload,
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
    ).lower()

    suspicious_keys = (
        "password_hash",
        "credit_card",
        "social_security",
    )

    for suspicious_key in suspicious_keys:

        assert suspicious_key not in body_text, (
            f"Possible sensitive data leakage: "
            f"'{suspicious_key}' found in response after "
            f"UNION-based payload {payload!r} "
            f"on field '{field_name}'."
        )


# ============================================================================
# TIME BASED BLIND SQL INJECTION TESTS
# ============================================================================

@pytest.mark.negative
@pytest.mark.parametrize(
    "payload",
    TIME_BASED_SQLI_PAYLOADS,
)
def test_sql_injection_time_based_blind(
    module_onboarding_client,
    accepted_offer_context,
    validated_onboarding_payload,
    payload,
):

    offer_uuid, token = accepted_offer_context

    onboarding_payload = _build_payload(
        "bank.account_holder_name",
        payload,
        validated_onboarding_payload,
    )

    start = time.monotonic()

    response = (
        module_onboarding_client.submit_onboarding(
            offer_uuid,
            token,
            onboarding_payload,
        )
    )

    elapsed = (
        time.monotonic() - start
    )

    _log_evidence(
        "time_based_blind",
        "bank.account_holder_name",
        payload,
        response,
        elapsed,
    )

    assert elapsed < TIME_BASED_THRESHOLD_SECONDS, (
        f"Response took {elapsed:.2f}s "
        f"(threshold {TIME_BASED_THRESHOLD_SECONDS}s) "
        f"for time-based payload {payload!r} — "
        "possible blind SQL injection vulnerability."
    )

    _assert_safe_response(
        response,
        payload,
        "bank.account_holder_name",
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
    accepted_offer_context,
    validated_onboarding_payload,
    field_name,
    true_payload,
    false_payload,
):

    offer_uuid, token = accepted_offer_context

    true_payload_body = _build_payload(
        field_name,
        true_payload,
        validated_onboarding_payload,
    )

    false_payload_body = _build_payload(
        field_name,
        false_payload,
        validated_onboarding_payload,
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

    true_signature = (
        _response_signature(
            true_response
        )
    )

    false_signature = (
        _response_signature(
            false_response
        )
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
    [
        {
            "username": "admin' --",
            "password": "anything",
        },
        {
            "username": "admin' OR '1'='1",
            "password": "' OR '1'='1",
        },
    ],
)
def test_sql_injection_login_bypass_attempt(
    credentials,
):
    """
    Test SQL injection authentication bypass attempts.
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
                    key.lower()
                    in possible_token_keys
                    and value
                ):

                    returned_tokens.append(
                        key
                    )

                if isinstance(
                    value,
                    (dict, list),
                ):

                    _find_tokens(
                        value
                    )

        elif isinstance(data, list):

            for item in data:

                _find_tokens(
                    item
                )

    _find_tokens(
        response_data
    )

    assert not returned_tokens, (
        "Authentication token data was returned during "
        "SQL injection login-bypass attempt. "
        f"Credentials={credentials!r}, "
        f"token_fields={returned_tokens}"
    )