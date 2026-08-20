import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from pages.add_employee_page import AddEmployeePage

def debug():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # login
        login = LoginPage(page)
        login.open()
        login.login.login()
        
        employee = AddEmployeePage(page)
        employee.open()
        
        employee.click_tab("Additional Details")
        page.wait_for_timeout(2000)
        
        # click dob
        dob_button = page.locator("#personal-date_of_birth-0")
        if dob_button.count() == 0:
            print("DOB button not found by ID")
            # Try alternate locator
            dob_button = page.locator("label:has-text('Date of Birth')").locator("..").locator("button")
            if dob_button.count() == 0:
                print("Could not find DOB button at all.")
                return
            else:
                dob_button = dob_button.first

        print(f"Clicking DOB button...")
        dob_button.click()
        page.wait_for_timeout(1000)
        
        year_dropdown = page.locator('select[aria-label="Choose the Year"]')
        if year_dropdown.count():
            html = year_dropdown.first.evaluate("el => el.innerHTML")
            print("YEAR DROPDOWN HTML:")
            print(html)
        else:
            print("Year dropdown not found")
            html = page.evaluate("document.body.innerHTML")
            with open("body_dump.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Dumped body to body_dump.html")
            
        browser.close()

if __name__ == "__main__":
    debug()
