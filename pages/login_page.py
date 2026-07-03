from utils.logger import logger


class LoginPage:
    def __init__(self, page):
        self.page = page

    def open(self):
        """Navigate to the login page and click optional super admin button."""
        login_url = "https://injin.injtechnologies.com/login"
        # Navigate and wait until DOM is loaded
        self.page.goto(login_url, wait_until="domcontentloaded")
        # Ensure network is idle before interacting
        self.page.wait_for_load_state("networkidle")
        # Click "Fill Super Admin Credentials" if present
        try:
            self.page.get_by_role(
                "button",
                name="Fill Super Admin Credentials",
                exact=True
            ).click(timeout=5000)
        except Exception:
            logger.info("Super Admin Credentials button not found; proceeding.")

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
        # Wait for post‑login navigation to complete
        self.page.wait_for_load_state("networkidle")