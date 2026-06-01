class BasePage:

    def __init__(self, page):
        self.page = page

    def click(self, locator):
        self.page.locator(locator).click()

    def fill(self, locator, value):
        self.page.locator(locator).fill(value)

    def wait(self, ms=1000):
        self.page.wait_for_timeout(ms)