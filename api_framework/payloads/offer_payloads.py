from faker import Faker

fake = Faker()


class OfferPayloads:

    @staticmethod
    def valid():

        return {

            "first_name":
                fake.first_name(),

            "middle_name":
                "",

            "last_name":
                fake.last_name(),

            "email":
                fake.email(),

            "employment_type":
                "Contract",

            "job_offered":
                "direct",

            "gross_monthly_salary":
                10000,

            "function_id":
                "42c5444f-838b-4abd-a4d1-9255022ddd48",

            "sub_function_id":
                "b95ffda6-fe48-4064-863e-9e342c69cd3b",

            "job_title_id":
                "3a1bfd7b-3a03-456f-86d1-76309e018d43",

            "legal_entity_id":
                "3bff1655-5f59-414e-aedc-4878dda1faea",

            "work_location_id":
                "fa2b82cd-6a21-4ab4-a547-c675c7eeb114",

            "reporting_manager_uuid":
                "ba2b7c16-5016-4df6-b41a-fc14e84adc6d",

            "hierarchy_level_uuid":
                "a20b28f1-64a0-41bb-88b2-c803cddb206f",

            "salary_structure_uuid":
                "cc306bda-4b7f-4408-920c-3871db9f7579",

            "proposed_joining_date":
                "2026-06-23",

            "variable_components": {
                "INSURANCE": 600,
                "INCENTIVE": 6000
            }
        }