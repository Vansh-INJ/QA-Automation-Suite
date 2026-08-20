from pages.onboarding_page import OnboardingPage
from pages.compensation_page import CompensationPage
from pages.candidate_form_filler import CandidateFormFiller
from utils.test_context import TEST_CONTEXT
from utils.test_data_generator import (
    unique_first_name,
    unique_last_name,
    unique_email
)
from utils.test_context import TEST_CONTEXT
import os


class AddEmployeePage:

    def __init__(self, page):
        self.page = page
        self.onboarding = OnboardingPage(page)
        self.compensation = CompensationPage(page)
        self.filler = CandidateFormFiller(page)

    
    def create_multiple_employees(self, employee, count=1):
        """
        Creates multiple employees using the existing flow.

        Args:
            employee (dict): Employee test data.
            count (int): Number of employees to create.
        """

        created_employees = []

        for i in range(count):
            print("\n" + "=" * 70)
            print(f"Creating Employee {i + 1} of {count}")
            print("=" * 70)

            # Open Add Employee page
            self.open()

            # Employment Details
            self.fill_employee_details(employee)

            # Compensation
            self.fill_compensation()

            # Additional Details
            self.fill_additional_details()

            # Documents
            self.fill_documents()

            # Profile Picture
            self.upload_profile_picture()

            # Save Employee
            payload = self.create_employee()

            created_employees.append({
                "emp_code": TEST_CONTEXT.get("emp_code"),
                "user_uuid": TEST_CONTEXT.get("user_uuid"),
                "email": TEST_CONTEXT.get("email"),
                "first_name": TEST_CONTEXT.get("first_name"),
                "last_name": TEST_CONTEXT.get("last_name")
            })

            print(f"Employee {i + 1} Created Successfully")

        return created_employees

        
    def fill_documents(self):

        self.click_tab(
            "Documents"
        )

        document_path = os.path.join(
            os.getcwd(),
            "test_data",
            "test_document.pdf"
        )

        required_documents = [
            "doc-aadhar",
            "doc-cancelled_cheque",
            "doc-experience_certificate",
            "doc-pan",
            "doc-relieving_certificate",
            "doc-resume",
            "doc-x_marksheet",
            "doc-xii_marksheet"
        ]

        print(
            f"\n[DOCUMENT UPLOAD STARTED]"
        )

        for doc_id in required_documents:

            try:

                self.page.locator(
                    f"#{doc_id}"
                ).set_input_files(
                    document_path
                )

                print(
                    f"[UPLOADED] {doc_id}"
                )

                self.page.wait_for_timeout(
                    500
                )

            except Exception as e:

                print(
                    f"[FAILED] {doc_id} : {e}"
                )
                raise

        print(
            "[DOCUMENT UPLOAD COMPLETED]"
        )

    
    def upload_profile_picture(self):

        image_path = os.path.join(
            os.getcwd(),
            "test_data",
            "profile_picture.jpg"
        )

        # Upload image
        self.page.locator(
            "input[type='file']"
        ).set_input_files(
            image_path
        )

        # Wait for crop modal/button
        crop_btn = self.page.get_by_role(
            "button",
            name="Crop Image"
        )

        crop_btn.wait_for(
            state="visible",
            timeout=15000
        )

        crop_btn.click()

        # Wait until crop modal disappears
        crop_btn.wait_for(
            state="hidden",
            timeout=15000
        )

        self.page.wait_for_load_state(
            "networkidle"
        )

        self.page.wait_for_timeout(
            1000
        )

    def open(self):
        self.page.goto(
            "https://injin.injtechnologies.com/hr/users/add",
            wait_until="networkidle"
        )

    def fill_employee_details(self, employee):

        first_name = unique_first_name()
        last_name = unique_last_name()
        email = unique_email()
        personal_email = unique_email()

        self.page.locator("#first_name").fill(first_name)
        self.page.locator("#middle_name").fill(
            employee.get("middle_name", "")
        )
        self.page.locator("#last_name").fill(last_name)
        self.page.locator("#email").fill(email)
        self.page.locator("#personal_email").fill(personal_email)

        TEST_CONTEXT["first_name"] = first_name
        TEST_CONTEXT["last_name"] = last_name
        TEST_CONTEXT["email"] = email
        TEST_CONTEXT["personal_email"] = personal_email

        # Reuse onboarding dropdown methods
        # Department
        self.onboarding.select_dropdown(
            "Select department",
            employee["department"]
        )

        # Handle dynamic dropdowns like sub-department
        self.onboarding.handle_dynamic_dropdowns_after_department()

        # Job Title
        self.onboarding.select_dropdown(
            "Select job title"
        )

        # Reporting Manager
        self.onboarding.select_dropdown(
            "Select reporting manager"
        )

        # Hierarchy Level
        self.onboarding.select_dropdown(
            "Select hierarchy level"
        )

        # Job Offered
        self.onboarding.select_dropdown(
            "Select job offered",
            employee["job_offered"]
        )

        # Employee Type
        self.onboarding.select_dropdown(
            "Select Employment Type",
            employee["employee_type"]
        )

        # Company Entity
        self.onboarding.select_dropdown(
            "Select company entity",
            employee["company_entity"]
        )

        # Work Location
        self.onboarding.select_dropdown(
            "Select Work Location"
        )

        # Fill any remaining dropdowns (e.g. shift, grade, etc.)
        self.onboarding.fill_remaining_dropdowns()

        # self.page.pause()

        # Date of Joining
       # ---------------- Date of Joining ---------------- #

        joining_date = employee.get("joining_date")

        if joining_date:
            from datetime import datetime
            try:
                doj = datetime.strptime(joining_date, "%d/%m/%y")
            except ValueError:
                doj = datetime.strptime(joining_date, "%d-%m-%Y")

            target_day = f"{doj.month}/{doj.day}/{doj.year}"
            print(f"[JOINING DATE] Selecting: {target_day}")

            try:
                # Try finding the trigger relative to the label
                date_btn = self.page.locator("label:has-text('Date of Joining')").locator("..").locator('button[data-slot="popover-trigger"]')
                if date_btn.count() == 0:
                    date_btn = self.page.locator('button[data-slot="popover-trigger"]').last
            except Exception:
                date_btn = self.page.locator('button[data-slot="popover-trigger"]').last

            date_btn.first.click()

            day_btn = self.page.locator(f'button[data-day="{target_day}"]')
            day_btn.first.wait_for(state="visible", timeout=5000)
            day_btn.first.click()
            print("[JOINING DATE] Date selected successfully")

        # Validate that all required fields on the first tab are filled
        missing = self.onboarding.check_unfilled_required_fields()
        print(f"\n[Validation] Missing Fields on Employment Details: {missing}")
        assert len(missing) == 0, f"Required fields on first tab still empty: {missing}"

    def click_tab(self, name):
        tab_btn = self.page.get_by_role("tab", name=name)
        tab_btn.wait_for(state="visible", timeout=10000)
        tab_btn.scroll_into_view_if_needed()
        tab_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def fill_compensation(self):

        self.click_tab("Compensation Details")

        self.compensation.select_salary_structure()

        self.compensation.fill_all_visible_inputs()

        self.compensation.click_calculate()

    def fill_additional_details(self):

        self.click_tab("Additional Details")

        self.filler.fill_current_tab()

        # Validate that all required fields on the third tab are filled
        from utils.dynamic_form_validator import validate_current_tab
        missing = validate_current_tab(self.page)
        print(f"\n[Validation] Missing Fields on Additional Details: {missing}")
        assert len(missing) == 0, f"Required fields on third tab still empty: {missing}"

    def click_save_employee(self):

        self.page.get_by_role(
            "button",
            name="Save Employee"
        ).click()

    def create_employee(self):

        # Click Save Employee
        self.page.get_by_role(
            "button",
            name="Save Employee"
        ).click()

        # Wait for confirmation dialog
        continue_btn = self.page.locator(
            '[data-slot="alert-dialog-action"]'
        )

        continue_btn.wait_for(
            state="visible",
            timeout=10000
        )

        # Listen for API triggered by Continue click
        with self.page.expect_response(
            lambda response:
            "api/hr/offers/create-employee"
            in response.url
            and response.request.method == "POST"
        ) as response_info:

            continue_btn.click(force=True)

        response = response_info.value

        assert response.ok, (
            f"Create Employee API Failed : "
            f"{response.status}"
        )

        payload = response.json()

        assert payload["status"] == "success"

        TEST_CONTEXT["user_uuid"] = (
            payload["data"]["user_uuid"]
        )

        TEST_CONTEXT["emp_code"] = (
            payload["data"]["emp_code"]
        )

        print(
            f"Employee Created : "
            f"{TEST_CONTEXT['emp_code']}"
        )

        print(
            f"UUID : "
            f"{TEST_CONTEXT['user_uuid']}"
        )

        return payload