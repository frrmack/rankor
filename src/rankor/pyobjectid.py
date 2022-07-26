# This is used to help Pydantic handle the bson ObjectId field from mongodb.
# You can find more discussion and examples around how to handle this issue
# at https://stackoverflow.com/questions/59503461/how-to-parse-objectid-in-a-pydantic-model


from bson import ObjectId as BsonObjectId
from pydantic import ValidationError
from pydantic.json import ENCODERS_BY_TYPE



class PyObjectId(BsonObjectId):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not BsonObjectId.is_valid(v):
            raise ValidationError("Not a valid bson object id")
        return PyObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


ENCODERS_BY_TYPE[PyObjectId] = str