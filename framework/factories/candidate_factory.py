from faker import Faker

fake = Faker()


class CandidateFactory:

    @staticmethod
    def onboarding():

        return {
            "phone": fake.phone_number(),
            "city": fake.city(),
            "address": fake.address()
        }