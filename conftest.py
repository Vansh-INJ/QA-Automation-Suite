import json
import os
from datetime import datetime

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from utils.api_context import API_CONTEXT
from utils.api_summary import print_api_summary
from utils.helpers import (
    create_excel_report,
    write_result,
)
from utils.logger import logger
from utils.run_manager import get_run_folder
from utils.test_context import TEST_CONTEXT

from api_framework.auth.token_manager import TokenManager
from api_framework.clients.offer_client import OfferClient
from api_framework.clients.onboarding_client import OnboardingClient
from api_framework.config.settings import Settings


load_dotenv()


# ===========================================================================
# API CLIENT FIXTURES
# ===========================================================================

@pytest.fixture(scope="function")
def authenticated_offer_client():
    """
    Create a fresh authenticated OfferClient for each test.

    A fresh TokenManager header is used for every test to avoid problems
    caused by token expiry during long test runs.
    """
    return OfferClient(
        base_url=Settings.BASE_URL,
        headers=TokenManager.get_headers(),
    )


@pytest.fixture(scope="function")
def onboarding_client():
    """
    Create an onboarding client for each test.
    """
    return OnboardingClient(
        base_url=Settings.BASE_URL,
    )


# ===========================================================================
# RUN FOLDER
# ===========================================================================

@pytest.fixture(scope="session")
def run_folder():
    """
    Resolve the run folder and initialize report directories once
    per pytest session.
    """
    folder = get_run_folder()

    create_excel_report()

    os.makedirs(
        os.path.join(
            folder,
            "screenshots",
        ),
        exist_ok=True,
    )

    os.makedirs(
        os.path.join(
            folder,
            "api_failures",
        ),
        exist_ok=True,
    )

    return folder


# ===========================================================================
# RESULT REPORTING
# ===========================================================================

@pytest.fixture(autouse=True)
def report_result(request, run_folder):
    """
    Generic test result reporting.

    API tests are excluded from the generic report because API tests
    have their own API execution/reporting mechanism.

    UI tests continue to use this fixture for Excel reporting.
    """
    test_path = str(
        request.node.fspath
    ).replace("\\", "/")

    # -----------------------------------------------------------------------
    # API TESTS
    # -----------------------------------------------------------------------
    if "/test/api/" in test_path:
        yield
        return

    test_name = request.node.name

    logger.info(
        f"========== STARTING TEST: {test_name} =========="
    )

    yield

    # -----------------------------------------------------------------------
    # TEST RESULT
    # -----------------------------------------------------------------------
    rep_call = getattr(
        request.node,
        "rep_call",
        None,
    )

    failed = (
        rep_call is not None
        and rep_call.failed
    )

    if failed:
        logger.error(
            f"TEST FAILED: {test_name}"
        )

        error = str(
            rep_call.longrepr
        )

    else:
        logger.info(
            f"TEST PASSED: {test_name}"
        )

        error = ""

    # -----------------------------------------------------------------------
    # EXCEL-SAFE VALUE HELPER
    # -----------------------------------------------------------------------
    def excel_safe(value):
        if isinstance(
            value,
            (dict, list),
        ):
            try:
                return json.dumps(
                    value,
                    indent=4,
                )
            except Exception:
                return str(value)

        return value

    # -----------------------------------------------------------------------
    # DEFAULT API REPORT VALUES
    # -----------------------------------------------------------------------
    method = ""
    endpoint = ""

    api_status = TEST_CONTEXT.get(
        "api_status",
        "",
    )

    duration = ""

    request_headers = ""

    request_payload = ""

    response_body = TEST_CONTEXT.get(
        "api_response",
        "",
    )

    # -----------------------------------------------------------------------
    # API CONTEXT
    # -----------------------------------------------------------------------
    if API_CONTEXT:
        response_obj = API_CONTEXT.get(
            "response"
        )

        try:
            response_body = (
                response_obj.json()
                if response_obj
                else response_body
            )

        except Exception:
            response_body = (
                response_obj.text
                if response_obj
                else response_body
            )

        method = API_CONTEXT.get(
            "method",
            "",
        )

        endpoint = API_CONTEXT.get(
            "endpoint",
            "",
        )

        api_status = getattr(
            response_obj,
            "status_code",
            api_status,
        )

        duration = API_CONTEXT.get(
            "duration",
            "",
        )

        request_headers = API_CONTEXT.get(
            "headers",
            "",
        )

        request_payload = API_CONTEXT.get(
            "payload",
            "",
        )

    # -----------------------------------------------------------------------
    # SLA
    # -----------------------------------------------------------------------
    sla = TEST_CONTEXT.get(
        "sla",
        "",
    )

    sla_status = ""

    if sla != "" and duration != "":
        try:
            sla_status = (
                "PASS"
                if float(duration) <= float(sla)
                else "FAIL"
            )
        except (
            TypeError,
            ValueError,
        ):
            sla_status = ""

    # -----------------------------------------------------------------------
    # FINAL RESULT ROW
    # -----------------------------------------------------------------------
    write_result(
        test_name=test_name,
        status="FAILED" if failed else "PASSED",
        action=excel_safe(
            TEST_CONTEXT.get(
                "action",
                "",
            )
        ),
        candidate_name=excel_safe(
            TEST_CONTEXT.get(
                "candidate_name",
                "",
            )
        ),
        candidate_email=excel_safe(
            TEST_CONTEXT.get(
                "candidate_email",
                "",
            )
        ),
        api_message=excel_safe(
            TEST_CONTEXT.get(
                "api_message",
                "",
            )
        ),
        run_id=os.path.basename(
            run_folder
        ),
        environment="SIT",
        username=Settings.API_USERNAME,
        method=method,
        endpoint=endpoint,
        api_status=api_status,
        expected_status=TEST_CONTEXT.get(
            "expected_status",
            "",
        ),
        duration=duration,
        sla=sla,
        sla_status=sla_status,
        request_headers=excel_safe(
            request_headers
        ),
        request_payload=excel_safe(
            request_payload
        ),
        response_body=excel_safe(
            response_body
        ),
        error=error,
        screenshot=TEST_CONTEXT.get(
            "screenshot",
            "",
        ),
    )

    logger.info(
        f"========== FINISHED TEST: {test_name} =========="
    )


# ===========================================================================
# PLAYWRIGHT PAGE FIXTURE
# ===========================================================================

@pytest.fixture(scope="function")
def page(request, run_folder):
    """
    Playwright browser fixture.

    Responsible only for:
        - browser lifecycle
        - API failure listener
        - autocomplete disabling
        - screenshot capture on failure
    """
    screenshot_dir = os.path.join(
        run_folder,
        "screenshots",
    )

    api_failure_dir = os.path.join(
        run_folder,
        "api_failures",
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            slow_mo=100,
        )

        logger.info(
            "Chromium browser launched"
        )

        context = browser.new_context()

        page = context.new_page()

        logger.info(
            "New browser page created"
        )

        # -------------------------------------------------------------------
        # API FAILURE LISTENER
        # -------------------------------------------------------------------
        def capture_failed_response(response):

            if "upload" in response.url.lower():
                print(
                    "UPLOAD API INTERCEPTED: "
                    f"{response.request.method} "
                    f"{response.url}"
                )

                try:
                    print(
                        "UPLOAD RESPONSE:",
                        response.text(),
                    )
                except Exception:
                    pass

            if response.status >= 400:

                logger.error(
                    "API FAILURE | "
                    f"STATUS: {response.status} | "
                    f"URL: {response.url}"
                )

                try:
                    body = response.text()

                    timestamp = datetime.now().strftime(
                        "%Y%m%d_%H%M%S"
                    )

                    file_path = os.path.join(
                        api_failure_dir,
                        (
                            f"failure_"
                            f"{response.status}_"
                            f"{timestamp}.txt"
                        ),
                    )

                    with open(
                        file_path,
                        "w",
                        encoding="utf-8",
                    ) as f:
                        f.write(
                            f"STATUS: {response.status}\n"
                        )

                        f.write(
                            f"URL: {response.url}\n\n"
                        )

                        f.write(body)

                    logger.info(
                        "API failure log saved: "
                        f"{file_path}"
                    )

                except Exception as e:
                    logger.exception(
                        "Failed to capture API "
                        f"response body: {e}"
                    )

        page.on(
            "response",
            capture_failed_response,
        )

        logger.info(
            "Response listener attached"
        )

        # -------------------------------------------------------------------
        # DISABLE AUTOCOMPLETE
        # -------------------------------------------------------------------
        page.add_init_script(
            """
            window.addEventListener('DOMContentLoaded', () => {
                document.querySelectorAll('input').forEach(el => {
                    el.setAttribute('autocomplete', 'off');
                    el.setAttribute('autocorrect', 'off');
                    el.setAttribute('autocapitalize', 'off');
                    el.setAttribute('spellcheck', 'false');
                });
            });
            """
        )

        # -------------------------------------------------------------------
        # TEST EXECUTION
        # -------------------------------------------------------------------
        yield page

        # -------------------------------------------------------------------
        # SCREENSHOT ON FAILURE
        # -------------------------------------------------------------------
        test_name = request.node.name

        rep_call = getattr(
            request.node,
            "rep_call",
            None,
        )

        if (
            rep_call is not None
            and rep_call.failed
        ):
            try:
                screenshot_path = os.path.join(
                    screenshot_dir,
                    f"{test_name}.png",
                )

                page.screenshot(
                    path=screenshot_path,
                    full_page=True,
                )

                logger.info(
                    "Failure screenshot saved: "
                    f"{screenshot_path}"
                )

                TEST_CONTEXT["screenshot"] = (
                    screenshot_path
                )

            except Exception as e:

                logger.exception(
                    "Failed to capture screenshot: "
                    f"{e}"
                )

                TEST_CONTEXT["screenshot"] = ""

        # -------------------------------------------------------------------
        # CLOSE BROWSER
        # -------------------------------------------------------------------
        context.close()

        logger.info(
            f"Closing browser for: {test_name}"
        )

        browser.close()


# ===========================================================================
# PYTEST REPORT HOOK
# ===========================================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Store pytest reports on the test item so fixtures can inspect
    setup/call/teardown results.
    """
    outcome = yield

    rep = outcome.get_result()

    setattr(
        item,
        "rep_" + rep.when,
        rep,
    )


# ===========================================================================
# PYTEST SESSION FINISH
# ===========================================================================

def pytest_sessionfinish(session, exitstatus):
    """
    Print API execution summary after the complete test session.
    """
    try:
        print_api_summary()

    except Exception as e:
        print(
            "\n[SUMMARY ERROR]",
            e,
        )