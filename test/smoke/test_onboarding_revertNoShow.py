from pages.login_page import LoginPage
from pages.onboarding_page import OnboardingPage
from pages.onboarding_approval_page import (
    OnboardingApprovalPage
)

from utils.test_context import (
    TEST_CONTEXT
)


def test_onboarding_revert_no_show(page):

    login = LoginPage(page)

    onboarding = OnboardingPage(page)

    approval = OnboardingApprovalPage(page)

    # =====================================
    # LOGIN
    # =====================================

    login.open()

    login.login_as_super_admin()

    # =====================================
    # OPEN ONBOARDING PAGE
    # =====================================

    onboarding.open()

    approval.show_100_candidates()

    count = approval.get_today_candidate_count()

    assert count > 0

    print(
        f"[TODAY CANDIDATES] {count}"
    )

    # =====================================
    # OPEN NO SHOW TAB
    # =====================================

    approval.open_no_show_tab()

    # =====================================
    # FIND REVERT NO SHOW CANDIDATE
    # =====================================

    found = approval.find_candidate_with_action(
        "Revert No Show"
    )

    assert found, (
        "No candidate found with "
        "'Revert No Show' button"
    )

    # =====================================
    # REVERT NO SHOW
    # =====================================

    revert_response = (
        approval.revert_no_show()
    )

    print(
        "\n===== REVERT NO SHOW RESPONSE ====="
    )

    print(
        revert_response
    )

    # =====================================
    # REPORTING
    # =====================================

    TEST_CONTEXT["action"] = (
        "Revert No Show"
    )

    TEST_CONTEXT["api_status"] = 200

    TEST_CONTEXT["api_message"] = (
        revert_response["data"][
            "message"
        ]
    )

    TEST_CONTEXT["api_response"] = str(
        revert_response
    )

    # =====================================
    # VALIDATION
    # =====================================

    assert (
        revert_response["status"]
        == "success"
    )

    assert (
        revert_response["data"][
            "success"
        ]
        is True
    )

    assert (
        revert_response["data"][
            "message" 
        ]
        ==
        "No-show reverted and joining date updated successfully"
    )

    print(
        "\n[SUCCESS] No Show reverted successfully"
    )