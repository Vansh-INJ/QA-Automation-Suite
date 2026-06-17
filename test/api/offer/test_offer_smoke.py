import time
import pytest

from api_framework.config.settings import Settings
from api_framework.payloads.offer_payloads import (
    OfferPayloads
)
from utils.helpers import (
    log_api_execution
)


@pytest.mark.smoke
def test_offer_creation_smoke(
        authenticated_offer_client
):

    payload = OfferPayloads.valid()

    start_time = time.time()

    response = (
        authenticated_offer_client
        .send_offer(payload)
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "success"
    assert "data" in body
    assert "offer_uuid" in body["data"]
    assert "invite_link" in body["data"]

    log_api_execution(
        test_name="TC-OFF-001 Offer Creation Smoke",
        method="POST",
        endpoint="/api/hr/offers/send",
        payload=payload,
        response=response,
        start_time=start_time,
        expected_status=200,
        environment="SIT",
        username=Settings.API_USERNAME
    )