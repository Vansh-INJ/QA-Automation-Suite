from api_framework.clients.base_client import (
    BaseClient
)


class OfferClient(BaseClient):

    def send_offer(
            self,
            payload
    ):
        return self.post(
            "/api/hr/offers/send",
            payload
        )