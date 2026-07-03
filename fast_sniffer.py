import os
import urllib.parse
from playwright.sync_api import sync_playwright
from api_framework.clients.offer_client import OfferClient
from api_framework.auth.token_manager import TokenManager
from api_framework.config.settings import Settings
from api_framework.payloads.offer_payloads import OfferPayloads

def run():
    print("Generating offer...")
    client = OfferClient(base_url=Settings.BASE_URL, headers=TokenManager.get_headers())
    res = client.send_offer(OfferPayloads.valid())
    invite_link = res.json()["data"]["invite_link"]
    print("Got invite link:", invite_link)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_request(request):
            if "upload" in request.url.lower() or request.method == "POST":
                if "/api/" in request.url:
                    print(f"API Request: {request.method} {request.url}")

        def handle_response(response):
            if "upload" in response.url.lower() and "/api/" in response.url:
                print(f"API Response: {response.status} {response.url}")
                try:
                    print("Body:", response.text())
                except:
                    pass

        page.on("request", handle_request)
        page.on("response", handle_response)

        print("Navigating...")
        page.goto(invite_link)
        page.wait_for_timeout(3000)

        print("Clicking Start Onboarding...")
        try:
            page.get_by_role("button", name="Start Onboarding").click()
            page.wait_for_timeout(2000)
        except:
            pass
            
        print("Uploading Profile Image...")
        try:
            page.get_by_role("button", name="Upload").first.click()
            page.get_by_label("Choose a file").set_input_files("test_data/test_document.pdf")
            page.wait_for_timeout(5000)
        except Exception as e:
            print("Failed to upload:", e)

        print("Done")
        browser.close()

if __name__ == "__main__":
    run()
