from utils.logger import logger


class LoginPage:
    def __init__(self, page):
        self.page = page

    def open(self):
        """Navigate to the login page."""
        login_url = "https://injin.injtechnologies.com/login"
        self.page.goto(login_url, wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")

    def fill_username(self, username: str):
        """Click and type into the username/employee ID field."""
        username_field = self.page.locator("#username")
        username_field.click()
        username_field.fill(username)

    def fill_password(self, password: str):
        """Click and type into the password field."""
        password_field = self.page.locator("#password")
        password_field.click()
        password_field.fill(password)

    def fill_credentials(self, username: str, password: str):
        """Fill both username and password fields."""
        self.fill_username(username)
        self.fill_password(password)

    def click_login(self):
        self.page.get_by_role(
            "button",
            name="Sign In",
            exact=True
        ).click()

    def login(self, username: str = "EMP001", password: str = "Password@123"):
        """Full login flow: fill credentials and submit."""
        self.fill_credentials(username, password)
        self.page.wait_for_timeout(500)
        self.click_login()
        # Wait for post-login navigation to complete
        self.page.wait_for_load_state("networkidle")

    def login_as_super_admin(self, username: str = "EMP001", password: str = "Password@123"):
        """Deprecated alias for login(). Kept for backward compatibility with existing tests."""
        self.login(username, password)