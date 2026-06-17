import os
from datetime import datetime
from utils.logger import logger
from utils.run_manager import get_run_folder
import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from utils.test_context import TEST_CONTEXT
from utils.helpers import (
    create_excel_report,
    create_field_log,
    write_result,
)

import json

from utils.api_context import (
    API_CONTEXT
)

from utils.helpers import (
    write_api_log
)

from utils.api_summary import (
    print_api_summary
)

from api_framework.auth.token_manager import (
    TokenManager
)
from api_framework.clients.offer_client import (
    OfferClient
)


load_dotenv()


@pytest.fixture
def authenticated_offer_client():

    token = (
        TokenManager.get_token()        
    )
    print("\nTOKEN FETCHED")

    headers = {
        "Authorization":
            f"Bearer {token}",
        "Content-Type":
            "application/json"
    }

    return OfferClient(
        base_url=os.getenv(
            "BASE_URL"
        ),
        headers=headers
    )

import pytest

from api_framework.auth.token_manager import (
    TokenManager
)

from api_framework.clients.offer_client import (
    OfferClient
)

from api_framework.config.settings import (
    Settings
)


@pytest.fixture(scope="session")
def authenticated_offer_client():

    return OfferClient(
        base_url=
        Settings.BASE_URL,

        headers=
        TokenManager.get_headers()
    )


@pytest.fixture(scope="function")
def page(request):
    logger.info(
        f"========== STARTING TEST: {request.node.name} =========="
    )

    create_excel_report()
    RUN_FOLDER = get_run_folder()

    SCREENSHOT_DIR = os.path.join(
        RUN_FOLDER,
        "screenshots"
    )

    API_FAILURE_DIR = os.path.join(
        RUN_FOLDER,
        "api_failures"
    )

    os.makedirs(
        API_FAILURE_DIR,
        exist_ok=True
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            slow_mo=100
        )

        logger.info(
            "Chromium browser launched"
        )

        context = browser.new_context()
        page = context.new_page()

        logger.info(
            "New browser page created"
        )

        # ======================================
        # API FAILURE LISTENER
        # ======================================

        def capture_failed_response(response):

            if response.status >= 400:

                logger.error(
                    f"API FAILURE | "
                    f"STATUS: {response.status} | "
                    f"URL: {response.url}"
                )

                try:

                    body = response.text()

                    timestamp = datetime.now().strftime(
                        "%Y%m%d_%H%M%S"
                    )

                    file_path = os.path.join(
                        API_FAILURE_DIR,
                        f"failure_{response.status}_{timestamp}.txt"
                    )

                    with open(
                        file_path,
                        "w",
                        encoding="utf-8"
                    ) as f:

                        f.write(
                            f"STATUS: {response.status}\n"
                        )

                        f.write(
                            f"URL: {response.url}\n\n"
                        )

                        f.write(body)

                    logger.info(
                        f"API failure log saved: {file_path}"
                    )

                except Exception as e:

                    logger.exception(
                        f"Failed to capture API response body: {e}"
                    )

        page.on(
            "response",
            capture_failed_response
        )

        logger.info(
            "Response listener attached"
        )

        # ======================================
        # DISABLE AUTOCOMPLETE
        # ======================================

        page.add_init_script("""
            window.addEventListener('DOMContentLoaded', () => {

                document.querySelectorAll('input').forEach(el => {

                    el.setAttribute('autocomplete', 'off');
                    el.setAttribute('autocorrect', 'off');
                    el.setAttribute('autocapitalize', 'off');
                    el.setAttribute('spellcheck', 'false');

                });

            });
        """)

        yield page

        test_name = request.node.name

        # ======================================
        # FAILED TEST
        # ======================================

        if request.node.rep_call.failed:

            try:

                screenshot_path = os.path.join(
                    SCREENSHOT_DIR,
                    f"{test_name}.png"
                )

                logger.error(
                    f"TEST FAILED: {request.node.name}"
                )

                page.screenshot(
                    path=screenshot_path,
                    full_page=True
                )

                logger.info(
                    f"Failure screenshot saved: {screenshot_path}"
                )

            except Exception as e:

                logger.exception(
                    f"Failed to capture screenshot: {e}"
                )

                screenshot_path = ""

            write_result(
            test_name=test_name,
            status="FAILED",

            action=TEST_CONTEXT.get(
                "action",
                ""
            ),
            candidate_name=TEST_CONTEXT.get(
                "candidate_name",
                ""
            ),

            candidate_email=TEST_CONTEXT.get(
                "candidate_email",
                ""
            ),

            api_status=TEST_CONTEXT.get(
                "api_status",
                ""
            ),

            api_message=TEST_CONTEXT.get(
                "api_message",
                ""
            ),

            api_response=TEST_CONTEXT.get(
                "api_response",
                ""
            ),

            error=str(
                request.node.rep_call.longrepr
            ),

            screenshot=screenshot_path
        )

        # ======================================
        # PASSED TEST
        # ======================================

        

        else:  

            if request.node.rep_call.passed:
                logger.info(
                    f"TEST PASSED: {request.node.name}"
                )         

            write_result(
                test_name=test_name,
                status="PASSED",

                action=TEST_CONTEXT.get(
                    "action",
                    ""
                ),

                candidate_name=TEST_CONTEXT.get(
                    "candidate_name",
                    ""
                ),

                candidate_email=TEST_CONTEXT.get(
                    "candidate_email",
                    ""
                ),

                api_status=TEST_CONTEXT.get(
                    "api_status",
                    ""
                ),

                api_message=TEST_CONTEXT.get(
                    "api_message",
                    ""
                ),

                api_response=TEST_CONTEXT.get(
                    "api_response",
                    ""
                ),
            )

        context.close()

        logger.info(
            f"Closing browser for: {request.node.name}"
        )

        logger.info(
            f"========== FINISHED TEST: {request.node.name} =========="
        )

        context.close()
        browser.close()


# ==========================================
# PYTEST REPORT HOOK
# ==========================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item,
    call
):

    outcome = yield

    rep = outcome.get_result()

    setattr(
        item,
        "rep_" + rep.when,
        rep
    )


@pytest.hookimpl(
    hookwrapper=True
)
def pytest_runtest_makereport(
        item,
        call
):

    outcome = yield

    report = (
        outcome.get_result()
    )

    if report.when != "call":
        return

    if not API_CONTEXT:
        return

    response = API_CONTEXT.get(
        "response"
    )

    status_code = (
        response.status_code
    )

    result = (
        "PASS"
        if report.passed
        else "FAIL"
    )

    try:
        request_payload = (
            json.dumps(
                API_CONTEXT.get(
                    "payload"
                ),
                indent=4,
                default=str
            )
        )
    except Exception:
        request_payload = str(
            API_CONTEXT.get(
                "payload"
            )
        )

    try:
        response_body = (
            json.dumps(
                response.json(),
                indent=4
            )
        )
    except Exception:
        response_body = (
            response.text
        )

    write_api_log(
        test_name=item.name,
        method=API_CONTEXT.get(
            "method"
        ),
        endpoint=API_CONTEXT.get(
            "endpoint"
        ),
        status_code=status_code,
        expected_status="",
        actual_status=status_code,
        duration=API_CONTEXT.get(
            "duration"
        ),
        request_payload=request_payload,
        response_body=response_body,
        error=(
            report.longreprtext
            if report.failed
            else ""
        )
    )

    API_CONTEXT.clear()

def pytest_sessionfinish(
        session,
        exitstatus
):

    try:

        print_api_summary()

    except Exception as e:

        print(
            "\n[SUMMARY ERROR]",
            e
        )