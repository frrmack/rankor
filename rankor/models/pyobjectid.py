"""
Custom pydantic field data types PyObjectId and PyObjectIdString.

These data types help pydantic handle and validate the bson ObjectId field
assigned by mongodb -- it ensures both correct validation by pydantic and
correct string encoding into json. To understand why we are defining a
PyObjectId for pydantic to handle mongodb's bson object ids, check out the
following link:
https://stackoverflow.com/questions/59503461/how-to-parse-objectid-in-a-pydantic-model

If you're wondering why we are using the alias="_id" part when we are defining
id fields with this PyObjecId in the MongoModels, check out the following:
https://www.mongodb.com/community/forums/t/why-do-we-need-alias-id-in-pydantic-model-of-fastapi/170728/3
"""

# data type we want to build our custom Pydantic field types for
from bson import ObjectId as BsonObjectId

# pydantic's encoder directory (we want to tell pydantic how we want
# these object ids to be encoded)
from pydantic.json import ENCODERS_BY_TYPE


class BsonObjectIdValidator(object):
    '''
    Mixin class to add bson object id validation to a data type class,
    making it usable as a pydantic field type that expects a valid bson 
    object id in a pydantic schema
    '''

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not BsonObjectId.is_valid(value):
            raise ValueError("Not a valid bson ObjectId, it must be a 24 character hex string")
        return value

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class PyObjectId(BsonObjectId, BsonObjectIdValidator):
    """
    Custom pydantic field type for bson object ids. These are the _id
    fields used by mongodb as the unique identifiers of documents in the
    database. (It will be used for a field called "id" with an "_id" alias,
    since pydantic would automatically treat it as a private field if we 
    had directly called it "_id")
    """
    pass


class PyObjectIdString(str, BsonObjectIdValidator):
    """
    Custom pydantic field type for strings of bson object ids. The object
    ids themselves are binary objects, and should be referred to as PyObjectId.
    This class is used to denote fields that contain the hex value string of a
    bson object id. This is used for fields that contain a string reference
    to the id of a different document.
    """
    pass


# record which class to use when encoding bson object ids to json
ENCODERS_BY_TYPE[BsonObjectId] = PyObjectIdString
ENCODERS_BY_TYPE[PyObjectId] = PyObjectIdString