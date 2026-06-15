from pages.onboarding_page import OnboardingPage
from pages.compensation_page import CompensationPage
from utils.test_context import TEST_CONTEXT
from utils.test_data_generator import (
    unique_first_name,
    unique_last_name,
    unique_email
)
import os


class AddEmployeePage:

    def __init__(self, page):
        self.page = page
        self.onboarding = OnboardingPage(page)
        self.compensation = CompensationPage(page)

    def open(self):
        self.page.goto(
            "https://injin.injtechnologies.com/hr/users/add",
            wait_until="networkidle"
        )

    def fill_employee_details(self, employee):

        first_name = unique_first_name()
        last_name = unique_last_name()
        email = unique_email()

        self.page.locator("#first_name").fill(first_name)
        self.page.locator("#middle_name").fill(
            employee.get("middle_name", "")
        )
        self.page.locator("#last_name").fill(last_name)
        self.page.locator("#email").fill(email)

        TEST_CONTEXT["first_name"] = first_name
        TEST_CONTEXT["last_name"] = last_name
        TEST_CONTEXT["email"] = email

        # Reuse onboarding dropdown methods
        # Department
        self.onboarding.select_dropdown(
            "Select department",
            employee["department"]
        )

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
            "Select type",
            employee["employee_type"]
        )

        # Company Entity
        self.onboarding.select_dropdown(
            "Select company entity",
            employee["company_entity"]
        )

        # Work Location
        self.onboarding.select_dropdown(
            "Select location"
        )

    def fill_compensation(self):

        self.compensation.select_salary_structure()

        self.compensation.fill_all_visible_inputs()

        self.compensation.click_calculate()

    def click_save_employee(self):

        self.page.get_by_role(
            "button",
            name="Save Employee"
        ).click()

    def create_employee(self):

        with self.page.expect_response(
            lambda response:
            "api/hr/offers/create-employee"
            in response.url
            and response.status == 200
        ) as response_info:

            self.click_save_employee()

        response = response_info.value
        payload = response.json()

        TEST_CONTEXT["user_uuid"] = (
            payload["data"]["user_uuid"]
        )

        TEST_CONTEXT["emp_code"] = (
            payload["data"]["emp_code"]
        )

        return payload