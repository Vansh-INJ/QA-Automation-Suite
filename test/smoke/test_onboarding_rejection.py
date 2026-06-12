import pytest
from utils.test_context import TEST_CONTEXT
from pages.login_page import LoginPage
from pages.onboarding_page import OnboardingPage
from pages.onboarding_approval_page import (
    OnboardingApprovalPage
)

def test_employee_onboarding_rejection(page):

    login = LoginPage(page)

    onboarding = OnboardingPage(page)

    approval = OnboardingApprovalPage(page)

    # =====================================
    # LOGIN
    # =====================================

    login.open()

    login.login_as_super_admin()
   

    # =====================================
    # OPEN ONBOARDING LISTING
    # =====================================

    onboarding.open()

    # =====================================
    # OPEN TODAY'S CANDIDATE
    # =====================================

    approval.filter_today_candidates()

    # found = approval.find_reject_candidate()

    # =====================================
    # REJECT EMPLOYEE
    # =====================================

    found = approval.find_candidate_with_action(
        "Reject"
    )

    assert found, (
        "No candidate found with Reject button"
    )

    reject_response = (
        approval.reject_employee()
    )

    TEST_CONTEXT["action"] = "Rejection"

    TEST_CONTEXT["api_status"] = 200

    TEST_CONTEXT["api_message"] = (
        reject_response["status"]
    )

    TEST_CONTEXT["api_response"] = str(
        reject_response
    )

    TEST_CONTEXT["action"] = "Rejection"

    TEST_CONTEXT["api_status"] = 200

    TEST_CONTEXT["api_message"] = (
        reject_response["status"]
    )

    TEST_CONTEXT["api_response"] = str(
        reject_response
    )


    print(
        f"\nReject Response: {reject_response}"
    )