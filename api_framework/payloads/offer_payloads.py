# api_framework/payloads/offer_payloads.py

from faker import Faker
from datetime import datetime, timedelta
import random

from api_framework.config.settings import Settings

fake = Faker()


class OfferPayloads:

    @staticmethod
    def valid():

        # =====================================
        # Dynamic future joining date
        # Always generates 3-15 days in future
        # =====================================
        joining_date = (
            datetime.today()
            + timedelta(days=random.randint(3, 15))
        ).strftime("%Y-%m-%d")

        # =====================================
        # Dynamic unique email
        # =====================================
        email = (
            f"test{random.randint(10000, 99999)}"
            f"@injpartners.com"
        )

        return {

            # =====================================
            # Candidate Details
            # =====================================
            "first_name": fake.first_name(),
            "middle_name": "",
            "last_name": fake.last_name(),
            "email": email,

            # =====================================
            # Employment Details
            # =====================================
            "employment_type": "Contract",
            "job_offered": "direct",
            "gross_monthly_salary": random.randint(
                10000,
                50000
            ),

            # =====================================
            # Master IDs
            # Replace these with your VALID IDs
            # =====================================
            "function_id": Settings.FUNCTION_ID,
            "sub_function_id": Settings.SUB_FUNCTION_ID,
            "job_title_id": Settings.JOB_TITLE_ID,
            "legal_entity_id": Settings.LEGAL_ENTITY_ID,
            "work_location_id": Settings.WORK_LOCATION_ID,
            "reporting_manager_uuid": Settings.REPORTING_MANAGER_UUID,
            "hierarchy_level_uuid": Settings.HIERARCHY_LEVEL_UUID,
            "salary_structure_uuid": Settings.SALARY_STRUCTURE_UUID,

            # =====================================
            # Dynamic future date
            # =====================================
            "proposed_joining_date":
                joining_date,

            # =====================================
            # Variable Components
            # =====================================
            "variable_components": {
                "INSURANCE": random.randint(
                    500,
                    5000
                ),
                "INCENTIVE": random.randint(
                    1000,
                    10000
                )
            }
        }