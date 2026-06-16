from playwright.sync_api import expect
from playwright.sync_api import TimeoutError
from datetime import datetime, timedelta
import os
from utils.helpers import RUN_FOLDER
from locators.onboarding_locators import (
    OnboardingLocators
)

import os

from utils.run_manager import (
    get_run_folder
)

RUN_FOLDER = get_run_folder()

from pages.base_page import BasePage

class OnboardingPage(BasePage):
    def get_next_hierarchy_index(self):

        counter_file = os.path.join(
            RUN_FOLDER,
            "hierarchy_counter.txt"
        )

        if not os.path.exists(counter_file):

            with open(counter_file, "w") as f:
                f.write("0")

        with open(counter_file, "r") as f:

            current = int(
                f.read().strip()
            )

        with open(counter_file, "w") as f:

            f.write(
                str(current + 1)
            )

        return current

    def select_hierarchy_level(
        self,
        option_text
    ):
        print(
            f"\n[HIERARCHY] Selecting: {option_text}"
        )

        dropdown = self.page.locator(
            "div:has(label:text('Hierarchy Level')) button[role='combobox']"
        )

        dropdown.click()

        self.page.wait_for_selector(
            "[role='option']",
            timeout=10000
        )

        option = self.page.locator(
            "[role='option']"
        ).filter(
            has_text=option_text
        ).first

        option.click()

        self.page.wait_for_timeout(500)

        return option_text

    def select_job_offered(
        self,
        option_text
    ):
        print(
            f"\n[JOB OFFERED] Selecting: {option_text}"
        )

        dropdown = self.page.locator(
            "div:has(label:text('Job Offered')) button[role='combobox']"
        )

        dropdown.click()

        self.page.wait_for_selector(
            "[role='option']",
            timeout=10000
        )

        option = self.page.locator(
            "[role='option']"
        ).filter(
            has_text=option_text
        ).first

        option.click()

        self.page.wait_for_timeout(500)

        return option_text

    def get_next_job_title_index(self):

        RUN_FOLDER = get_run_folder()

        counter_file = os.path.join(
            RUN_FOLDER,
            "job_title_counter.txt"
        )

        if not os.path.exists(counter_file):

            with open(counter_file, "w") as f:
                f.write("0")

        with open(counter_file, "r") as f:

            current = int(
                f.read().strip()
            )

        with open(counter_file, "w") as f:

            f.write(
                str(current + 1)
            )

        return current

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

        target_url = (
            "https://injin.injtechnologies.com/hr/users/onboarding"
        )

        self.page.goto(
            target_url,
            wait_until="domcontentloaded"
        )

        self.page.get_by_role(
            "button",
            name="Employee Onboarding"
        ).wait_for(
            state="visible",
            timeout=15000
        )

        if "/onboarding" not in self.page.url:

            self.page.goto(
                target_url,
                wait_until="domcontentloaded"
            )

            self.page.wait_for_timeout(3000)

    # OPEN MODAL

    def open_employee_onboarding_modal(self):

        target_url = (
            "https://injin.injtechnologies.com/hr/users/onboarding"
        )

        for attempt in range(5):

            try:

                if "/onboarding" not in self.page.url:

                    print(
                        "[NOT ON ONBOARDING PAGE]"
                    )

                    self.page.goto(
                        target_url,
                        wait_until="domcontentloaded"
                    )

                    self.page.wait_for_timeout(
                        3000
                    )

                btn = self.page.get_by_role(
                    "button",
                    name="Employee Onboarding"
                )

                btn.wait_for(
                    state="visible",
                    timeout=10000
                )

                btn.click()

                return

            except Exception:

                self.page.reload()

                self.page.wait_for_timeout(
                    3000
                )

        raise Exception(
            "Employee Onboarding button never appeared"
        )
    
    # INPUT FIELDS

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

        assert actual == value, (
            f"Email overwritten. "
            f"Expected={value}, "
            f"Actual={actual}"
        )

    def enter_job_offered(self, value):
        self.page.locator(OnboardingLocators.JOB_OFFERED).fill(value)

    # GENERIC SEARCHABLE DROPDOWN
    # Multi-strategy: handles custom select components where
    # placeholder text appears as a visible span/div, not an
    # HTML placeholder attribute.

    def select_dropdown(
    self,
    placeholder_text,
    option_text=None,
    timeout=15000
):
        """
        Stable dropdown selector for React/MUI/ShadCN components.
        """

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

        # Wait for API-driven options to render
        self.page.wait_for_selector(
            "[role='option']",
            state="visible",
            timeout=10000
        )

        options = self.page.locator("[role='option']")

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

                target = self.page.get_by_role(
                    "option",
                    name=option_text,
                    exact=True
                ).first

                target.wait_for(
                    state="visible",
                    timeout=timeout
                )

                target.scroll_into_view_if_needed()

                selected_text = target.inner_text().strip()

                try:
                    target.click(timeout=3000)

                except Exception:

                    print(
                        f"[Dropdown Retry] Force clicking: "
                        f"{selected_text}"
                    )

                    target.click(
                        force=True,
                        timeout=3000
                    )

                self.page.wait_for_timeout(1000)

                return selected_text

            except Exception:

                print(f"[Dropdown] " f"'{option_text}' not found")
        
        else:

            options = self.page.locator(
                '[role="option"]'
            )

            count = options.count()

            print(
                f"[Dropdown] {placeholder_text} "
                f"loaded {count} option(s)"
            )

            for i in range(count):
                print(
                    f"Option {i}: "
                    f"{options.nth(i).inner_text()}"
                )

            if count <= 1:
                raise Exception(
                    f"No selectable options found "
                    f"for {placeholder_text}"
                )

            option = options.nth(1)

            selected_text = option.inner_text()

            option.click()

            print(
                f"[AUTO SELECT] "
                f"{placeholder_text} -> "
                f"{selected_text}"
            )

            self.page.wait_for_timeout(1000)

            return selected_text

        # =====================================
        # Dynamic Selection Logic
        # =====================================

        if placeholder_text == "Select location":

            valid_options = []

            for i in range(option_count):

                text = options.nth(i).inner_text().strip()

                if text.lower().startswith("select"):
                    continue

                valid_options.append(text)

            if valid_options:

                selected_text = valid_options[0]

                print(
                    f"[LOCATION AUTO SELECT] {selected_text}"
                )

                target = options.filter(
                    has_text=selected_text
                ).first

                target.click(force=True)

                self.page.wait_for_timeout(1000)

                return selected_text

        available_options = []

        for i in range(option_count):

            text = options.nth(i).inner_text().strip()

            if text.lower().startswith("select"):
                continue

            available_options.append(text)

        if not available_options:

            raise Exception(
                f"No valid options found for {placeholder_text}"
            )
        
        # Job Title Rotation
        # =====================================

        if placeholder_text == "Select job title":

            index = (
                self.get_next_job_title_index()
                % len(available_options)
            )

            selected_text = available_options[index]
            options.filter(
                has_text=selected_text
            ).first.click()

            self.page.wait_for_timeout(1000)

            return selected_text
        
        # Hierarchy Rotation

        if placeholder_text == "Select hierarchy level":

            index = (
                self.get_next_hierarchy_index()
                % len(available_options)
            )

            selected_text = available_options[index]

            print(
                f"[HIERARCHY ROTATION] "
                f"Index={index} "
                f"Selected={selected_text}"
            )

            options.filter(
                has_text=selected_text
            ).first.click()

            self.page.wait_for_timeout(1000)

            return selected_text

        # Default Selection

        selected_text = available_options[0]

        options.filter(
            has_text=selected_text
        ).first.click()

        self.page.wait_for_timeout(1000)

        return selected_text

    def handle_dynamic_dropdowns_after_department(self):

        """
        Fill ONLY dynamically rendered dropdowns
        that are visible and enabled.
        """

        filled = {}

        self.page.wait_for_load_state(
            "networkidle"
        )
        self.page.wait_for_timeout(
            1000
        )

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

                cb.click()

                self.page.wait_for_timeout(2000)

                options = self.page.locator("[role='option']:visible")

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

        counter_file = os.path.join(
            RUN_FOLDER,
            "joining_date_counter.txt"
        )
        print(
            f"[JOB TITLE COUNTER FILE] {counter_file}"
        )

        # =====================================
        # Read Counter
        # =====================================

        if not os.path.exists(counter_file):

            with open(counter_file, "w") as f:
                f.write("0")

        with open(counter_file, "r") as f:

            offset = int(f.read().strip())

        # =====================================
        # Calculate Target Date
        # =====================================

        target_date = (
            datetime.now() +
            timedelta(days=offset)
        )

        target_day = (
            f"{target_date.month}/"
            f"{target_date.day}/"
            f"{target_date.year}"
        )

        print(
            f"[DOJ] Selecting: {target_day}"
        )

        # =====================================
        # Open Date Picker
        # =====================================

        self.page.locator(
            "#joining_date"
        ).click()

        self.page.wait_for_timeout(
            1000
        )

        # =====================================
        # Select Exact Date
        # =====================================

        target_button = self.page.locator(
            f'button[data-day="{target_day}"]'
        )

        target_button.first.wait_for(
            state="visible",
            timeout=5000
        )

        target_button.first.click()

        print(
            f"[DOJ Selected] {target_day}"
        )

        # =====================================
        # Increment Counter
        # =====================================

        with open(counter_file, "w") as f:

            f.write(str(offset + 1))

        self.page.wait_for_timeout(
            500
        )

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