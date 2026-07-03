from api_framework.clients.base_client import BaseClient
import os


class OnboardingClient(BaseClient):

    def submit_onboarding(
            self,
            offer_uuid,
            token,
            payload
    ):
        return self.post(
            f"/api/onboarding/{offer_uuid}/submit?token={token}",
            payload
        )

    def accept_offer(
            self,
            offer_uuid,
            token
    ):
        return self.post(
            f"/api/public/offers/{offer_uuid}/accept?token={token}"
        )

    def upload_document(
            self,
            offer_uuid,
            token,
            file_path,
            document_type
    ):
        with open(file_path, "rb") as file:

            files = {
                "file": (
                    os.path.basename(file_path),
                    file,
                    "application/pdf"
                )
            }

            data = {
                "document_type": document_type
            }

            return self.post(
                f"/api/onboarding/{offer_uuid}/document?token={token}",
                data=data,
                files=files
            )