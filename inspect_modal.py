import time
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Login
        page.goto("https://injin.injtechnologies.com/login")
        page.get_by_role("button", name="Fill Super Admin Credentials", exact=True).click()
        time.sleep(1)
        page.get_by_role("button", name="Login", exact=True).click()
        page.wait_for_load_state("networkidle")
        
        # Onboarding
        page.goto("https://injin.injtechnologies.com/hr/users/onboarding")
        page.get_by_role("button", name="Employee Onboarding").click()
        
        time.sleep(2)
        
        # Extract text from the modal
        texts = page.locator("body").inner_text()
        print(texts)
        
        browser.close()

if __name__ == "__main__":
    run()
