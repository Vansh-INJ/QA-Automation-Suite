from api_framework.payloads.offer_payloads import (
    OfferPayloads
)

import time

from utils.api_logger import (
    log_api_execution
)


def test_send_offer_without_first_name(
        authenticated_offer_client
):

    payload = (
        OfferPayloads.valid()
    )

    del payload["first_name"]

    response = (
        authenticated_offer_client
        .send_offer(
            payload
        )
    )

    print("\nMissing First Name")
    print("Status:", response.status_code)
    print("Response:", response.json())


def test_send_offer_without_email(
        authenticated_offer_client
):

    payload = (
        OfferPayloads.valid()
    )

    del payload["email"]

    response = (
        authenticated_offer_client
        .send_offer(
            payload
        )
    )

    print("\nMissing Email")
    print("Status:", response.status_code)
    print("Response:", response.json())


def test_send_offer_with_invalid_email(
        authenticated_offer_client
):

    payload = (
        OfferPayloads.valid()
    )

    payload["email"] = "abc"

    response = (
        authenticated_offer_client
        .send_offer(
            payload
        )
    )

    print("\nInvalid Email")
    print("Status:", response.status_code)
    print("Response:", response.json())


def test_send_offer_with_negative_salary(
        authenticated_offer_client
):

    payload = (
        OfferPayloads.valid()
    )

    payload[
        "gross_monthly_salary"
    ] = -1000

    start = time.time()

    response = (
        authenticated_offer_client
        .send_offer(
            payload
        )
    )

    log_api_execution(
        test_name=
        "test_send_offer_with_negative_salary",

        method=
        "POST",

        endpoint=
        "/api/hr/offers/send",

        payload=
        payload,

        response=
        response,

        start_time=
        start,

        expected_status=
        422
    )

    print("\nNegative Salary")
    print("Status:", response.status_code)
    print("Response:", response.json())

    assert (
        response.status_code
        == 422
    )