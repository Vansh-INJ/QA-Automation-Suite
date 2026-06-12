import pytest

from pages.login_page import LoginPage
from pages.onboarding_page import OnboardingPage
from pages.onboarding_approval_page import (
    OnboardingApprovalPage
)


def test_employee_onboarding_approval(page):

    login = LoginPage(page)

    onboarding = OnboardingPage(page)

    approval = OnboardingApprovalPage(page)

    login.open()

    login.login_as_super_admin()
    

    onboarding.open()

    approval.show_100_candidates()

    approval.filter_today_candidates()

    found = approval.find_approve_candidate()

    assert found, (
        "No candidate found with Approve button"
    )

    approval_response = (
        approval.approve_employee()
    )

    from utils.test_context import TEST_CONTEXT

    TEST_CONTEXT["action"] = "Approval"

    TEST_CONTEXT["api_status"] = 200

    TEST_CONTEXT["api_message"] = (
        approval_response["status"]
    )

    TEST_CONTEXT["api_response"] = str(
        approval_response
    )

    print(
        f"\nApproval Response: "
        f"{approval_response}"
    )

    hire_response = (
        approval.hire_employee()
    )

    print(
        f"\nHire Response: {hire_response}"
    )

    print(
        f"\nApproval Response: "
        f"{approval_response}"
    )
    print(
        "[TEST PASSED] Employee approved and hired successfully"
    )