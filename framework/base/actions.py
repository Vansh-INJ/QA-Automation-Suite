class Actions:

    @staticmethod
    def click(locator, retries=3):

        for attempt in range(retries):
            try:
                locator.click()
                return

            except Exception:
                locator.page.wait_for_timeout(500)

        raise Exception("Click failed")

    @staticmethod
    def fill(locator, value):

        locator.click()
        locator.clear()
        locator.fill(str(value))