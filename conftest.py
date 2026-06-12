import os
from datetime import datetime
from utils.run_manager import get_run_folder
import pytest
from playwright.sync_api import sync_playwright
from utils.test_context import TEST_CONTEXT
from utils.helpers import (
    create_excel_report,
    create_field_log,
    write_result,
)


@pytest.fixture(scope="function")
def page(request):

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
            slow_mo=300
        )

        context = browser.new_context()

        page = context.new_page()

        # ======================================
        # API FAILURE LISTENER
        # ======================================

        def capture_failed_response(response):

            if response.status >= 400:

                print(
                    f"\n[API FAILURE]"
                    f"\nSTATUS : {response.status}"
                    f"\nURL    : {response.url}"
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

                    print(
                        f"[API LOG SAVED] {file_path}"
                    )

                except Exception as e:

                    print(
                        f"[BODY CAPTURE FAILED] {e}"
                    )

        page.on(
            "response",
            capture_failed_response
        )

        print(
            "[INFO] Response listener attached"
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

                page.screenshot(
                    path=screenshot_path,
                    full_page=True
                )

                print(
                    f"[SCREENSHOT SAVED] {screenshot_path}"
                )

            except Exception as e:

                print(
                    f"[SCREENSHOT FAILED] {e}"
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