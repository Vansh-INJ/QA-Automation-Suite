class Dropdown:

    def __init__(self, page):
        self.page = page

    def select(self, trigger, option):

        trigger.click()

        self.page.get_by_role(
            "option",
            name=option
        ).click()