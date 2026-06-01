from playwright.sync_api import expect
from playwright.sync_api import TimeoutError

from locators.onboarding_locators import (
    OnboardingLocators
)

from pages.base_page import BasePage

class OnboardingPage(BasePage):

    def fill_remaining_dropdowns(self):

        dropdowns = self.onboarding_modal().locator(
            "[role='combobox']:visible"
        )

        for i in range(dropdowns.count()):

            try:

                cb = dropdowns.nth(i)

                if cb.is_disabled():
                    continue

                text = cb.inner_text().strip()

                if text.startswith("Select"):

                    print(
                        f"[Auto Fill] {text}"
                    )

                    cb.click()

                    options = self.page.locator(
                        "[role='option']:visible"
                    )

                    options.first.wait_for(
                        state="visible",
                        timeout=5000
                    )

                    if options.count() > 1:
                        options.nth(1).click()
                    else:
                        options.first.click()

                    self.page.wait_for_timeout(500)

            except Exception as e:

                print(
                    f"[Auto Fill Skip] {e}"
                )
                
    def check_unfilled_required_fields(self):

        """
        Finds all required fields still showing placeholder values.
        Returns list of unfilled fields.
        """

        missing_fields = []

        # Required dropdowns
        dropdowns = self.onboarding_modal().locator(
            "[role='combobox']:visible"
        )

        for i in range(dropdowns.count()):

            try:

                text = dropdowns.nth(i).inner_text().strip()

                print(
                    f"[Validation] Combobox {i}: '{text}'"
                )

                empty_placeholders = [
                    "Select location",
                    "Select sub department",
                    "Select sub-department",
                    "Select grade",
                    "Select level",
                    "Select band",
                    "Select shift",
                    "Select work mode",
                    "Select cost center",
                    "Select job title",
                    "Select reporting manager",
                    "Select type",
                    "Select company entity",
                ]

                if text.strip() in empty_placeholders:
                    missing_fields.append(text)

            except Exception:
                pass

        # Required text inputs
        inputs = self.onboarding_modal().locator(
            "input:visible[required]"
        )

        for i in range(inputs.count()):

            try:

                field = inputs.nth(i)

                value = field.input_value().strip()

                if not value:

                    name = (
                        field.get_attribute("name")
                        or field.get_attribute("id")
                        or f"input_{i}"
                    )

                    missing_fields.append(name)

            except Exception:
                pass

        return missing_fields

    def wait_for_job_title_dropdown(self):

        self.page.wait_for_function(
            """
            () => {
                return [...document.querySelectorAll('*')]
                .some(
                    el =>
                        el.textContent &&
                        el.textContent.includes(
                            'Select job title'
                        )
                );
            }
            """,
            timeout=15000
        )
    def wait_for_dropdown_options(self, timeout=15000):

        self.page.wait_for_function(
            """
            () => {
                return document.querySelectorAll(
                    '[role="option"]'
                ).length > 0;
            }
            """,
            timeout=timeout
        )

        return self.page.locator("[role='option']")

    def __init__(self, page):

        super().__init__(page)
    
    def onboarding_modal(self):
     return self.page.locator("[role='dialog']").last


    # ==========================================
    # OPEN PAGE
    # ==========================================

    def open(self):
        self.page.goto(
            "https://injin.injtechnologies.com/hr/users/onboarding"
        )

    # ==========================================
    # OPEN MODAL
    # ==========================================

    def open_employee_onboarding_modal(self):
        self.page.get_by_role(
            "button",
            name="Employee Onboarding"
        ).click()
        self.page.locator(OnboardingLocators.FIRST_NAME).wait_for(
            state="visible", timeout=10000
        )

    # ==========================================
    # INPUT FIELDS
    # ==========================================

    def enter_first_name(self, value):
        self.page.locator(OnboardingLocators.FIRST_NAME).fill(value)

    def enter_middle_name(self, value):
        self.page.locator(OnboardingLocators.MIDDLE_NAME).fill(value)

    def enter_last_name(self, value):
        self.page.locator(OnboardingLocators.LAST_NAME).fill(value)

    def enter_email(self, value):

        email_field = self.page.locator(
            OnboardingLocators.EMAIL
        )

        email_field.click()

        email_field.press("Control+A")

        email_field.press("Delete")

        email_field.fill("")

        email_field.type(
            value,
            delay=50
        )

        self.page.keyboard.press("Tab")

        actual = email_field.input_value()

        print(
            f"[EMAIL DEBUG] Expected: {value}"
        )

        print(
            f"[EMAIL DEBUG] Actual: {actual}"
        )

        assert actual == value, (
            f"Email overwritten. "
            f"Expected={value}, "
            f"Actual={actual}"
        )

    def enter_job_offered(self, value):
        self.page.locator(OnboardingLocators.JOB_OFFERED).fill(value)

    # ==========================================
    # GENERIC SEARCHABLE DROPDOWN
    # Multi-strategy: handles custom select components where
    # placeholder text appears as a visible span/div, not an
    # HTML placeholder attribute.
    # ==========================================

    def select_dropdown(
    self,
    placeholder_text,
    option_text=None,
    timeout=15000
):
        """
        Stable dropdown selector for React/MUI/ShadCN components.
        """

        print(f"\n[Dropdown] Opening: {placeholder_text}")

        trigger = None

        strategies = [
            lambda: self.page.get_by_text(
                placeholder_text,
                exact=True
            ).first,

            lambda: self.page.locator(
                f"[placeholder='{placeholder_text}']"
            ).first,

            lambda: self.page.locator(
                "[role='combobox']"
            ).filter(
                has_text=placeholder_text
            ).first,
        ]

        for strategy in strategies:

            try:
                candidate = strategy()

                if candidate.count() > 0 and candidate.is_visible():
                    trigger = candidate
                    break

            except Exception:
                continue

        if not trigger:

            raise Exception(
                f"Dropdown not found: {placeholder_text}"
            )

        trigger.scroll_into_view_if_needed()

        trigger.click(force=True)

        options = self.wait_for_dropdown_options()

        option_count = options.count()

        print(
            f"[Dropdown] {placeholder_text} "
            f"loaded {option_count} option(s)"
        )

        for i in range(option_count):
            try:
                print(
                    f"Option {i}: "
                    f"{options.nth(i).inner_text()}"
                )
            except:
                pass

        if option_count == 0:

            raise Exception(
                f"No options rendered for {placeholder_text}"
            )

        if option_text:

            try:

                target = self.page.locator(
                    "[role='option']"
                ).filter(
                    has_text=option_text
                ).first

                target.wait_for(
                    state="visible",
                    timeout=timeout
                )

                target.scroll_into_view_if_needed()

                selected_text = target.inner_text().strip()

                target.click()

                self.page.wait_for_timeout(800)

                print(
                    f"[Dropdown] Selected: "
                    f"{selected_text}"
                )

                return selected_text

            except Exception:

                print(
                    f"[Dropdown] "
                    f"'{option_text}' not found"
                )

        selected_text = options.first.inner_text().strip()

        options.first.click()

        self.page.wait_for_timeout(800)

        return selected_text

        

    def handle_dynamic_dropdowns_after_department(self):

        """
        Fill ONLY dynamically rendered dropdowns
        that are visible and enabled.
        """

        filled = {}

        self.page.wait_for_timeout(2000)

        comboboxes = self.onboarding_modal().locator(
            "[role='combobox']:visible"
        )

        total = comboboxes.count()

        print(f"\n[Dynamic Check] Found {total} comboboxes")

        for i in range(total):

            try:

                cb = comboboxes.nth(i)

                # Skip disabled dropdowns
                if cb.is_disabled():
                    continue

                text = cb.inner_text().strip()

                # We only want dynamically rendered
                # dropdowns that still show placeholder text

                dynamic_placeholders = [
                    "Select sub department",
                    "Select sub-department",
                    "Select location",
                    "Select grade",
                    "Select level",
                    "Select band",
                    "Select shift",
                    "Select work mode",
                    "Select cost center"
                ]

                if text not in dynamic_placeholders:
                    continue

                print(f"[Dynamic] Filling: {text}")

                print(f"\nTrying to open: {text}")

                cb.click()

                self.page.wait_for_timeout(2000)

                options = self.page.locator("[role='option']:visible")

                print(
                    f"Visible options count = {options.count()}"
                )

                for j in range(options.count()):
                    try:
                        print(
                            f"Option {j}: "
                            f"{options.nth(j).inner_text()}"
                        )
                    except:
                        pass

                if options.count() > 1:
                    selected = options.nth(1).inner_text().strip()
                    options.nth(1).click()
                else:
                    selected = options.first.inner_text().strip()
                    options.first.click()

                filled[text] = selected

                self.page.wait_for_timeout(500)

            except Exception as e:

                print(
                    f"[Dynamic] Skip {i}: {e}"
                )

        return filled

    def select_joining_date(self):
        self.page.locator("#joining_date").click()
        self.page.wait_for_timeout(500)

        enabled_dates = self.page.locator(
            "button:not([disabled])[data-day]"
        )

        try:
            enabled_dates.first.wait_for(state="visible", timeout=5000)
        except Exception:
            pass

        count = enabled_dates.count()
        if count == 0:
            raise Exception("No enabled dates found in date picker")

        # Pick index 5 if available (avoids weekends near month start), else first
        idx = min(5, count - 1)
        enabled_dates.nth(idx).click()
        self.page.wait_for_timeout(500)

    # ==========================================
    # BUTTONS
    # ==========================================

    def click_next(self):
        next_button = self.page.locator(OnboardingLocators.NEXT_BUTTON)
        next_button.wait_for(state="visible", timeout=10000)
        expect(next_button).to_be_enabled(timeout=10000)
        next_button.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(500)