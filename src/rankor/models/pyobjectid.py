# This is a small piece of code to help pydantic handle the bson 
# ObjectId field assigned by mongodb -- it ensures both correct 
# validation by pydantic and correct string encoding into json.
# To understand why we are defining a PyObjectId for pydantic to
# handle mongodb's bson object ids, check out the following link:
# https://stackoverflow.com/questions/59503461/how-to-parse-objectid-in-a-pydantic-model
# If you're wondering why we are using this alias="_id" part when
# we are defining id fields with this PyObjecId in the models below,
# check out the following:
# https://www.mongodb.com/community/forums/t/why-do-we-need-alias-id-in-pydantic-model-of-fastapi/170728/3


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


class PyObjectIdString(str):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not cls.is_valid(value):
            raise ValueError("Not a valid bson object id")
        return cls(value)



ENCODERS_BY_TYPE[BsonObjectId] = PyObjectIdString
ENCODERS_BY_TYPE[PyObjectId] = PyObjectIdString