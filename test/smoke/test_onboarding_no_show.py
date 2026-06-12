from pages.login_page import LoginPage
from pages.onboarding_approval_page import OnboardingApprovalPage
from pages.onboarding_page import OnboardingPage
from utils.test_context import TEST_CONTEXT

def test_onboarding_no_show(page):

    login = LoginPage(page)

    onboarding = OnboardingPage(page)

    approval = OnboardingApprovalPage(page)

    # LOGIN

    login.open()

    login.login_as_super_admin()

    # OPEN ONBOARDING PAGE

    onboarding.open()

    approval.filter_today_candidates()

    approval.show_100_candidates()

    count = approval.get_today_candidate_count()

    assert count > 0

    found = approval.find_candidate_with_action(
        "Approve"
    )

    assert found

    approval.approve_employee()

    no_show_response = (
        approval.mark_no_show()
    )

    TEST_CONTEXT["action"] = "No Show"

    TEST_CONTEXT["api_status"] = 200

    TEST_CONTEXT["api_message"] = (
        no_show_response["status"]
    )

    TEST_CONTEXT["api_response"] = str(
        no_show_response
    )


    print(
        "\n[SUCCESS] Candidate marked as No Show"
    )