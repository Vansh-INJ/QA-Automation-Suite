import time

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
    # Populate context before request
    # ======================================

    TEST_CONTEXT["action"] = "Send Offer"

    TEST_CONTEXT["candidate_name"] = (
        f"{payload['first_name']} "
        f"{payload['last_name']}"
    ).strip()

    TEST_CONTEXT["candidate_email"] = (
        payload["email"]
    )

    # ======================================
    # Execute API and measure SLA
    # ======================================

    start = time.time()

    response = (
        authenticated_offer_client
        .send_offer(payload)
    )

    response_time_ms = (
        time.time() - start
    ) * 1000

    print(
        "\nResponse Time:",
        f"{response_time_ms:.2f} ms"
    )

    body = response.json()

    print(
        "\nStatus:",
        response.status_code
    )

    print(
        "\nResponse:",
        body
    )

    # ======================================
    # Store API results
    # ======================================

    TEST_CONTEXT["api_status"] = (
        response.status_code
    )

    TEST_CONTEXT["api_message"] = (
        body.get(
            "message",
            body.get(
                "status",
                ""
            )
        )
    )

    TEST_CONTEXT["api_response"] = body

    TEST_CONTEXT["response_time_ms"] = round(
        response_time_ms,
        2
    )

    TEST_CONTEXT["expected_status"] = 200

    TEST_CONTEXT["sla"] = 500

    # ======================================
    # Functional assertions
    # ======================================

    assert (
        response.status_code == 200
    ), (
        f"Expected 200 "
        f"but got "
        f"{response.status_code}"
    )

    assert (
        body["status"] == "success"
    )

    assert (
        "offer_uuid"
        in body["data"]
    )

    assert (
        "invite_link"
        in body["data"]
    )

    # ======================================
    # SLA assertion
    # ======================================

    assert (
        response_time_ms
        <= TEST_CONTEXT["sla"]
    ), (
        f"API exceeded SLA. "
        f"Actual: "
        f"{response_time_ms:.2f} ms | "
        f"Expected: <= "
        f"{TEST_CONTEXT['sla']} ms"
    )