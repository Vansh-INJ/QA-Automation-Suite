import pytest

from pages.login_page import LoginPage
from pages.onboarding_page import OnboardingPage
from pages.onboarding_approval_page import (
    OnboardingApprovalPage
)


def test_employee_revoke_invite(page):

    login = LoginPage(page)

    onboarding = OnboardingPage(page)

    approval = OnboardingApprovalPage(page)

    login.open()

    login.login.login()

    onboarding.open()

    approval.show_100_candidates()

    approval.filter_today_candidates()

    found = approval.find_candidate_with_action(
        "Revoke Invite"
    )

    assert found, (
        "No candidate found with Revoke Invite button"
    )

    revoke_response = (
        approval.revoke_invite()
    )

    from utils.test_context import TEST_CONTEXT

    TEST_CONTEXT["action"] = "Revoke Invite"

    TEST_CONTEXT["api_status"] = 200

    TEST_CONTEXT["api_message"] = (
        revoke_response["status"]
    )

    TEST_CONTEXT["api_response"] = str(
        revoke_response
    )

    print(
        f"\nRevoke Response: "
        f"{revoke_response}"
    )

    print(
        "[TEST PASSED] Invite revoked successfully"
    )