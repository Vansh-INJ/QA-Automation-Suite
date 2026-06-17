class ResponseValidator:

    @staticmethod
    def has_keys(
            body,
            keys
    ):
        for key in keys:

            assert (
                key in body
            ), (
                f"Missing key: {key}"
            )