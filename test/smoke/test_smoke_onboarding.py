import pytest
from conftest import page
from pages.login_page import LoginPage
from pages.onboarding_page import OnboardingPage
from pages.compensation_page import CompensationPage
from pages.candidate_onboarding_page import (
    CandidateOnboardingPage
)
from utils.run_manager import get_run_folder

RUN_FOLDER = get_run_folder()
from datetime import datetime
import os
from test_data.employee_data import (
    EMPLOYEE_PROFILES,
    CANDIDATE_DATA
)
from utils.helpers import write_field_log
from utils.test_data_generator import (
    unique_email,
    unique_first_name,
    unique_last_name
)
from utils.dynamic_form_validator import validate_all_tabs


@pytest.mark.parametrize(
    "employee_data",
    EMPLOYEE_PROFILES,
    ids=[p["test_case"] for p in EMPLOYEE_PROFILES]
)

def select_today_joining_date(page):

        target_date = datetime.now()

        target_day = (
            f"{target_date.month}/"
            f"{target_date.day}/"
            f"{target_date.year}"
        )

        print(
            f"[DOJ] Selecting Today's Date: {target_day}"
        )

        page.locator("#joining_date").click()

        page.wait_for_timeout(1000)

        target_button = page.locator(
            f'button[data-day="{target_day}"]'
        )

        target_button.first.wait_for(
            state="visible",
            timeout=5000
        )

        target_button.first.click()

        print(
            f"[DOJ Selected] {target_day}"
        )

        page.wait_for_timeout(500)

@pytest.mark.parametrize(
        "employee_data",
        EMPLOYEE_PROFILES,
        ids=[p["test_case"] for p in EMPLOYEE_PROFILES]
)



    
def test_valid_employee_onboarding(page, employee_data):

    login = LoginPage(page)
    onboarding = OnboardingPage(page)
    compensation = CompensationPage(page)

    # ======================================
    # LOGIN
    # ======================================
    login.open()
    login.login_as_super_admin()
    print(
        f"[URL AFTER LOGIN] {page.url}"
    )
    page.wait_for_load_state("networkidle", timeout=60000)
    print(f"[POST LOGIN ACTUAL URL] {page.url}")


    # ======================================
    # OPEN ONBOARDING MODAL
    # ======================================
    onboarding.open()
    print(
        f"[URL AFTER ONBOARDING OPEN] {page.url}"
    )
    print(page.url)

    page.screenshot(
        path="debug_before_modal.png",
        full_page=True
    )
    onboarding.open_employee_onboarding_modal()

    # ======================================
    # EMPLOYEE DETAILS
    # ======================================
    first_name = unique_first_name()
    last_name = unique_last_name()

    onboarding.enter_first_name(first_name)

    onboarding.enter_middle_name(employee_data["middle_name"])

    onboarding.enter_last_name(last_name)
    email = unique_email()


    onboarding.enter_email(email)

    actual_email = page.locator("#email").input_value()

    print(
        f"Generated Email = {email}"
    )

    print(
        f"UI Email Value = {actual_email}"
    )
    selected_job_offered = onboarding.select_dropdown(
        "Select job offered",
        option_text=employee_data["job_offered"]
    )

    # Department — actual trigger placeholder text is "Select function"
    # ("Select department" is only the first placeholder OPTION inside the list)
    selected_dept = onboarding.select_dropdown(
        "Select function",
        option_text=employee_data["department"]
    )

    dynamic_filled = onboarding.handle_dynamic_dropdowns_after_department()

    page.wait_for_timeout(3000)

    selected_job = onboarding.select_dropdown(
        "Select job title"
    )

    selected_hierarchy = onboarding.select_dropdown(
        "Select hierarchy level"
    )

    selected_manager = onboarding.select_dropdown(
        "Select reporting manager"
    )

    # Joining Date
    # onboarding.select_joining_date()

    # Joining Date (always today)
    select_today_joining_date(page)

    # Employment Type
    selected_emp_type = onboarding.select_dropdown(
        "Select type",
        option_text=employee_data["employee_type"]
    )

    # Company Entity
    selected_entity = onboarding.select_dropdown(
        "Select company entity",
        option_text=employee_data["company_entity"]
    )

    onboarding.fill_remaining_dropdowns()

    missing = onboarding.check_unfilled_required_fields()

    print(f"\nMissing Fields: {missing}")

    assert len(missing) == 0, (
        f"Required fields still empty: {missing}"
    )

    onboarding.click_next()
    # COMPENSATION
    # ======================================
    compensation.verify_compensation_tab_visible()

    compensation.select_salary_structure(
        option_text=employee_data["salary_structure"]
    )

    compensation.fill_all_visible_inputs()

    compensation.click_calculate()

    with page.expect_response(
            lambda response:
                "api/hr/offers/send" in response.url
                and response.status == 200
        ) as response_info:    

        compensation.click_send_onboarding_invite()
        compensation_log = (
            compensation.captured_data
        )
        print(
            "\n===== COMPENSATION LOG ====="
        )

        for k, v in compensation_log.items():
            print(k, "=", v)

        print(
            "Total Compensation Fields:",
            len(compensation_log)
        )

        response = response_info.value

        payload = response.json()

        invite_link = payload["data"]["invite_link"]
        candidate_page = page.context.new_page()

        response = candidate_page.goto(
            invite_link,
            wait_until="networkidle"
        )

        # Verify page opened successfully
        assert response is not None, "No response received from invite link"

        assert response.status == 200, (
            f"Invite link returned status {response.status}"
        )

        print("Candidate URL:", candidate_page.url)

        print("Candidate Title:", candidate_page.title())

        candidate_page.screenshot(
            path=os.path.join(
                RUN_FOLDER,
                "screenshots",
                f"after_accept_offer_{employee_data['test_case']}.png"
            ),
            full_page=True
        )

        print("Screenshot captured")

        candidate = CandidateOnboardingPage(
            candidate_page
        )

        candidate.continue_onboarding()

        candidate_page.wait_for_load_state(
            "networkidle"
        )

        print(
            "Offer Letter URL:",
            candidate_page.url
        )

        candidate.accept_offer()

        candidate_page.wait_for_load_state(
            "networkidle"
        )

        print(
            "After Accept URL:",
            candidate_page.url
        )

        candidate_page.screenshot(
        path=os.path.join(
            RUN_FOLDER,
            "screenshots",
            f"candidate_debug_{employee_data['test_case']}.png"
        ),
        full_page=True)

        candidate.verify_form_loaded()

        candidate_data = candidate.fill_all_tabs()

        validation_results = validate_all_tabs(
            candidate_page
        )

        print(
            "\nValidation Results:",
            validation_results
        )

        failed_tabs = {
            tab: errors
            for tab, errors
            in validation_results.items()
            if errors
        }

        assert not failed_tabs, (
            f"Validation failed: {failed_tabs}"
        )

        # ======================================
        # DYNAMIC ONBOARDING FORM VALIDATION
        # ======================================

        validation_results = validate_all_tabs(candidate_page)

        print("\n===== Dynamic Form Validation =====")

        for tab_name, missing_fields in validation_results.items():

            print(f"\nTab: {tab_name}")

            if missing_fields:
                for field in missing_fields:
                    print(f"Missing -> {field}")
            else:
                print("All required fields completed")


    # ======================================
    # LOG TO EXCEL (on success)
    # ======================================
    field_data = {

        # Employee Creation
        "first_name": first_name,
        "middle_name": employee_data["middle_name"],
        "last_name": last_name,
        "email": email,

        "job_offered": selected_job_offered,
        "hierarchy_level": selected_hierarchy,
        "department": selected_dept,
        "job_title": selected_job,
        "manager": selected_manager,

        "employment_type": selected_emp_type,
        "company_entity": selected_entity,
        "salary_structure": employee_data["salary_structure"],

        # Personal
        "gender": CANDIDATE_DATA["gender"],
        "dob": CANDIDATE_DATA["dob"],

        # Contact
        "candidate_email": CANDIDATE_DATA["email"],
        "phone": CANDIDATE_DATA["phone"],

        # Banking
        "account_holder_name": CANDIDATE_DATA["account_holder_name"],
        "bank_name": CANDIDATE_DATA["bank_name"],
        "branch": CANDIDATE_DATA["branch"],
        "account_number": CANDIDATE_DATA["account_number"],
        "ifsc": CANDIDATE_DATA["ifsc"],

        # Identity
        "aadhaar": CANDIDATE_DATA["aadhar"],
        "pan": CANDIDATE_DATA["pan"],

        # Address
        "address1": CANDIDATE_DATA["address1"],
        "address2": CANDIDATE_DATA["address2"],
        "city": CANDIDATE_DATA["city"],
        "pin": CANDIDATE_DATA["pin"],
        "state": CANDIDATE_DATA["state"],

        # Family
        "relation": CANDIDATE_DATA["relation"],
        "family_name": CANDIDATE_DATA["family_name"],

        # Education
        "college": CANDIDATE_DATA["college"],
        "level": CANDIDATE_DATA["level"],
        "course": CANDIDATE_DATA["course"],
        "specialization": CANDIDATE_DATA["specialization"],
        "passing_year": CANDIDATE_DATA["passing_year"],

        # Uploads
        "profile_image_uploaded": "YES",
        "documents_uploaded": "YES",

        # Validation
        "validation_status": "PASSED",
        "missing_fields": "None",

        "send_onboarding_invite": "clicked"
    }
    field_data.update(candidate_data)
    field_data.update(
        compensation_log
    )
    
    write_field_log(
        test_name=f"smoke_{employee_data['test_case']}",
        field_data=field_data,
        section="Onboarding"
    )

    page.wait_for_timeout(2000)
