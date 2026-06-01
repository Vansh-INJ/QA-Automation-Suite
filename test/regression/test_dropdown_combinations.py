import pytest
from allpairspy import AllPairs
from pages.login_page import LoginPage
from pages.onboarding_page import OnboardingPage
from pages.compensation_page import CompensationPage
from test_data.employee_data import EMPLOYEE_PROFILES
from utils.helpers import write_field_log

from utils.test_data_generator import (
    unique_email,
    unique_first_name,
    unique_last_name,
    unique_job_offered
)

# ============================================================
# COMBINATORIAL PARAMETERS
# All valid dropdown options from the onboarding form.
# allpairspy generates the optimal pairwise subset automatically.
# ============================================================
parameters = [
    ['ASD', 'Information Technology', 'Business Development'],   # Department
    ['Software Developer Intern', 'Software Developer'],          # Job Title
    ['Amit Kumar Sharma (EMP001)', 'Neha Ramesh Verma (EMP002)', 'Rahul S. Mehta (EMP003)'],  # Manager
    ['Full Time', 'Part Time', 'Contract', 'Intern'],             # Employment Type
    ['INJ Partners', 'INJ Technologies', 'Lead X Prospects'],     # Company Entity
    ['Noida Salary Structure Main', 'Noida Salary Structure WO Bonus'],  # Salary Structure
]


def generate_pairs():
    return list(AllPairs(parameters))


@pytest.mark.parametrize(
    "dept, job_title, manager, emp_type, entity, salary_struct",
    generate_pairs()
)
def test_combinatorial_dropdowns(page, dept, job_title, manager, emp_type, entity, salary_struct):

    # Use the first valid employee profile as the base payload
    employee_data = EMPLOYEE_PROFILES[0]

    login = LoginPage(page)
    onboarding = OnboardingPage(page)
    compensation = CompensationPage(page)

    # =========================================================
    # LOGIN
    # =========================================================
    login.open()
    login.login_as_super_admin()

    # =========================================================
    # OPEN ONBOARDING MODAL
    # =========================================================
    onboarding.open()
    onboarding.open_employee_onboarding_modal()

    # =========================================================
    # STATIC EMPLOYEE DETAILS
    # =========================================================
    first_name = unique_first_name()
    last_name = unique_last_name()
    email = unique_email()

    onboarding.enter_first_name(first_name)
    onboarding.enter_middle_name(employee_data["middle_name"])
    onboarding.enter_last_name(last_name)
    onboarding.enter_email(email)

    job_offered = unique_job_offered()

    onboarding.enter_job_offered(
        job_offered
    )

    print(
        f"[REGRESSION] Job Offered = "
        f"{employee_data['job_offered']}"
    )

    # =========================================================
    # DYNAMIC DROPDOWNS (pairwise combinatorial values)
    # NOTE: The actual trigger placeholder on the Department field is "Select function".
    # "Select department" only appears as the first option INSIDE the open dropdown list.
    # =========================================================
    selected_dept = onboarding.select_dropdown(
        "Select function",
        option_text=dept
    )
    dynamic_filled = onboarding.handle_dynamic_dropdowns_after_department()

    page.wait_for_timeout(3000)

    # After selecting department, check for any dynamically rendered
    # dropdowns (e.g., Sub Department for "Information Technology")
    # dynamic_filled = onboarding.handle_dynamic_dropdowns_after_department()

    selected_job = onboarding.select_dropdown("Select job title", option_text=job_title)
    selected_manager = onboarding.select_dropdown("Select reporting manager", option_text=manager)

    onboarding.select_joining_date()

    selected_emp_type = onboarding.select_dropdown("Select type", option_text=emp_type)
    selected_entity = onboarding.select_dropdown(
        "Select company entity",
        option_text=entity
    )

    page.wait_for_timeout(3000)

    selected_location = onboarding.select_dropdown(
        "Select location"
    )

    onboarding.fill_remaining_dropdowns()

    missing = onboarding.check_unfilled_required_fields()

    assert len(missing) == 0

    job_value = page.locator("#job_offered").input_value()

    print(
        f"[DEBUG] Job Offered Field = "
        f"{job_value}"
    )

    onboarding.click_next()

    # =========================================================
    # COMPENSATION
    # =========================================================
    compensation.verify_compensation_tab_visible()
    compensation.select_salary_structure(option_text=salary_struct)

    # Fill all visible fields (salary inputs, dynamic fields, comboboxes)
    compensation.fill_all_visible_inputs()

    compensation.click_calculate()
    compensation.click_send_onboarding_invite()

    # =========================================================
    # LOG FIELD DATA TO EXCEL (on success)
    # =========================================================
    field_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,       
        "middle_name": employee_data["middle_name"],        
        "job_offered": job_offered,
        "department": selected_dept,
        "job_title": selected_job,
        "manager": selected_manager,
        "employment_type": selected_emp_type,
        "company_entity": selected_entity,
        "salary_structure": salary_struct,
        "send_onboarding_invite": "clicked",
    }
    # Merge any dynamic fields that were auto-filled
    pass

    write_field_log(
        test_name=f"test_combinatorial[{dept}-{job_title}-{emp_type}]",
        field_data=field_data,
        section="Onboarding"
    )

    page.wait_for_timeout(1000)
