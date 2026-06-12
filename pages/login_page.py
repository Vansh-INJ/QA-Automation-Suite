class LoginPage:

    def __init__(self, page):

        self.page = page

    def open(self):

        login_url = "https://injin.injtechnologies.com/login"

        self.page.goto(
            login_url,
            wait_until="domcontentloaded"
        )

        for attempt in range(10):

            try:

                self.page.get_by_role(
                    "button",
                    name="Fill Super Admin Credentials",
                    exact=True
                ).wait_for(
                    state="visible",
                    timeout=3000
                )

                return

            except Exception:   

                self.page.reload(
                    wait_until="domcontentloaded"
                )

                self.page.wait_for_timeout(2000)

        raise Exception(
            "Login page failed to load after 10 refresh attempts"
        )

    def fill_super_admin_credentials(self):

        self.page.get_by_role(
            "button",
            name="Fill Super Admin Credentials",
            exact=True
        ).click()

    def click_login(self):

        self.page.get_by_role(
            "button",
            name="Login",
            exact=True
        ).click()

    def login_as_super_admin(self):

        self.fill_super_admin_credentials()

        self.page.wait_for_timeout(1000)

        self.click_login()

        self.page.wait_for_load_state("networkidle")