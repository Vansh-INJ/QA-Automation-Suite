class Table:

    def __init__(self, page):
        self.page = page

    def rows(self, locator):
        return self.page.locator(locator)

    def count(self, locator):
        return self.rows(locator).count()