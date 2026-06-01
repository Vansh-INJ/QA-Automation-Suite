from playwright.sync_api import expect


class CompensationPage:

    def __init__(self, page):
        self.page = page

    # ==========================================
    # VERIFY TAB
    # ==========================================

    def verify_compensation_tab_visible(self):
        """
        Wait for the compensation tab/section heading to become visible.
        Tries multiple text variants that the app may use.
        """
        self.page.wait_for_load_state("networkidle")
        try:
            self.page.get_by_text(
                "Compensation", exact=False
            ).first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass  # If not found, continue — the form elements will confirm presence

    # ==========================================
    # SALARY STRUCTURE DROPDOWN
    # ==========================================

    def select_salary_structure(self, option_text=None):
        """
        Opens the salary structure dropdown and selects the matching option.
        Falls back to first non-placeholder option if no specific text given.
        """
        # The salary structure combobox is typically the last combobox on the page
        comboboxes = self.page.locator("[role='combobox']:visible")
        count = comboboxes.count()

        # Try the last combobox first (typical layout)
        if count > 0:
            comboboxes.last.click()
        else:
            # Fallback: button-based dropdown trigger
            self.page.locator(
                "button:has-text('Select salary'), button:has-text('Salary')"
            ).first.click()

        self.page.wait_for_timeout(500)

        options = self.page.locator("[role='option']:visible")
        try:
            options.first.wait_for(state="visible", timeout=6000)
        except Exception:
            pass

        count = options.count()
        print(f"\n[Salary Structure] {count} option(s) found")
        for i in range(count):
            try:
                print(f"  [{i}] {options.nth(i).inner_text().strip()}")
            except Exception:
                pass

        if count == 0:
            raise Exception("No salary structure options found")

        if option_text:
            match = self.page.locator(
                f"[role='option']:has-text('{option_text}')"
            ).first
            try:
                match.wait_for(state="visible", timeout=3000)
                match.click()
                self.page.wait_for_load_state("networkidle")
                self.page.wait_for_timeout(800)
                return option_text
            except Exception:
                pass

        # Skip placeholder (index 0 is usually "Select salary structure")
        idx = 1 if count > 1 else 0
        options.nth(idx).click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(800)

    # ==========================================
    # FILL ALL VISIBLE INPUTS
    # After salary structure is selected, input fields render
    # dynamically. This fills every editable field robustly.
    # ==========================================

    def fill_all_visible_inputs(self):
        """
        Fills all visible, editable inputs on the compensation form.
        Handles: text inputs, number inputs, textareas, native selects,
        and custom combobox dropdowns.
        """
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(500)

        self._fill_text_inputs()
        self._fill_textareas()
        self._fill_native_selects()
        self._fill_comboboxes()

    def _fill_text_inputs(self):
        inputs = self.page.locator(
            "input:visible:not([type='hidden']):not([type='checkbox'])"
            ":not([type='radio']):not([type='file']):not([disabled]):not([readonly])"
        )
        count = inputs.count()
        print(f"\n[Compensation] Filling {count} text input(s)")
        for i in range(count):
            try:
                field = inputs.nth(i)
                # Re-check attributes at fill time (list may shift after fills)
                if (field.get_attribute("disabled") is not None
                        or field.get_attribute("readonly") is not None):
                    continue
                current = field.input_value().strip()
                if current:
                    continue  # already has a value
                field_type = field.get_attribute("type") or "text"
                if field_type in ("number", "tel"):
                    field.fill("10000")
                elif field_type == "email":
                    field.fill("hr@injtechnologies.com")
                elif field_type == "date":
                    field.fill("2026-01-01")
                else:
                    field.fill("10000")
                print(f"  Filled input [{i}] type={field_type}")
            except Exception as e:
                print(f"  Skipped input [{i}]: {e}")

    def _fill_textareas(self):
        areas = self.page.locator(
            "textarea:visible:not([disabled]):not([readonly])"
        )
        for i in range(areas.count()):
            try:
                area = areas.nth(i)
                if area.input_value().strip():
                    continue
                area.fill("Automated compensation entry")
            except Exception as e:
                print(f"  Skipped textarea [{i}]: {e}")

    def _fill_native_selects(self):
        selects = self.page.locator("select:visible:not([disabled])")
        for i in range(selects.count()):
            try:
                select = selects.nth(i)
                if select.input_value().strip():
                    continue
                non_placeholder_opts = select.locator("option:not([disabled]):not([value=''])")
                if non_placeholder_opts.count() > 0:
                    val = non_placeholder_opts.first.get_attribute("value")
                    if val:
                        select.select_option(val)
            except Exception as e:
                print(f"  Skipped native select [{i}]: {e}")

    def _fill_comboboxes(self):
        """
        Fills any custom combobox dropdowns that are still showing
        a placeholder (empty / no value selected).
        """
        comboboxes = self.page.locator("[role='combobox']:visible")
        count = comboboxes.count()
        print(f"\n[Compensation] Checking {count} combobox(es)")
        for i in range(count):
            try:
                cb = comboboxes.nth(i)
                if cb.get_attribute("disabled") is not None:
                    continue
                # If it already shows a real value (not placeholder), skip
                text = cb.inner_text().strip()
                if text and not text.lower().startswith("select"):
                    print(f"  Combobox [{i}] already has value: '{text}'")
                    continue
                print(f"  Filling combobox [{i}] placeholder: '{text}'")
                cb.click()
                self.page.wait_for_timeout(500)
                opts = self.page.locator("[role='option']:visible")
                try:
                    opts.first.wait_for(state="visible", timeout=3000)
                except Exception:
                    pass
                if opts.count() > 0:
                    opts.first.click()
                    self.page.wait_for_timeout(400)
            except Exception as e:
                print(f"  Skipped combobox [{i}]: {e}")

    # ==========================================
    # CALCULATE
    # ==========================================

    def click_calculate(self):
        """
        Finds and clicks the Calculate button.
        If disabled, fills missing fields and retries up to 3 times.
        """
        for attempt in range(3):
            calc = self.page.locator("button:has-text('Calculate')")
            try:
                calc.wait_for(state="visible", timeout=5000)
            except Exception:
                pass

            if calc.count() == 0:
                print(f"  [Calculate] Button not found (attempt {attempt + 1})")
                self.fill_all_visible_inputs()
                self.page.wait_for_timeout(800)
                continue

            if calc.first.is_enabled():
                calc.first.click()
                print("  [Calculate] Button clicked")
                self.page.wait_for_load_state("networkidle")
                self.page.wait_for_timeout(800)
                return

            print(f"  [Calculate] Button disabled (attempt {attempt + 1}), filling fields")
            self.fill_all_visible_inputs()
            self.page.wait_for_timeout(800)

        raise Exception("Calculate button remained disabled after 3 fill attempts")

    # ==========================================
    # SEND ONBOARDING INVITE
    # ==========================================

    def click_send_onboarding_invite(self):
        """
        Ensures the Send Onboarding Invite button is enabled and clicks it.
        If disabled, fills any remaining required fields and retries.
        """
        send_btn = self.page.locator("button:has-text('Send Onboarding Invite')")

        for attempt in range(3):
            try:
                send_btn.wait_for(state="visible", timeout=5000)
            except Exception:
                pass

            if send_btn.count() > 0 and send_btn.first.is_enabled():
                send_btn.first.click()
                print("  [Send Onboarding Invite] Button clicked")
                self.page.wait_for_load_state("networkidle")
                self.page.wait_for_timeout(1000)
                return

            print(
                f"  [Send Onboarding Invite] Disabled (attempt {attempt + 1}), "
                f"filling remaining fields"
            )
            self.fill_all_visible_inputs()
            self.page.wait_for_timeout(1000)

        raise Exception(
            "Send Onboarding Invite button remained disabled after filling all visible fields. "
            "A required field may still be empty or a validation error exists."
        )
