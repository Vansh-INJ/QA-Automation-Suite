import os
from playwright.sync_api import sync_playwright

def run():
    invite_link = "https://injin-dev.injtechnologies.com/onboarding/d34118ae-aa86-444f-82c5-32a310c357e5?token=5b0e94e5fc617384b4b1f5d9cebccb3ee2c61ee6c3c9155632a17dddf596c656"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_request(request):
            if "upload" in request.url.lower() or request.method == "POST":
                # Only print API calls
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
        # Start the onboarding process
        try:
            page.get_by_role("button", name="Start Onboarding").click()
            page.wait_for_timeout(2000)
        except:
            pass
            
        print("Uploading Profile Image...")
        # Try uploading to profile image to catch the upload endpoint
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
