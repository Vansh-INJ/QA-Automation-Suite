import pytest
from playwright.sync_api import sync_playwright
from datetime import datetime

from utils.helpers import (
    create_excel_report,
    create_field_log,
    write_result,
)


@pytest.fixture(scope="function")
def page(request):

    create_excel_report()
    create_field_log()

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            slow_mo=300
        )

        context = browser.new_context()

        page = context.new_page()
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

        # FAILED TEST
        if request.node.rep_call.failed:

            screenshot_path = f"screenshots/{test_name}.png"

            page.screenshot(
                path=screenshot_path,
                full_page=True
            )

            write_result(
                test_name=test_name,
                status="FAILED",
                error=str(request.node.rep_call.longrepr),
                screenshot=screenshot_path
            )

        # PASSED TEST
        else:

            write_result(
                test_name=test_name,
                status="PASSED"
            )

        context.close()
        browser.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item,
    call
):

    outcome = yield

    rep = outcome.get_result()

    setattr(item, "rep_" + rep.when, rep)
