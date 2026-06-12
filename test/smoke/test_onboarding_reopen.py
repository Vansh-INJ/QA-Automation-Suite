from itertools import count
from utils.run_manager import get_run_folder
import pytest
from utils.test_context import TEST_CONTEXT
from pages.login_page import LoginPage
from pages.onboarding_page import OnboardingPage
from pages.onboarding_approval_page import (
    OnboardingApprovalPage
)
from pages.candidate_onboarding_page import (
    CandidateOnboardingPage
)

from utils.dynamic_form_validator import (
    validate_all_tabs
)


def test_employee_onboarding_reopen(page):

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
    approval.filter_today_candidates()

    approval.show_100_candidates()

    

    count = approval.get_today_candidate_count()

    assert count > 0, (
        "No candidates found for today's date"
    )

    print(
        f"[TODAY CANDIDATES FOUND] {count}"
    )
    found = approval.find_candidate_with_action(
        "Reopen Request"
    )

    assert found, (
        "No candidate found with Reopen Request button"
    )

    reopen_response = (
        approval.reopen_employee()
    )

    TEST_CONTEXT["action"] = "Reopen"

    TEST_CONTEXT["api_status"] = 200

    TEST_CONTEXT["api_message"] = (
        reopen_response["status"]
    )

    TEST_CONTEXT["api_response"] = str(
        reopen_response
    )

    TEST_CONTEXT["action"] = "Reopen"

    TEST_CONTEXT["api_status"] = 200

    TEST_CONTEXT["api_message"] = (
        reopen_response["status"]
    )

    TEST_CONTEXT["api_response"] = str(
        reopen_response
    )


    invite_link = (
        reopen_response["data"]["invite_link"]
    )


    # =====================================
    # OPEN REOPEN INVITE
    # =====================================

    candidate_page = (
        page.context.new_page()
    )

    response = candidate_page.goto(
        invite_link,
        wait_until="networkidle"
    )

    assert response is not None

    assert response.status == 200

    # REOPENED CANDIDATE FORM

    candidate = CandidateOnboardingPage(
        candidate_page
    )

    candidate.verify_form_loaded()

    # OPTIONAL REVISION

    candidate.revise_and_submit_onboarding()

    # VALIDATION

    validation_results = (
        validate_all_tabs(
            candidate_page
        )
    )

    print(
        "\n===== REOPEN VALIDATION ====="
    )

    for tab_name, missing_fields in validation_results.items():

        print(
            f"\nTab: {tab_name}"
        )

        if missing_fields:

            for field in missing_fields:

                print(
                    f"Missing -> {field}"
                )

        else:

            print(
                "All required fields completed"
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

    candidate_page.close()

    print(
        "\n[SUCCESS] Reopened onboarding submitted successfully"
    )