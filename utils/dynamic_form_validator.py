from playwright.sync_api import Page


def get_tabs(page: Page):
    return page.locator('[role="tab"]')

def get_required_fields(page: Page):
    return page.locator("p.text-destructive")

def validate_current_tab(page: Page):

    errors = page.locator(
        '[role="tabpanel"]:not([hidden]) p.text-destructive'
    )

    count = errors.count()

    missing = []

    for i in range(count):
        msg = errors.nth(i).inner_text().strip()

        if "required" in msg.lower():
            missing.append(msg)

    return missing


def validate_all_tabs(page: Page):

    tabs = page.locator('[role="tab"]')

    total_tabs = tabs.count()

    results = {}

    for i in range(total_tabs):

        tab = tabs.nth(i)

        tab_name = tab.inner_text().strip()

        tab.scroll_into_view_if_needed()
        tab.click(force=True)

        page.wait_for_load_state("networkidle")

        missing = validate_current_tab(page)

        results[tab_name] = missing

    return results
