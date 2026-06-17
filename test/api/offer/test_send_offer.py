from utils.test_context import TEST_CONTEXT

from api_framework.payloads.offer_payloads import (
    OfferPayloads
)


def test_send_offer(
        authenticated_offer_client
):

    payload = (
        OfferPayloads.valid()
    )

    # ======================================
    # POPULATE TEST_CONTEXT
    # ======================================
    # Set this BEFORE the request goes out (and before any asserts) so that
    # candidate name/email are still logged to Excel even if the request
    # fails or an assertion below raises.

    TEST_CONTEXT["action"] = "Send Offer"

    TEST_CONTEXT["candidate_name"] = (
        f"{payload['first_name']} {payload['last_name']}".strip()
    )

    TEST_CONTEXT["candidate_email"] = payload["email"]

    response = (
        authenticated_offer_client
        .send_offer(
            payload
        )
    )

    print(
        "\nStatus:",
        response.status_code
    )

    print(
        "\nResponse:",
        response.json()
    )

    body = response.json()

    # ======================================
    # CAPTURE API RESULT INTO TEST_CONTEXT
    # ======================================
    # Done right after the response is available, before asserts, for the
    # same reason as above — a failed assertion shouldn't blank these out.

    TEST_CONTEXT["api_status"] = response.status_code

    TEST_CONTEXT["api_message"] = body.get(
        "message",
        body.get("status", "")
    )

    TEST_CONTEXT["api_response"] = body

    # ======================================
    # EXPECTED STATUS + SLA
    # ======================================
    # expected_status: what you're about to assert against below.
    # sla: max acceptable response time in ms for this endpoint - pick a
    # number that reflects what's actually acceptable for /offers/send,
    # not just whatever happened to come back today.

    TEST_CONTEXT["expected_status"] = 200
    TEST_CONTEXT["sla"] = 500

    assert (
        response.status_code
        == 200
    )

    assert (
        body["status"]
        == "success"
    )

    assert (
        "offer_uuid"
        in body["data"]
    )

    assert (
        "invite_link"
        in body["data"]
    )