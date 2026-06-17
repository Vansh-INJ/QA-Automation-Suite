class Uploader:

    def upload(
            self,
            locator,
            file_path
    ):
        locator.set_input_files(
            file_path
        )