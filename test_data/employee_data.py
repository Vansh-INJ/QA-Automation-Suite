import random


def generate_phone():

    return f"9{random.randint(100000000, 999999999)}"


def generate_family_phone():

    return f"8{random.randint(100000000, 999999999)}"

PRIMARY_PHONE = generate_phone()
FAMILY_PHONE = generate_family_phone()

OFFER_DECLINE_DATA = {

    "test_case": "Offer_Decline",
    "first_name": "Subham",
    "middle_name": "Kumar",
    "last_name": "Negi",
    "job_offered": "Full Time",
    "department": "Information Technology",
    "employee_type": "Permanent",
    "company_entity": "INJ Technologies",
    "salary_structure": "Noida Salary Structure Main"

}

EMPLOYEE_PROFILES = [
    {
        "test_case": "Standard Employee",
        "middle_name": "K",        
        "job_offered": "Reference",
        "department": "Information Technology",
        "employee_type": "Full Time",
        "company_entity": "INJ Technologies",
        "salary_structure": "Noida Salary Structure Main",
    },
    {
        "test_case": "No Middle Name",
        "first_name": "Amit",
        "middle_name": "",
        "last_name": "Patel",
        "job_offered": "Engineering",
        "department": "Information Technology",
        "employee_type": "Part Time",
        "company_entity": "INJ Partners",
        "salary_structure": "Noida Salary Structure WO Bonus",
    },
    {
        "test_case": "Standard Employee",
        "first_name": "Vansh",
        "middle_name": "K",
        "last_name": "Sharma",
        "job_offered": "Reference",
        "department": "Information Technology",
        "employee_type": "Full Time",
        "company_entity": "INJ Technologies",
        "salary_structure": "Noida Salary Structure Main",
    },

    {
        "test_case": "No Middle Name",
        "first_name": "Amit",
        "middle_name": "",
        "last_name": "Patel",
        "job_offered": "Engineering",
        "department": "Information Technology",
        "employee_type": "Part Time",
        "company_entity": "INJ Partners",
        "salary_structure": "Noida Salary Structure WO Bonus",
    },

    {
        "test_case": "Contract Employee",
        "first_name": "Rahul",
        "middle_name": "K",
        "last_name": "Singh",
        "job_offered": "Engineering",
        "department": "Information Technology",
        "employee_type": "Contract",
        "company_entity": "INJ Technologies",
        "salary_structure": "Noida Salary Structure Main",
    },

    {
        "test_case": "Full Time Employee 2",
        "first_name": "Neha",
        "middle_name": "R",
        "last_name": "Gupta",
        "job_offered": "Reference",
        "department": "Information Technology",
        "employee_type": "Full Time",
        "company_entity": "INJ Partners",
        "salary_structure": "Noida Salary Structure WO Bonus",
    },

    {
        "test_case": "Part Time Employee 2",
        "first_name": "Priya",
        "middle_name": "",
        "last_name": "Verma",
        "job_offered": "Engineering",
        "department": "Information Technology",
        "employee_type": "Part Time",
        "company_entity": "INJ Technologies",
        "salary_structure": "Noida Salary Structure Main",
    },
]

TEST_PDF = "test_data/test_document.pdf"
PROFILE_IMAGE = "test_data/profile_picture.png"

CANDIDATE_DATA = {
    "gender": "Male",
    "dob": "1995-06-15",

    "email": "testcandidate@example.com",
    "phone": PRIMARY_PHONE,
    "family_contact": FAMILY_PHONE,

    "account_holder_name": "Test Candidate",
    "bank_name": "State Bank of India",
    "branch": "Bangalore Main",
    "account_number": "123456789012",
    "ifsc": "SBIN0001234",

    "aadhar": "123456789012",
    "pan": "ABCDE1234F",

    "address1": "123 Test Street",
    "address2": "Near City Mall",
    "city": "Bangalore",
    "pin": "560001",
    "state": "Karnataka",

    "relation": "Father",
    "family_name": "Test Father",

    "college": "Test Engineering College",
    "level": "Graduate",
    "course": "B.Tech",
    "specialization": "Computer Science",
    "passing_year": "2017",
}