from api_framework.payloads.offer_payloads import (
    OfferPayloads
)

def test_send_offer(
        authenticated_offer_client
):

    payload = (
        OfferPayloads.valid()
    )

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

    assert (
        response.status_code
        == 200
    )

    body = response.json()

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