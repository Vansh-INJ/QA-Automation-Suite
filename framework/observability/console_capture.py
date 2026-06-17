class ConsoleCapture:

    def __init__(self):
        self.logs = []

    def attach(self, page):

        page.on(
            "console",
            lambda msg:
            self.logs.append(
                msg.text
            )
        )