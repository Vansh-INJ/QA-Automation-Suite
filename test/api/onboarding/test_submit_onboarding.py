import urllib.parse
from utils.test_context import TEST_CONTEXT

from api_framework.payloads.offer_payloads import OfferPayloads
from api_framework.payloads.onboarding_payloads import (
    OnboardingPayloads
)


def test_submit_onboarding(
        authenticated_offer_client,
        onboarding_client
):
    # ======================================
    # 1. GENERATE AN OFFER
    # ======================================
    offer_payload = OfferPayloads.valid()

    # Store candidate info for Excel logging
    TEST_CONTEXT["action"] = "Submit Onboarding API"
    TEST_CONTEXT["candidate_name"] = (
        f"{offer_payload['first_name']} "
        f"{offer_payload['last_name']}"
    ).strip()
    TEST_CONTEXT["candidate_email"] = (
        offer_payload["email"]
    )

    offer_response = (
        authenticated_offer_client
        .send_offer(offer_payload)
    )

    assert (
        offer_response.status_code == 200
    ), "Failed to create offer"

    offer_body = offer_response.json()
    invite_link = (
        offer_body["data"]["invite_link"]
    )

    # ======================================
    # 2. EXTRACT UUID AND TOKEN
    # ======================================
    parsed_url = urllib.parse.urlparse(
        invite_link
    )

    query_params = urllib.parse.parse_qs(
        parsed_url.query
    )

    token = query_params["token"][0]
    offer_uuid = (
        parsed_url.path.split("/")[-1]
    )

    print(f"\n[OFFER UUID] {offer_uuid}")
    print(f"[TOKEN] {token[:20]}...")

    # ======================================
    # 3. ACCEPT OFFER
    # ======================================
    accept_response = (
        onboarding_client.accept_offer(
            offer_uuid=offer_uuid,
            token=token
        )
    )

    print(
        "\nAccept Offer Status:",
        accept_response.status_code
    )

    try:
        print(
            "Accept Offer Response:",
            accept_response.json()
        )
    except Exception:
        print(
            "Accept Offer Response:",
            accept_response.text
        )

    assert (
        accept_response.status_code == 200
    ), (
        "Failed to accept offer: "
        f"{accept_response.text}"
    )

    accept_body = (
        accept_response.json()
    )

    assert (
        accept_body["status"] == "success"
    ), (
        f"Offer acceptance failed: "
        f"{accept_body}"
    )

    print("[OFFER ACCEPTED]")

    # ======================================
    # 4. UPLOAD DOCUMENTS
    # ======================================
    onboarding_payload = (
        OnboardingPayloads.valid()
    )

    document_types = [
        "aadhar",
        "cancelled_cheque",
        "experience_certificate",
        "pan",
        "relieving_certificate",
        "resume",
        "x_marksheet",
        "xii_marksheet"
    ]

    file_path = (
        "test_data/test_document.pdf"
    )

    for doc_type in document_types:

        upload_res = (
            onboarding_client
            .upload_document(
                offer_uuid=offer_uuid,
                token=token,
                file_path=file_path,
                document_type=doc_type
            )
        )

        assert (
            upload_res.status_code == 200
        ), (
            f"Upload failed for "
            f"{doc_type}: "
            f"{upload_res.text}"
        )

        doc_uuid = (
            upload_res
            .json()["data"]["uuid"]
        )

        onboarding_payload[
            "documents"
        ][doc_type] = doc_uuid

        print(
            f"[DOCUMENT UPLOADED] "
            f"{doc_type}"
        )

    # ======================================
    # 5. SUBMIT ONBOARDING
    # ======================================
    submit_response = (
        onboarding_client
        .submit_onboarding(
            offer_uuid=offer_uuid,
            token=token,
            payload=onboarding_payload
        )
    )

    print(
        "\nSubmit Onboarding Status:",
        submit_response.status_code
    )

    try:
        print(
            "Submit Onboarding Response:",
            submit_response.json()
        )
    except Exception:
        print(
            "Submit Onboarding Response:",
            submit_response.text
        )

    body = submit_response.json()

    # Capture result into context for Excel reporting
    TEST_CONTEXT["api_status"] = (
        submit_response.status_code
    )
    TEST_CONTEXT["api_message"] = (
        body.get("data", {})
        .get(
            "message",
            body.get("status", "")
        )
    )
    TEST_CONTEXT["api_response"] = body
    TEST_CONTEXT["expected_status"] = 200
    TEST_CONTEXT["sla"] = 1000

    # ======================================
    # 6. ASSERTIONS
    # ======================================
    assert (
        submit_response.status_code == 200
    ), (
        f"Expected 200, got "
        f"{submit_response.status_code}"
    )

    assert (
        body["status"] == "success"
    ), (
        f"Expected success status, "
        f"got {body.get('status')}"
    )

    data = body.get("data", {})

    assert (
        "message" in data
    ), "No message in response data"

    assert (
        data["message"]
        == "Onboarding submitted successfully"
    ), (
        f"Unexpected message: "
        f"{data['message']}"
    )

    assert (
        "request_uuid" in data
    ), "No request_uuid in response data"

    print(
        f"[ONBOARDING SUBMITTED] "
        f"Request UUID: "
        f"{data['request_uuid']}"
    )