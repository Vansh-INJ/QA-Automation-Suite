import os

from playwright.sync_api import Page
from datetime import datetime
from utils.helpers import RUN_FOLDER
from test_data.employee_data import (
    CANDIDATE_DATA,
    TEST_PDF,
    PROFILE_IMAGE
)


class CandidateFormFiller:

    def get_next_dropdown_index(self, dropdown_name):

        counter_file = os.path.join(
            RUN_FOLDER,
            f"{dropdown_name}_counter.txt"
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

    def __init__(self, page: Page):
        self.page = page
        self.captured_data = {}

    def fill_visible_inputs(self):

        field_map = {

            # Communication
            "communication-primary_phone-0":
                CANDIDATE_DATA["phone"],

            "communication-secondary_phone-0":
                "9876543211",

            "communication-linkedin_url-0":
                "https://linkedin.com/in/testcandidate",

            # Bank
            # Bank
            "bank-account_holder_name-0":
                CANDIDATE_DATA["account_holder_name"],

            "bank-bank_name-0":
                CANDIDATE_DATA["bank_name"],

            "bank-branch-0":
                CANDIDATE_DATA["branch"],

            "bank-account_number-0":
                CANDIDATE_DATA["account_number"],

            "bank-ifsc_code-0":
                CANDIDATE_DATA["ifsc"],

            # Identity
            "identity-aadhar-0":
                CANDIDATE_DATA["aadhar"],

            "identity-pan-0":
                CANDIDATE_DATA["pan"],

            "identity-uan-0":
                "123456789012",

            # Current Address
            "addresses.current-line1-0":
                CANDIDATE_DATA["address1"],

            "addresses.current-line2-0":
                CANDIDATE_DATA["address2"],

            "addresses.current-city-0":
                CANDIDATE_DATA["city"],

            "addresses.current-pin_code-0":
                CANDIDATE_DATA["pin"],

            # Permanent Address
            "addresses.permanent-line1-0":
                CANDIDATE_DATA["address1"],

            "addresses.permanent-line2-0":
                CANDIDATE_DATA["address2"],

            "addresses.permanent-city-0":
                CANDIDATE_DATA["city"],

            "addresses.permanent-pin_code-0":
                CANDIDATE_DATA["pin"],

            # Family
            "family_members-name-0":
                CANDIDATE_DATA["family_name"],

            "family_members-contact_number-0":
               CANDIDATE_DATA["family_contact"],

            # Education
            # Education
            "education-college-0":
                CANDIDATE_DATA["college"],

            "education-course-0":
                CANDIDATE_DATA["course"],

            "education-specialization-0":
                CANDIDATE_DATA["specialization"],

            "education-passing_year-0":
                str(CANDIDATE_DATA["passing_year"]),
        }

        inputs = self.page.locator(
            'input:not([type="hidden"]):not([type="file"])'
        )

        total = inputs.count()

        print(f"[Inputs Found] {total}")

        for i in range(total):

            inp = inputs.nth(i)

            try:

                field_name = inp.get_attribute("name")
                field_id = inp.get_attribute("id")

                key = (
                    field_name
                    or field_id
                    or ""
                ).lower()

                current = inp.input_value()

                if current.strip():
                    continue

                value = field_map.get(key)

                print(
                    f"[Input] "
                    f"name={field_name} "
                    f"id={field_id} "
                    f"key={key} "
                    f"value={value}"
                )

                if not value:

                    print(
                        f"[No Mapping Found] {key}"
                    )

                    continue

                inp.fill(str(value))

                self.captured_data[key] = value     

            except Exception as e:

                print(
                    f"[Input Error] {e}"
                )

    def fill_visible_dropdowns(self):

        dropdowns = self.page.locator(
            'button[role="combobox"]'
        )

        total = dropdowns.count()

        print(
            f"[Dropdowns Found] {total}"
        )

        for i in range(total):

            try:

                dropdown = dropdowns.nth(i)

                dropdown.click()

                self.page.wait_for_timeout(
                    500
                )

                options = self.page.locator(
                    '[role="option"]'
                )

                option_count = options.count()

                available_options = []

                for j in range(option_count):

                    txt = (
                        options.nth(j)
                        .inner_text()
                        .strip()
                    )

                    if (
                        not txt
                        or txt.lower().startswith("select")
                        or txt.lower() == "all"
                    ):
                        continue

                    available_options.append(txt)

                if not available_options:

                    print(
                        "[Dropdown] No valid options found"
                    )
                    continue

                dropdown_name = (
                    dropdown.get_attribute("name")
                    or dropdown.get_attribute("id")
                    or f"dropdown_{i}"
                )

                rotation_index = (
                    self.get_next_dropdown_index(
                        dropdown_name
                    )
                    % len(available_options)
                )

                selected_text = available_options[
                    rotation_index
                ]

                print(
                    f"[DROPDOWN ROTATION] "
                    f"{dropdown_name} | "
                    f"Index={rotation_index} | "
                    f"Selected={selected_text}"
                )

                options.filter(
                    has_text=selected_text
                ).first.click()

                self.captured_data[
                    dropdown_name
                ] = selected_text

                self.captured_data[
                    f"dropdown_{i}"
                ] = selected_text

                self.page.wait_for_timeout(
                    500
                )

            except Exception as e:

                print(
                    f"[Dropdown Error] {e}"
                )


    def fill_datepickers(self):

            # =====================================
            # DOB FIELD
            # =====================================
            try:

                dob_button = self.page.locator(
                    "#personal-date_of_birth-0"
                )

                if dob_button.count() and dob_button.is_visible():

                    dob = datetime.strptime(
                        CANDIDATE_DATA["dob"],
                        "%Y-%m-%d"
                    )

                    month_name = dob.strftime("%b")   # Jun
                    year = str(dob.year)             # 1995
                    day = str(dob.day)               # 15

                    dob_button.click()

                    self.page.wait_for_timeout(
                        1000
                    )

                    print(
                        "[DOB Calendar Opened]"
                    )

                    self.page.screenshot(
                        path="dob_calendar_debug.png"
                    )

                    # =========================
                    # MONTH
                    # =========================
                    month_dropdown = self.page.locator(
                        'select[aria-label="Choose the Month"]'
                    )

                    if month_dropdown.count():

                        month_dropdown.select_option(
                            label=month_name
                        )

                        print(
                            f"[DOB Month Selected] {month_name}"
                        )

                    # =========================
                    # YEAR
                    # =========================
                    year_dropdown = self.page.locator(
                        'select[aria-label="Choose the Year"]'
                    )

                    if year_dropdown.count():

                        year_dropdown.select_option(
                            value=year
                        )

                        print(
                            f"[DOB Year Selected] {year}"
                        )

                    self.page.wait_for_timeout(
                        1000
                    )

                    # =========================
                    # DAY
                    # =========================
                    day_button = self.page.get_by_role(
                        "gridcell",
                        name=day
                    )

                    if day_button.count():

                        day_button.first.click()

                        print(
                            f"[DOB Day Selected] {day}"
                        )
                        self.captured_data[
                            "date_of_birth"
                        ] = CANDIDATE_DATA["dob"]

                        print(
                            f"[DOB Selected] {day}-{month_name}-{year}"
                        )

                        self.captured_data[
                            "date_of_birth"
                        ] = CANDIDATE_DATA["dob"]

                    self.page.wait_for_timeout(
                        1000
                    )

                    selected_value = dob_button.inner_text()

                    print(
                        f"[DOB Button Value] {selected_value}"
                    )

                    assert selected_value != "Select date", \
                      "DOB was not actually selected"

            except Exception as e:

                print(
                    f"[DOB Error] {e}"
                )

            # =====================================
            # OTHER DATE PICKERS
            # =====================================
            try:

                buttons = self.page.locator(
                    'button:has-text("Select date")'
                )

                count = buttons.count()

                print(
                    f"[Other Date Pickers Found] {count}"
                )

                for i in range(count):

                    try:

                        btn = buttons.nth(i)

                        btn_id = (
                            btn.get_attribute("id")
                            or ""
                        )

                        # Skip DOB
                        if "date_of_birth" in btn_id:
                            continue

                        btn.click()

                        self.page.wait_for_timeout(
                            500
                        )

                        days = self.page.locator(
                            '[role="gridcell"] button:not([disabled])'
                        )

                        if days.count():

                            days.first.click()

                            self.captured_data[
                                btn_id or f"date_{i}"
                            ] = "selected"

                            print(
                                f"[Date Selected] {btn_id}"
                            )

                    except Exception as e:

                        print(
                            f"[Date Error] {e}"
                        )

            except Exception as e:

                print(
                    f"[Date Picker Error] {e}"
                )

    def fill_file_uploads(self):

        profile_input = self.page.locator(
            'input[type="file"]:not([id^="doc-"])'
        ).first

        if profile_input.count():

            profile_input.set_input_files(
                PROFILE_IMAGE
            )

            self.page.wait_for_timeout(
                1000
            )

            try:

                profile_container = profile_input.locator(
                    "xpath=ancestor::div[contains(@class,'space-y-1.5')]"
                )

                profile_upload_btn = profile_container.get_by_role(
                    "button",
                    name="Upload"
                )

                profile_upload_btn.click()

                self.page.wait_for_timeout(
                    3000
                )

                print(
                    "[Profile Image Uploaded]"
                )

            except Exception as e:

                print(
                    f"[Profile Upload Button Error] {e}"
                )

            self.captured_data[
                "profile_image"
            ] = PROFILE_IMAGE

        print("\n===== DOCUMENT UPLOAD START =====")

        uploaded = 0

        while True:

            document_inputs = self.page.locator(
                'input[type="file"][id^="doc-"]'
            )

            remaining = document_inputs.count()

            if remaining == 0:

                break

            try:

                file_input = document_inputs.first

                doc_id = (
                    file_input.get_attribute("id")
                    or "unknown"
                )

                print(
                    f"[Uploading] {doc_id}"
                )

                file_input.set_input_files(
                    TEST_PDF
                )
                self.captured_data[
                    doc_id
                ] = TEST_PDF

                container = file_input.locator(
                    "xpath=ancestor::div[contains(@class,'space-y-1.5')]"
                )

                upload_btn = container.get_by_role(
                    "button",
                    name="Upload"
                )

                upload_btn.click()

                self.page.wait_for_timeout(
                    3000
                )

                uploaded += 1

                print(
                    f"[Uploaded] {doc_id}"
                )

                self.captured_data[
                    f"upload_{doc_id}"
                ] = TEST_PDF

            except Exception as e:

                print(
                    f"[Upload Error] {doc_id}: {e}"
                )

                break

        print(
            f"===== DOCUMENT UPLOAD COMPLETE ({uploaded}) =====\n"
        )
    def fill_checkboxes(self):

        try:

            checkboxes = self.page.locator(
                '[role="checkbox"]'
            )

            total = checkboxes.count()

            print(
                f"[Checkboxes Found] {total}"
            )

            for i in range(total):

                try:

                    cb = checkboxes.nth(i)

                    checked = cb.get_attribute(
                        "aria-checked"
                    )

                    if checked != "true":

                        cb.click(force=True)

                        self.page.wait_for_timeout(
                            300
                        )

                    checkbox_name = (
                        cb.get_attribute("id")
                        or f"checkbox_{i}"
                    )

                    self.captured_data[
                        checkbox_name
                    ] = True

                    print(
                        f"[Checkbox Checked] "
                        f"{checkbox_name}"
                    )

                except Exception as e:

                    print(
                        f"[Checkbox Error] {e}"
                    )

        except Exception as e:

            print(
                f"[Checkbox Section Error] {e}"
            )
    def fill_current_tab(
        self,
        skip_dates=False
    ):

        print(
            "\n===== START TAB FILLING ====="
        )

        self.fill_visible_inputs()

        print(
            f"[DEBUG] skip_dates={skip_dates}"
        )

        if not skip_dates:

            print(
                "[DEBUG] Calling fill_datepickers()"
            )

            self.fill_datepickers()

        self.fill_visible_dropdowns()

        self.fill_file_uploads()

        self.fill_checkboxes()

        print(
            "===== TAB FILLING COMPLETE =====\n"
        )

        return self.captured_data