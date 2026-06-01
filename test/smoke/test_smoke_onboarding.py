import pytest
from pages.login_page import LoginPage
from pages.onboarding_page import OnboardingPage
from pages.compensation_page import CompensationPage
from test_data.employee_data import EMPLOYEE_PROFILES
from utils.helpers import write_field_log
from utils.test_data_generator import (
    unique_email,
    unique_first_name,
    unique_last_name
)


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

    # ======================================
    # OPEN ONBOARDING MODAL
    # ======================================
    onboarding.open()
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
    onboarding.enter_job_offered(employee_data["job_offered"])

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

    selected_manager = onboarding.select_dropdown(
        "Select reporting manager"
    )

    # Joining Date
    onboarding.select_joining_date()

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

    compensation.click_send_onboarding_invite()

    # ======================================
    # LOG TO EXCEL (on success)
    # ======================================
    field_data = {
        "first_name": first_name,
        "middle_name": employee_data["middle_name"],
        "last_name": last_name,
        "email": email,
        "job_offered": employee_data["job_offered"],
        "department": selected_dept,
        "job_title": selected_job,
        "manager": selected_manager,
        "employment_type": selected_emp_type,
        "company_entity": selected_entity,
        "salary_structure": employee_data["salary_structure"],
        "send_onboarding_invite": "clicked",
    }
    field_data.update({f"dynamic_{k}": v for k, v in dynamic_filled.items()})

    write_field_log(
        test_name=f"smoke_{employee_data['test_case']}",
        field_data=field_data,
        section="Onboarding"
    )

    page.wait_for_timeout(2000)
