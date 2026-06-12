from test_data.employee_data import (
    CANDIDATE_DATA,
    TEST_PDF
)
from pages.candidate_form_filler import (
        CandidateFormFiller
    )
import random

class CandidateOnboardingPage:

    
    def __init__(self, page):
        self.page = page

    
    def decline_offer(self):

        with self.page.expect_response(
            lambda r:
            "/decline" in r.url
            and r.status == 200
        ) as response_info:

            self.page.get_by_role(
                "button",
                name="Decline Offer"
            ).click()

        response = response_info.value

        payload = response.json()

        print(
            "\n===== DECLINE OFFER RESPONSE ====="
        )

        print(payload)

        return payload

    
    def open_candidate_by_index(self, index):

        rows = self.page.locator(
            "table tbody tr"
        )

        row = rows.nth(index)

        action_btn = (
            row.locator("td")
            .nth(7)
            .locator("button")
            .nth(1)
        )

        action_btn.click()

        self.page.wait_for_load_state(
            "networkidle"
        )

        print(
            f"[CANDIDATE OPENED] Row {index}"
        )

        
    
    def submit_onboarding(self):

        self.page.get_by_role(
            "button",
            name="Submit Onboarding"
        ).click()

        self.page.wait_for_timeout(
            3000
        )

        print(
            "[SUCCESS] Onboarding submitted"
        )


    def continue_onboarding(self):

        self.page.get_by_role(
            "button",
            name="Continue Onboarding"
        ).click()

    def enter_first_name(self, value):

        self.page.locator(
            "#first_name"
        ).fill(value)

    def enter_last_name(self, value):

        self.page.locator(
            "#last_name"
        ).fill(value)

    def submit(self):

        self.page.get_by_role(
            "button",
            name="Submit"
        ).click()


    def accept_offer(self):
        self.page.get_by_role(
            "button",
            name="Accept Offer"
        ).click()

    
    def verify_form_loaded(self):
        self.page.wait_for_load_state("networkidle")

        controls = self.page.locator(
            "input, textarea, select, [role='combobox']"
        )

        controls.first.wait_for(timeout=10000)

        count = controls.count()

        print(
            f"[Candidate Form] Controls found: {count}"
        )

        assert "/form" in self.page.url

        assert count > 0

    
    def revise_and_submit_onboarding(self):

        filler = CandidateFormFiller(
            self.page
        )

        tabs = self.page.locator(
            '[role="tab"]'
        )

        total = tabs.count()

        all_data = {}
        revised_fields = {}

        for i in range(total):

            tab = tabs.nth(i)

            tab_name = tab.inner_text().strip()

            print(
                f"\n[Revising Tab] {tab_name}"
            )

            inputs = self.page.locator("input")

            print(f"\n===== {tab_name} INPUTS =====")

            for j in range(inputs.count()):

                print(
                    "ID =",
                    inputs.nth(j).get_attribute("id")
                )

            tab.click()

            self.page.wait_for_load_state("networkidle")

            self.page.wait_for_timeout(
                2000
            )

            # ----------------------------------
            # PERSONAL
            # ----------------------------------

            if "Personal" in tab_name:

                inputs = self.page.locator("input")

                print("\n===== PERSONAL TAB INPUT IDS =====")

                for j in range(inputs.count()):

                    print(
                        inputs.nth(j).get_attribute("id")
                    )

                try:

                    first_name = self.page.locator(
                        "#personal-first_name-0"
                    )

                    if first_name.count():

                        old_value = first_name.input_value()

                        first_name.fill("Revised")

                        revised_fields["first_name"] = {
                            "old": old_value,
                            "new": "Revised"
                        }

                        print(
                            f"[UPDATED] First Name: "
                            f"{old_value} -> Revised"
                        )

                except:
                    pass

                try:

                    dob = self.page.locator(
                        "#personal-date_of_birth-0"
                    )

                    current_dob = dob.inner_text()

                    print(
                        f"[CURRENT DOB] {current_dob}"
                    )

                    # If DOB already exists,
                    # don't touch it.

                    if (
                        current_dob.strip()
                        and current_dob != "Select date"
                    ):

                        print(
                            "[DOB ALREADY PRESENT]"
                        )

                    else:

                        filler.fill_datepickers()

                except Exception as e:

                    print(
                        f"[DOB ERROR] {e}"
                    )

            # ----------------------------------
            # CONTACT
            # ----------------------------------

            elif "Communication" in tab_name:

                try:

                    phone = self.page.locator(
                        "#communication-primary_phone-0"
                    )

                    if phone.count():

                        old_value = phone.input_value()

                        new_phone = (
                            "9" +
                            str(random.randint(
                                100000000,
                                999999999
                            ))
                        )

                        phone.fill(new_phone)

                        revised_fields["phone"] = {
                            "old": old_value,
                            "new": new_phone
                        }

                        print(
                            f"[UPDATED] Phone: "
                            f"{old_value} -> {new_phone}"
                        )

                except:
                    pass

            # ----------------------------------
            # ADDRESS
            # ----------------------------------

            elif "Current Address" in tab_name:

                try:

                    city = self.page.locator(
                        "#addresses.current-city-0"
                    )

                    if city.count():

                        old_value = city.input_value()

                        city.fill("Noida")

                        revised_fields["city"] = {
                            "old": old_value,
                            "new": "Noida"
                        }

                        print(
                            f"[UPDATED] City: "
                            f"{old_value} -> Noida"
                        )

                except:
                    pass

            # Don't refill already completed tabs
            tab_data = {}

            all_data.update(
                tab_data
            )
        
        if not revised_fields:

            print(
                "\n[WARNING] No fields were revised"
            )

        else:

            print(
                "\n===== REVISED FIELDS ====="
            )

            for field, values in revised_fields.items():

                print(
                    f"{field}: "
                    f"{values['old']} "
                    f"-> "
                    f"{values['new']}"
                )

        self.submit_onboarding()

        return all_data

    
    def fill_all_tabs(self):

        filler = CandidateFormFiller(
            self.page
        )

        tabs = self.page.locator(
            '[role="tab"]'
        )

        total = tabs.count()

        all_data = {}

        for i in range(total):

            tab = tabs.nth(i)

            tab_name = tab.inner_text().strip()

            print(
                f"\n[Filling Tab] {tab_name}"
            )

            tab.click()
            self.page.wait_for_timeout(2000)
            
            self.page.wait_for_timeout(
                500
            )

            tab_data = filler.fill_current_tab(
                skip_dates=False
            )

            all_data.update(tab_data)

        print(
            "\n===== ALL TABS FILLED ====="
        )

        self.submit_onboarding()

        print("\n===== FINAL CANDIDATE DATA =====")

        for k, v in all_data.items():
            print(k, "=", v)

        print("Total Candidate Fields:", len(all_data))
        

        return all_data
