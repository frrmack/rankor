# Pydantic provides data validation and creates a schema using typing,
# which is Python's own runtime support for type hints. This is good
# and necessary for a robust api. 
from pydantic import BaseModel, Field
from typing import Optional

# JSON encoding
import json

# This is used to help Pydantic handle the bson ObjectId field from mongodb.
# You can find more discussion and examples around how to handle this issue
# at https://stackoverflow.com/questions/59503461/how-to-parse-objectid-in-a-pydantic-model
# and more notes in rankor's pyobjectid.py as well
from rankor.models.pyobjectid import PyObjectId


class MongoModel(BaseModel):
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
    
    The to_json, to_jsonable_dict and to_bsonable_dict methods are just for
    convenience to ensure correct serialization with these strict typing
    schemas. For example, bson supports native ObjectId and datetime types, so
    to_bsonable_dict method returns a dict representation with those types, but
    to_jsonable_dict method converts an ObjectId into an str of its hex string
    value, and it converts a datetime object into an ISO8601 string. Both
    to_jsonable_dict and to_bsonable_dict methods return dicts with the relevant
    json or bson encodings, and to_json returns an actual json string of the
    jsonable_dict. 
    """
    id: Optional[PyObjectId] = Field(None, alias="_id")


    def to_json(self):
        """
        A simple wrapper around BaseModel.json() with a few keyword arguments
        already set as the default json serialization behavior of MongoModel. It
        uses pydantic's json encoder, it looks at pydantic.json.ENCODERS_BY_TYPE
        to figure out how to encode non-standard types. 
        
        It excludes fields that are None from the json result by default (this
        includes optional fields that aren't set), and pretty-print-ifies the
        json with sorted keys and indents for readability.
        """
        return self.json(exclude_none=True, indent=2, sort_keys=True)


    def to_jsonable_dict(self):
        """
        Encodes complex classes in relevant serialization types just as the
        to_json() method (such as converting datetime objects to isoformat
        timestamp strings, for example), but returns a dict representation with
        these json-able contents instead of a json string. This is handy when
        you need the encoding but want to keep a dict, for example when you need
        to include it in another dict which will be encoded to json in its
        entirety. It excludes fields set to None (this includes Optional fields
        that were never set).
        
        While re-parsing a json dumped from a dict by BaseModel.json is slightly
        ridiculous, pydantic.json.pydantic_encoder, pydantic.BaseModel.json, and
        pydantic.BaseModel.dict are written in a way that this functionality is
        a bit difficult to ensure without writing a custom json encoder or using
        an existing external one (such as fastapi.encoders.jsonable_encoder),
        and it's simpler and more straightforward to just do this instead. The
        performance difference is absolutely negligible for rankor's use cases. 
        
        This lacking feature (a jsonable encoder returning a dict) has actually
        been proposed for pydantic, and it's favored by Samuel Colvin
        (pydantic's author). You can read more about it here:
        https://github.com/samuelcolvin/pydantic/issues/951#issuecomment-552463606
        """
        return json.loads(self.to_json())


    def to_bsonable_dictable_dict(self):
        """
        A simple wrapper around BaseModel.dict(). It has by_alias set to True,
        which is very important, as we want the 'id' field of a MongoModel to be
        recorded by its alias '_id' in a bson document to be written to mongodb.
        There is more info on this in rankor/models/pyobjectid.py, but basically
        we are avoiding calling the field '_id' directly to avoid pydantic
        treating it as a private field. We get around this by calling it 'id'
        and using the alias '_id' for it. 
        
        Like to_jsonable_dict, this also excludes fields that are set to None
        from the model's representation (this includes optional fields that are
        not set). This returns a dict, not a bson, but it's a dict with the
        desired data types for conversion to bson. Pymongo will convert it to
        bson before writing it to the mongodb database.
        """
        return self.dict(by_alias=True, exclude_none=True)

