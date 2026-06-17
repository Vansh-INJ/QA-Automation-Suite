import json
class Config:

    data = None

    @classmethod
    def load(cls):

        with open(
            "framework/config/qa.json"
        ) as file:

            cls.data = json.load(file)

    @classmethod
    def get(cls, key):

        return cls.data[key]