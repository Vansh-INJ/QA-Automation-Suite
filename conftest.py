import os
import json
from datetime import datetime

from utils.logger import logger
from utils.run_manager import get_run_folder

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from utils.test_context import TEST_CONTEXT
from utils.api_context import API_CONTEXT
from utils.helpers import (
    create_excel_report,
    create_field_log,
    write_result,
)

from utils.api_summary import print_api_summary

from api_framework.auth.token_manager import TokenManager
from api_framework.clients.offer_client import OfferClient
from api_framework.config.settings import Settings


load_dotenv()


# ==========================================
# API CLIENT FIXTURE
# ==========================================
# NOTE: the original file had this fixture defined TWICE (once function-scoped,
# once session-scoped). Python silently keeps only the second definition, so the
# session-scoped version was the one actually in effect, meaning the same token
# was reused for the whole test session. Kept function-scoped here so a fresh
# token is fetched per test and you don't get bitten by token expiry on long runs.

@pytest.fixture(scope="function")
def authenticated_offer_client():
    return OfferClient(
        base_url=Settings.BASE_URL,
        headers=TokenManager.get_headers(),
    )


# ==========================================
# RUN FOLDER (SESSION-SCOPED)
# ==========================================
# Resolves the run folder + initializes the Excel report file exactly ONCE
# per test session, instead of once per test. This is what `page` used to do
# on every test setup. Both API-only tests and UI tests now depend on this,
# so the report/run folder exists regardless of which kind of test runs first.

@pytest.fixture(scope="session")
def run_folder():
    folder = get_run_folder()
    create_excel_report()

    os.makedirs(os.path.join(folder, "screenshots"), exist_ok=True)
    os.makedirs(os.path.join(folder, "api_failures"), exist_ok=True)

    return folder


# ==========================================
# RESULT REPORTING (AUTOUSE - RUNS FOR EVERY TEST)
# ==========================================
# This is the actual fix. Excel result-writing no longer lives inside `page`,
# so it no longer skips tests that don't request `page` (i.e. every pure API
# test, like test_send_offer.py).
#
# Teardown ordering note: this fixture does not depend on `page`, so pytest
# instantiates it BEFORE `page` and tears it down AFTER `page` (fixtures tear
# down in reverse setup order). That means if a UI test uses `page` and fails,
# `page`'s teardown (below) has already written the screenshot path into
# TEST_CONTEXT by the time this fixture's teardown runs and reads it.

@pytest.fixture(autouse=True)
def report_result(request, run_folder):

    test_path = str(
        request.node.fspath
    ).replace("\\", "/")

    # Skip API tests entirely.
    # API tests write their own rows using
    # log_api_execution()
    if "/test/api/" in test_path:
        yield
        return

    test_name = request.node.name

    logger.info(
        f"========== STARTING TEST: {test_name} =========="
    )

    yield

    rep_call = getattr(
        request.node,
        "rep_call",
        None
    )

    failed = (
        rep_call is not None
        and rep_call.failed
    )

    if failed:
        logger.error(
            f"TEST FAILED: {test_name}"
        )
        error = str(rep_call.longrepr)
    else:
        logger.info(
            f"TEST PASSED: {test_name}"
        )
        error = ""

    def excel_safe(value):

        if isinstance(
            value,
            (dict, list)
        ):
            try:
                return json.dumps(
                    value,
                    indent=4
                )
            except Exception:
                return str(value)

        return value

    method = ""
    endpoint = ""
    api_status = TEST_CONTEXT.get(
        "api_status",
        ""
    )
    duration = ""
    request_headers = ""
    request_payload = ""
    response_body = TEST_CONTEXT.get(
        "api_response",
        ""
    )

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
            ""
        )

        endpoint = API_CONTEXT.get(
            "endpoint",
            ""
        )

        api_status = getattr(
            response_obj,
            "status_code",
            api_status
        )

        duration = API_CONTEXT.get(
            "duration",
            ""
        )

        request_headers = API_CONTEXT.get(
            "headers",
            ""
        )

        request_payload = API_CONTEXT.get(
            "payload",
            ""
        )

    sla = TEST_CONTEXT.get(
        "sla",
        ""
    )

    sla_status = ""

    if sla != "" and duration != "":
        try:
            sla_status = (
                "PASS"
                if float(duration) <= float(sla)
                else "FAIL"
            )
        except Exception:
            pass
    
    if "/api/" not in str(request.node.nodeid).replace("\\", "/"):
      write_result(...)

    write_result(
        test_name=test_name,
        status="FAILED" if failed else "PASSED",
        action=excel_safe(
            TEST_CONTEXT.get(
                "action",
                ""
            )
        ),
        candidate_name=excel_safe(
            TEST_CONTEXT.get(
                "candidate_name",
                ""
            )
        ),
        candidate_email=excel_safe(
            TEST_CONTEXT.get(
                "candidate_email",
                ""
            )
        ),
        api_message=excel_safe(
            TEST_CONTEXT.get(
                "api_message",
                ""
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
            ""
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
            ""
        ),
    )

    logger.info(
        f"========== FINISHED TEST: {test_name} =========="
    )
# ==========================================
# PLAYWRIGHT PAGE FIXTURE (UI TESTS ONLY)
# ==========================================
# Now responsible ONLY for the browser lifecycle: launch, context/page,
# API-failure listener, autocomplete disabling, and screenshot-on-failure.
# It no longer touches the Excel report directly — on failure it just drops
# the screenshot path into TEST_CONTEXT for `report_result` to pick up.

@pytest.fixture(scope="function")
def page(request, run_folder):
    SCREENSHOT_DIR = os.path.join(run_folder, "screenshots")
    API_FAILURE_DIR = os.path.join(run_folder, "api_failures")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            slow_mo=100,
        )
        logger.info("Chromium browser launched")

        context = browser.new_context()
        page = context.new_page()
        logger.info("New browser page created")

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
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_path = os.path.join(
                        API_FAILURE_DIR,
                        f"failure_{response.status}_{timestamp}.txt",
                    )
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"STATUS: {response.status}\n")
                        f.write(f"URL: {response.url}\n\n")
                        f.write(body)
                    logger.info(f"API failure log saved: {file_path}")
                except Exception as e:
                    logger.exception(f"Failed to capture API response body: {e}")

        page.on("response", capture_failed_response)
        logger.info("Response listener attached")

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

        # ======================================
        # SCREENSHOT ON FAILURE
        # ======================================

        test_name = request.node.name

        if request.node.rep_call.failed:
            try:
                screenshot_path = os.path.join(
                    SCREENSHOT_DIR,
                    f"{test_name}.png",
                )
                page.screenshot(
                    path=screenshot_path,
                    full_page=True,
                )
                logger.info(f"Failure screenshot saved: {screenshot_path}")
                TEST_CONTEXT["screenshot"] = screenshot_path
            except Exception as e:
                logger.exception(f"Failed to capture screenshot: {e}")
                TEST_CONTEXT["screenshot"] = ""

        context.close()
        logger.info(f"Closing browser for: {test_name}")
        browser.close()


# ==========================================
# PYTEST REPORT HOOK
# ==========================================
# Unchanged. (Original file also defined `pytest_sessionfinish` twice;
# deduplicated below — the second definition was silently overriding the
# first anyway, so this changes no behavior.)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


def pytest_sessionfinish(session, exitstatus):
    try:
        print_api_summary()
    except Exception as e:
        print("\n[SUMMARY ERROR]", e)