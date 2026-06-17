import os
from dotenv import load_dotenv

load_dotenv()


class Settings:

    BASE_URL = os.getenv("BASE_URL")

    API_USERNAME = os.getenv("API_USERNAME")
    API_PASSWORD = os.getenv("API_PASSWORD")

    FUNCTION_ID = os.getenv("FUNCTION_ID")
    SUB_FUNCTION_ID = os.getenv("SUB_FUNCTION_ID")
    JOB_TITLE_ID = os.getenv("JOB_TITLE_ID")
    LEGAL_ENTITY_ID = os.getenv("LEGAL_ENTITY_ID")
    WORK_LOCATION_ID = os.getenv("WORK_LOCATION_ID")
    REPORTING_MANAGER_UUID = os.getenv("REPORTING_MANAGER_UUID")
    HIERARCHY_LEVEL_UUID = os.getenv("HIERARCHY_LEVEL_UUID")
    SALARY_STRUCTURE_UUID = os.getenv("SALARY_STRUCTURE_UUID")