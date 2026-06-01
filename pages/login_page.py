class LoginPage:

    def __init__(self, page):

        self.page = page

    def open(self):

        self.page.goto(
            "https://injin.injtechnologies.com/login"
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