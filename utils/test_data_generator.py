from datetime import datetime
import random
import uuid


FIRST_NAMES = [
    "Aarav",
    "Vivaan",
    "Aditya",
    "Arjun",
    "Krishna",
    "Rahul",
    "Amit",
    "Rohan",
    "Vansh",
    "Karan",
    "Mohit",
    "Nikhil",
    "Siddharth",
    "Ankit",
    "Abhishek"
]

LAST_NAMES = [
    "Sharma",
    "Verma",
    "Patel",
    "Gupta",
    "Singh",
    "Mehta",
    "Joshi",
    "Kapoor",
    "Agarwal",
    "Malhotra"
]
JOB_DESIGNATIONS = [
    "Referral",
    "Direct",
    "Campus Placed",
   
]


def unique_job_offered():

    return random.choice(JOB_DESIGNATIONS)


def unique_email():

    return (
        f"automation_"
        f"{uuid.uuid4().hex[:12]}"
        f"@testmail.com"
    )


def unique_first_name():

    return random.choice(FIRST_NAMES)


def unique_last_name():

    return random.choice(LAST_NAMES)


def unique_employee_code():

    return (
        f"EMP"
        f"{datetime.now().strftime('%H%M%S%f')}"
    )

def unique_phone():

    return (
        f"9{random.randint(100000000,999999999)}"
    )

def unique_employee_code():

    return (
        f"EMP"
        f"{datetime.now().strftime('%H%M%S%f')}"
    )