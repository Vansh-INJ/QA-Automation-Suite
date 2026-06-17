
from framework.base.assertions import Assertions
from framework.base.assertions import Actions
from framework.base.base import Waits


class EnhancedPage:

    def __init__(self, page):
        self.page = page
        self.waits = Waits()
        self.actions = Actions()
        self.assertions = Assertions()