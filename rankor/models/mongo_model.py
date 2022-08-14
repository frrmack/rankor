# Pydantic provides data validation and creates a schema using typing, which is
# Python's own runtime support for type hints. This is good and necessary for a
# robust api. Here we are importing Field to design a custom pydantic Field for
# the id.
from pydantic import Field
from typing import Optional

# Jsonable is the granddaddy of all rankor models, it provides the necessary
# json encoding methods.
from rankor.models.jsonable_model import JsonableModel

# This is used to help Pydantic handle the bson ObjectId field from mongodb.
# You can find more discussion and examples around how to handle this issue
# at https://stackoverflow.com/questions/59503461/how-to-parse-objectid-in-a-pydantic-model
# and more notes in rankor's pyobjectid.py as well
from rankor.models.pyobjectid import PyObjectId


class MongoModel(JsonableModel):
    """
    Parent class for most Rankor models to inherit. It handles the bson object
    id stuff assigned by mongodb as an optional id field with an alias "_id".
    
    Why are we using this _id alias thing? (because otherwise Pydantic will
    treat an underscored field name to be a private field):
    https://www.mongodb.com/community/forums/t/why-do-we-need-alias-id-in-pydantic-model-of-fastapi/170728

    Every mongodb object needs to have an _id field. If you store an object in a
    mongodb collection, mongo will automatically create a bson object id and
    assign it to this object during the write, and will save it under the "_id"
    field.
    
    We are using Pydantic to have strict data validation, and what we do below
    (creating a custom field with an ObjectId type) ensures that Pydantic
    validates  this _id field correctly as a bson object id type. This field is
    Optional, because WE don't want to create an id when we create a model
    instance. We want id creation to happen automatically by mongodb. When we
    convert this python model instance to bson as part of writing it to mongodb
    (pymongo converts a python dict representing this model instance into a bson
    when we tell it to store it in the database), it won't have an _id field so
    that mongodb can create it itself. But if we read / rewrite / revalidate a
    model object that had already been written to mongodb once (and therefore it
    already has an id with the alias "_id"), it will stay on, and will still be
    validated as the correct ObjectId type. 
    
    The to_bsonable_dict() method is a counterpart to
    JsonableModel.to_jsonable_dict(). Just as to_jsonable_dict() creates a dict
    represenation of the model ready to be converted into json,
    to_bsonable_dict() creates a dict representation of the model ready to be
    converted to a bson document to store in the mongodb. This ensure correct
    serialization with these strict typing schemas. For example, bson supports
    native ObjectId and datetime types, so to_bsonable_dict method returns a
    dict representation with those types, but to_jsonable_dict method converts
    an ObjectId into an str of its hex string value, and it converts a datetime
    object into an ISO8601 string. In addition, to_bsonable_dict() also handles
    the id field on both the pydantic model and mongodb bson document sides.
    """

    id: Optional[PyObjectId] = Field(None, alias="_id")


    def to_bsonable_dict(self, *args, **kwargs):
        """
        Returns a python dict representation of the model, which includes
        complex python types that pymongo's bson conversion can handle.
        
        This is in contrast to (inherited) JsonableModel.to_jsonable_dict(),
        which converts such complex data types into json-friendly basic types.
        The json encoding relies on pydantic's encoder, and the bson conversion
        is handled by pymongo. The data types used in these two cases, differ,
        though. For example, pymongo accepts native ObjectId and datetime
        types (which it encodes as bson types oid and date), so
        to_bsonable_dict() returns a dict representation with those python
        types, whereas to_jsonable_dict() encodes an 'ObjectId' as its hex
        string ('str'), and it encodes a 'datetime' object as an ISO8601
        timestamp string ('str').

        It's a simple wrapper around the dict() method. It has by_alias set to
        True, which is very important, as we want the 'id' field of a MongoModel
        to be recorded by its alias '_id' in a bson document to be written to
        mongodb. "_id" is the special bson object field name that mongodb uses
        as the identifier of a document in the database. There is more info and
        links on this in rankor/models/pyobjectid.py, but basically we don't
        directly call the model's field '_id' to avoid pydantic treating it as a
        private field and hiding it. We get around this by calling it 'id' and
        using the alias '_id' for it. 
        
        Like JsonableModel.to_jsonable_dict, this also excludes fields that are
        set to None from the model's representation, since it inherits
        JsonableModel's dict() method, which has exclude_none keyword set to
        True by default. This returns a dict, not a bson, but it's a dict with
        the desired data types for conversion to bson. Pymongo will convert it
        to bson before writing it to the mongodb database.

        More info on pymongo's bson encoding:
        https://pymongo.readthedocs.io/en/stable/api/bson/index.html#module-bson
        """
        return self.dict(*args, by_alias=True, **kwargs)
