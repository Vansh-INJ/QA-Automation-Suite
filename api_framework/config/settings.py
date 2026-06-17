import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    BASE_URL = os.getenv(
        "BASE_URL"
    )

    API_USERNAME = os.getenv(
        "API_USERNAME"
    )

    API_PASSWORD = os.getenv(
        "API_PASSWORD"
    )