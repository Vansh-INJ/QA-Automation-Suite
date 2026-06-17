from playwright.sync_api import expect


class Assertions:

    @staticmethod
    def visible(locator):
        expect(locator).to_be_visible()

    @staticmethod
    def contains(locator, text):
        expect(locator).to_contain_text(text)

    @staticmethod
    def enabled(locator):
        expect(locator).to_be_enabled()

    @staticmethod
    def disabled(locator):
        expect(locator).to_be_disabled()