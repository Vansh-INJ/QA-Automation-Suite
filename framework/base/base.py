from playwright.sync_api import expect


class Waits:

    @staticmethod
    def visible(locator):
        expect(locator).to_be_visible()

    @staticmethod
    def hidden(locator):
        expect(locator).not_to_be_visible()

    @staticmethod
    def enabled(locator):
        expect(locator).to_be_enabled()

    @staticmethod
    def text(locator, text):
        expect(locator).to_have_text(text)