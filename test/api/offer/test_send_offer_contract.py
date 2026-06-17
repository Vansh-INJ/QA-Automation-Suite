from api_framework.payloads.offer_payloads import (
    OfferPayloads
)


def test_send_offer_response_contract(
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

    assert (
        response.status_code
        == 200
    )

    body = response.json()

    #
    # Top Level
    #

    assert (
        "status"
        in body
    )

    assert (
        "data"
        in body
    )

    assert (
        body["status"]
        == "success"
    )

    #
    # Data Section
    #

    data = body["data"]

    assert (
        "offer_uuid"
        in data
    )

    assert (
        "invite_link"
        in data
    )

    assert (
        isinstance(
            data["offer_uuid"],
            str
        )
    )

    assert (
        isinstance(
            data["invite_link"],
            str
        )
    )

    assert (
        data["offer_uuid"]
    )

    assert (
        data["invite_link"]
    )