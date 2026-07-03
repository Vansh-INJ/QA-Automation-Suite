import random
import uuid
from datetime import datetime, timedelta

class OnboardingPayloads:

    @staticmethod
    def valid():
        """
        Generates a valid payload for onboarding submission.
        Follows the constraints and structure defined in the meta API.
        """
        return {
            "personal": {
                "gender": "male",
                "date_of_birth": (datetime.now() - timedelta(days=25*365)).strftime("%Y-%m-%d"),
                "blood_group": "A+",
                "profile_image": "dummy_profile_image_uuid.jpg"
            },
            "communication": {
                "primary_phone": f"98{random.randint(10000000, 99999999)}",
                "secondary_phone": f"97{random.randint(10000000, 99999999)}",
                "linkedin_url": "https://linkedin.com/in/testuser"
            },
            "bank": {
                "account_holder_name": "Test Candidate",
                "bank_name": "Test Bank",
                "branch": "Test Branch",
                "account_number": f"{random.randint(100000000, 999999999)}",
                "ifsc_code": "SBIN0001234"
            },
            "identity": {
                "aadhar": f"{random.randint(100000000000, 999999999999)}",
                "pan": "ABCDE1234F",
                "uan": f"{random.randint(100000000000, 999999999999)}"
            },
            "addresses": {
                "current": {
                    "line1": "123 Test Street",
                    "line2": "Test Area",
                    "country": "India",
                    "pin_code": "400001",
                    "state": "Maharashtra",
                    "city": "Mumbai"
                },
                "permanent": {
                    "same_as_current": True,
                    "line1": "123 Test Street",
                    "line2": "Test Area",
                    "country": "India",
                    "pin_code": "400001",
                    "state": "Maharashtra",
                    "city": "Mumbai"
                }
            },
            "family_members": [
                {
                    "relation": 1, # e.g. Father
                    "name": "Father Name",
                    "contact_number": f"96{random.randint(10000000, 99999999)}",
                    "is_emergency_contact": True
                }
            ],
            "education": [
                {
                    "college": "Test College",
                    "level": 1, # e.g. Bachelors
                    "course": "B.Tech",
                    "specialization": "Computer Science",
                    "passing_year": 2020
                }
            ],
            "documents": {
                "aadhar": str(uuid.uuid4()),
                "cancelled_cheque": str(uuid.uuid4()),
                "experience_certificate": str(uuid.uuid4()),
                "pan": str(uuid.uuid4()),
                "relieving_certificate": str(uuid.uuid4()),
                "resume": str(uuid.uuid4()),
                "x_marksheet": str(uuid.uuid4()),
                "xii_marksheet": str(uuid.uuid4())
            }
        }
