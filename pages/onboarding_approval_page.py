from datetime import datetime
from utils.test_context import TEST_CONTEXT
from datetime import datetime

class OnboardingApprovalPage:

    def __init__(self, page):
        self.page = page


    def revert_no_show(self):

        # =====================================
        # CLICK REVERT NO SHOW
        # =====================================

        revert_btn = self.page.get_by_role(
            "button",
            name="Revert No Show"
        )

        revert_btn.wait_for(
            state="visible",
            timeout=10000
        )

        revert_btn.click()

        print(
            "[REVERT NO SHOW CLICKED]"
        )

        # CONFIRM POPUP

        yes_btn = self.page.get_by_role(
            "button",
            name="Yes"
        )

        yes_btn.wait_for(
            state="visible",
            timeout=5000
        )

        yes_btn.click()

        print(
            "[YES CLICKED]"
        )

        # =====================================
        # SELECT TODAY AS NEW DOJ
        # =====================================

        date_btn = self.page.locator(
            'button[data-slot="popover-trigger"]'
        ).last

        date_btn.wait_for(
            state="visible",
            timeout=10000
        )

        date_btn.click()

        print("[DATE PICKER OPENED]")

        target_date = datetime.now()

        target_day = (
            f"{target_date.month}/"
            f"{target_date.day}/"
            f"{target_date.year}"
        )

        day_btn = self.page.locator(
            f'button[data-day="{target_day}"]'
        )

        day_btn.first.wait_for(
            state="visible",
            timeout=5000
        )

        day_btn.first.click()

        print(
            f"[NEW DOJ SELECTED] {target_day}"
        )

        # =====================================
        # CONFIRM + CAPTURE API
        # =====================================

        confirm_btn = self.page.get_by_role(
            "button",
            name="Confirm"
        )

        with self.page.expect_response(
            lambda response:
            "revert-no-show" in response.url
            and response.status == 200
        ) as response_info:

            confirm_btn.click()

        response = response_info.value

        payload = response.json()

        print(
            "\n===== REVERT NO SHOW RESPONSE ====="
        )

        print(payload)

        return payload

    
    def open_no_show_tab(self):

        self.page.get_by_role(
            "tab",
            name="No Show"
        ).click()

        self.page.wait_for_load_state(
            "networkidle"
        )

        print("[NO SHOW TAB OPENED]")

    
    def capture_candidate_details(self, row):

        cells = row.locator("td")

        candidate_name = (
            cells.nth(0)
            .inner_text()
            .strip()
        )

        candidate_email = (
            cells.nth(1)
            .inner_text()
            .strip()
        )

        TEST_CONTEXT["candidate_name"] = (
            candidate_name
        )

        TEST_CONTEXT["candidate_email"] = (
            candidate_email
        )

        print(
            f"[CANDIDATE] "
            f"{candidate_name} | {candidate_email}"
        )

    
    def mark_no_show(self):

        print("\n[STEP] Marking candidate as No Show")

        with self.page.expect_response(
            lambda response:
            "/no-show" in response.url
            and response.request.method == "POST"
        ) as response_info:

            self.page.locator(
                "button:has-text('No Show')"
            ).click()

            self.page.locator(
                "button:has-text('Yes')"
            ).click()

        response = response_info.value

        print(
            f"[NO SHOW API] {response.status} | {response.url}"
        )

        assert response.status == 200, (
            f"No Show API failed. "
            f"Expected 200, got {response.status}"
        )

        body = response.json()

        print("\n[NO SHOW RESPONSE]")
        print(body)

        assert body["status"] == "success"

        assert body["data"]["success"] is True

        assert (
            body["data"]["message"]
            == "Marked as no-show successfully"
        )

        print(
            "\n[SUCCESS] Candidate marked as No Show successfully"
        )

        return body
    
    def reload_filtered_candidates(self):

        today = datetime.now().strftime("%Y-%m-%d")

        self.page.goto(
            f"https://injin.injtechnologies.com/hr/users/onboarding?limit=100&join_date={today}"
        )

        self.page.wait_for_load_state(
            "networkidle"
        )

    def find_approve_candidate(self):

        rows = self.page.locator(
            "table tbody tr"
        )

        total = rows.count()

        print(
            f"[SEARCHING APPROVE] {total} candidates"
        )

        for i in range(total):

            try:

                rows = self.page.locator(
                    "table tbody tr"
                )

                row = rows.nth(i)

                cells = row.locator("td")

                candidate_name = (
                    cells.nth(0)
                    .inner_text()
                    .strip()
                )

                candidate_email = (
                    cells.nth(1)
                    .inner_text()
                    .strip()
                )

                TEST_CONTEXT["candidate_name"] = (
                    candidate_name
                )

                TEST_CONTEXT["candidate_email"] = (
                    candidate_email
                )

                print(
                    f"\nChecking Row {i}"
                    f"\nName : {candidate_name}"
                    f"\nEmail: {candidate_email}"
                )

                self.capture_candidate_details(row)

                action_cell = row.locator(
                    "td"
                ).nth(7)

                edit_btn = action_cell.locator(
                    "button[title='Edit details']"
                )

                edit_btn.wait_for(
                    state="visible",
                    timeout=10000
                )

                print(
                    "Edit count:",
                    edit_btn.count()
                )

                print(
                    "Visible:",
                    edit_btn.is_visible()
                )

                print(
                    "Enabled:",
                    edit_btn.is_enabled()
                )
                
                edit_btn.scroll_into_view_if_needed()
                edit_btn.highlight()
                print(
                    "Current URL:",
                    self.page.url
                )

                self.page.wait_for_timeout(2000)

                print(
                    "Page title:",
                    self.page.title()
                )
                print("BEFORE CLICK")

                edit_btn.click(force=True)

                print("AFTER CLICK")

                self.page.wait_for_timeout(3000)

                print("URL:", self.page.url)

                self.page.wait_for_load_state(
                    "networkidle"
                )

                approve_btn = self.page.get_by_role(
                    "button",
                    name="Approve"
                )

                if approve_btn.is_visible():

                    print(
                        f"[APPROVE FOUND] Row {i}"
                    )

                    return True

                print(
                    f"[NOT APPROVE] Row {i}"
                )

                self.page.go_back()

                self.page.wait_for_load_state(
                    "networkidle"
                )

            except Exception as e:

                print(
                    f"[ROW {i} ERROR] {e}"
                )

                try:

                    self.page.go_back()

                    self.page.wait_for_load_state(
                        "networkidle"
                    )

                except Exception:
                    pass

        return False
    
    def show_100_candidates(self):

        pagination = self.page.get_by_role(
            "combobox"
        ).filter(
            has_text="10"
        ).first

        pagination.click()

        self.page.get_by_text(
            "100",
            exact=True
        ).click()

        self.page.wait_for_load_state(
            "networkidle"
        )

        self.page.wait_for_timeout(
            3000
        )

        print(
            "[PAGINATION CHANGED] Showing 100 candidates"
        )

    
    def show_all_candidates(self):

        page_size = self.page.locator(
            'button[role="combobox"]'
        ).last

        page_size.click()

        self.page.get_by_role(
            "option",
            name="100"
        ).click()

        self.page.wait_for_load_state(
            "networkidle"
        )

        self.page.wait_for_timeout(
            2000
        )

        print(
            "[PAGE SIZE SET] 100"
        )

    def open_candidate_by_index(self, index):

        rows = self.page.locator(
            "table tbody tr"
        )

        total = rows.count()

        print(
            f"[TODAY CANDIDATES FOUND] {total}"
        )

        if index >= total:

            raise Exception(
                f"Candidate index {index} not found"
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
    
    def get_today_candidate_count(self):

        rows = self.page.locator(
            "table tbody tr"
        )

        count = rows.count()

        print(
            f"[TODAY CANDIDATES] {count}"
        )

        return count

    
    def has_reopen_button(self):

        return self.page.get_by_role(
            "button",
            name="Reopen Request"
        ).count() > 0
    
    def find_candidate_with_action(
            self,
            action_name
    ):

        rows = self.page.locator(
            "table tbody tr"
        )

        total = rows.count()

        print(
            f"[SEARCHING {action_name.upper()}] "
            f"{total} candidates"
        )

        for i in range(total):

            try:

                rows = self.page.locator(
                    "table tbody tr"
                )

                row = rows.nth(i)

                print(
                    f"\nChecking Row {i}"
                )

                edit_btn = row.locator(
                    "button[title='Edit details']"
                )

                edit_btn.wait_for(
                    state="visible",
                    timeout=10000
                )

                print(
                    "Edit count:",
                    edit_btn.count()
                )
                print(
                    "Visible:",
                    edit_btn.is_visible()
                )
                print(
                    "Enabled:",
                    edit_btn.is_enabled()
                )

                edit_btn.scroll_into_view_if_needed()
                edit_btn.highlight()

                self.page.wait_for_timeout(
                    1000
                )

                print("BEFORE CLICK")

                edit_btn.click(
                    force=True
                )

                print("AFTER CLICK")

                self.page.wait_for_timeout(
                    2000
                )

                print(
                    "URL:",
                    self.page.url
                )

                target_btn = self.page.get_by_role(
                    "button",
                    name=action_name
                )

                if target_btn.is_visible():

                    print(
                        f"[{action_name.upper()} FOUND] "
                        f"Row {i}"
                    )

                    return True

                print(
                    f"[NOT {action_name.upper()}] "
                    f"Row {i}"
                )

                self.page.go_back()

                self.page.wait_for_timeout(
                    2000
                )

            except Exception as e:

                print(
                    f"[ROW {i} ERROR] {e}"
                )

                try:

                    self.page.go_back()

                    self.page.wait_for_timeout(
                        2000
                    )

                except Exception:
                    pass

        return False

    def reopen_employee(self):

        reopen_btn = self.page.get_by_role(
            "button",
            name="Reopen Request"
        )

        reopen_btn.wait_for(
            state="visible",
            timeout=10000
        )

        reopen_btn.click()

        print(
            "[REOPEN CLICKED]"
        )

        comment = (
            "Subham, please be attentive "
            "and fill accurate details"
        )

        textarea = self.page.locator(
            "#reopen-comment"
        )

        textarea.wait_for(
            state="visible",
            timeout=5000
        )

        textarea.fill(comment)

        print(
            f"[REOPEN COMMENT] {comment}"
        )

        with self.page.expect_response(
            lambda response:
                "/reopen" in response.url
                and response.status == 200
        ) as response_info:

            self.page.get_by_role(
                "button",
                name="Confirm Reopen"
            ).click()

        response = response_info.value

        payload = response.json()

        print(
            "\n===== REOPEN RESPONSE ====="
        )

        print(payload)

        assert payload["status"] == "success"

        assert payload["data"]["success"] is True

        return payload

    
    def reject_employee(self):

        reject_btn = self.page.get_by_role(
            "button",
            name="Reject"
        )

        reject_btn.wait_for(
            state="visible",
            timeout=10000
        )

        reject_btn.click()

        print(
            "[REJECT CLICKED]"
        )

        remarks = (
            "Subham, you are not a good developer, "
            "we have better options. Thank you for understanding."
        )

        textarea = self.page.locator(
            "textarea"
        )

        textarea.wait_for(
            state="visible",
            timeout=5000
        )

        textarea.fill(
            remarks
        )

        print(
            f"[REJECTION REMARKS] {remarks}"
        )

        with self.page.expect_response(
            lambda response:
                "/reject" in response.url
                and response.status == 200
        ) as response_info:

            self.page.get_by_role(
                "button",
                name="Confirm Reject"
            ).click()

        response = response_info.value

        payload = response.json()

        print(
            "\n===== REJECT RESPONSE ====="
        )

        print(payload)

        assert response.status == 200

        print(
            "[SUCCESS] Employee Rejected"
        )

        return payload

    # =====================================
    # OPEN TODAY'S CANDIDATE
    # =====================================

    def filter_today_candidates(self):

        today_filter = self.page.locator(
            'input[type="date"]'
        )

        today_filter.fill(
            datetime.now().strftime("%Y-%m-%d")
        )

        print(
            f"[FILTER APPLIED] "
            f"{datetime.now().strftime('%Y-%m-%d')}"
        )

        self.page.wait_for_load_state(
            "networkidle"
        )

        self.page.wait_for_timeout(
            2000
        )
    # =====================================
    # APPROVE EMPLOYEE
    # =====================================

    def approve_employee(self):

        self.page.wait_for_load_state(
            "networkidle"
        )

        approve_btn = self.page.get_by_role(
            "button",
            name="Approve"
        )

        approve_btn.wait_for(
            state="visible",
            timeout=10000
        )

        approve_btn.click()

        with self.page.expect_response(
            lambda response:
                "/approve" in response.url
                and response.status == 200
        ) as response_info:

            self.page.get_by_role(
                "button",
                name="Confirm Approve"
            ).click()

        response = response_info.value

        payload = response.json()

        print(
            "\n===== APPROVAL RESPONSE ====="
        )

        print(payload)

        assert payload["status"] == "success"

        assert payload["data"]["success"] is True

        print(
            "[SUCCESS] Employee Approved"
        )

        self.page.wait_for_load_state(
            "networkidle"
        )

        self.page.wait_for_timeout(
            2000
        )

        return payload

    # =====================================
    # HIRE EMPLOYEE
    # =====================================

    def hire_employee(self):

        hire_btn = self.page.get_by_role(
            "button",
            name="Hire"
        )

        hire_btn.wait_for(
            state="visible",
            timeout=10000
        )

        hire_btn.click()

        print(
            "[HIRE CLICKED]"
        )

        with self.page.expect_response(
            lambda response:
                "/hire" in response.url
                and response.status == 200
        ) as response_info:

            self.page.get_by_role(
                "button",
                name="Confirm Hire"
            ).click()

        response = response_info.value

        payload = response.json()

        print(
            "\n===== HIRE RESPONSE ====="
        )

        print(payload)

        assert response.status == 200

        print(
            "[SUCCESS] Employee Hired"
        )

        return payload