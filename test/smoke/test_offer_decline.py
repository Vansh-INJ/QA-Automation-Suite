import pytest

from utils.test_context import TEST_CONTEXT

from pages.login_page import LoginPage
from pages.onboarding_page import OnboardingPage
from pages.compensation_page import CompensationPage

from pages.candidate_onboarding_page import (
    CandidateOnboardingPage
)

from utils.test_data_generator import (
    unique_email,
    unique_first_name,
    unique_last_name
)
from datetime import datetime



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

    page.locator(
        "#joining_date"
    ).click()

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


from test_data.employee_data import (
    OFFER_DECLINE_DATA
)


def test_offer_decline(page,):
    
    employee_data = OFFER_DECLINE_DATA
    login = LoginPage(page)

    onboarding = OnboardingPage(page)

    compensation = CompensationPage(page)

    # =====================================
    # LOGIN
    # =====================================

    login.open()

    login.login_as_super_admin()

    page.wait_for_load_state(
        "networkidle",
        timeout=60000
    )

    # =====================================
    # OPEN ONBOARDING
    # =====================================

    onboarding.open()

    onboarding.open_employee_onboarding_modal()

    # =====================================
    # EMPLOYEE DETAILS
    # =====================================

    first_name = unique_first_name()

    last_name = unique_last_name()

    email = unique_email()

    onboarding.enter_first_name(
        first_name
    )

    onboarding.enter_middle_name(
        employee_data["middle_name"]
    )

    onboarding.enter_last_name(
        last_name
    )

    onboarding.enter_email(
        email
    )

    onboarding.select_dropdown(
        "Select job offered",
        option_text=employee_data[
            "job_offered"
        ]
    )

    onboarding.select_dropdown(
        "Select function",
        option_text=employee_data[
            "department"
        ]
    )

    onboarding.handle_dynamic_dropdowns_after_department()

    page.wait_for_timeout(3000)

    onboarding.select_dropdown(
        "Select job title"
    )

    onboarding.select_dropdown(
        "Select hierarchy level"
    )

    onboarding.select_dropdown(
        "Select reporting manager"
    )

    select_today_joining_date(
        page
    )

    onboarding.select_dropdown(
        "Select type",
        option_text=employee_data[
            "employee_type"
        ]
    )

    onboarding.select_dropdown(
        "Select company entity",
        option_text=employee_data[
            "company_entity"
        ]
    )

    onboarding.fill_remaining_dropdowns()

    onboarding.click_next()

    # =====================================
    # COMPENSATION
    # =====================================

    compensation.verify_compensation_tab_visible()

    compensation.select_salary_structure(
        option_text=employee_data[
            "salary_structure"
        ]
    )

    compensation.fill_all_visible_inputs()

    compensation.click_calculate()

    # =====================================
    # SEND INVITE
    # =====================================

    with page.expect_response(
        lambda response:
        "api/hr/offers/send"
        in response.url
        and response.status == 200
    ) as response_info:

        compensation.click_send_onboarding_invite()

    response = response_info.value

    payload = response.json()

    invite_link = (
        payload["data"]["invite_link"]
    )

    print(
        f"\nInvite Link: {invite_link}"
    )

    # =====================================
    # OPEN CANDIDATE INVITE
    # =====================================

    candidate_page = (
        page.context.new_page()
    )

    invite_response = (
        candidate_page.goto(
            invite_link,
            wait_until="networkidle"
        )
    )

    assert (
        invite_response is not None
    )

    assert (
        invite_response.status == 200
    )

    candidate = (
        CandidateOnboardingPage(
            candidate_page
        )
    )

    candidate.continue_onboarding()

    candidate_page.wait_for_load_state(
        "networkidle"
    )

    print(
        f"Offer Letter URL: "
        f"{candidate_page.url}"
    )

    # =====================================
    # DECLINE OFFER
    # =====================================

    decline_response = (
        candidate.decline_offer()
    )

    print(
        f"\nDecline Response: "
        f"{decline_response}"
    )

    # =====================================
    # REPORTING
    # =====================================

    TEST_CONTEXT["candidate_name"] = (
        f"{first_name} {last_name}"
    )

    TEST_CONTEXT["candidate_email"] = (
        email
    )

    TEST_CONTEXT["action"] = (
        "Decline Offer"
    )

    TEST_CONTEXT["api_status"] = 200

    TEST_CONTEXT["api_message"] = (
        decline_response["data"][
            "message"
        ]
    )

    TEST_CONTEXT["api_response"] = str(
        decline_response
    )

    # =====================================
    # VALIDATION
    # =====================================

    assert (
        decline_response["status"]
        == "success"
    )

    assert (
        decline_response["data"][
            "message"
        ]
        == "Offer declined"
    )

    print(
        "\n[SUCCESS] Offer declined successfully"
    )

    candidate_page.close()