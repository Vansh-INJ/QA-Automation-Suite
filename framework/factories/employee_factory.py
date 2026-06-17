from faker import Faker

fake = Faker()


class EmployeeFactory:

    @staticmethod
    def standard():

        return {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "department": "Information Technology"
        }