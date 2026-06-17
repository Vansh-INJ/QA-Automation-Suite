class NetworkCapture:

    def __init__(self):
        self.responses = []

    def attach(self, page):

        page.on(
            "response",
            self.capture
        )

    def capture(self, response):

        self.responses.append(
            {
                "status": response.status,
                "url": response.url
            }
        )