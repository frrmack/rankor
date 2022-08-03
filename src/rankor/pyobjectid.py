# This is used to help Pydantic handle the bson ObjectId field from mongodb.
# You can find more discussion and examples around how to handle this issue
# at https://stackoverflow.com/questions/59503461/how-to-parse-objectid-in-a-pydantic-model


from bson import ObjectId as BsonObjectId
from pydantic.json import ENCODERS_BY_TYPE



class PyObjectId(BsonObjectId):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not cls.is_valid(value):
            raise ValueError("Not a valid bson object id")
        return cls(value)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


ENCODERS_BY_TYPE[BsonObjectId] = str
ENCODERS_BY_TYPE[PyObjectId] = str