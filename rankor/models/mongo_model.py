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
    
    Why are we using this _id alias thing? (because otherwise Pydantic will treat
    an underscored field name to be a private field):
    https://www.mongodb.com/community/forums/t/why-do-we-need-alias-id-in-pydantic-model-of-fastapi/170728

    Every mongodb object needs to have an _id field. If you store an object in
    a mongodb collection, mongo will automatically create a bson object id and
    assign it to this object during the write, and will save it under the "_id"
    field.
    
    We are using Pydantic to have strict data validation, and what we do 
    below (creating a custom field with an ObjectId type) method ensures that 
    Pydantic validates  this _id field correctly as a bson object id type. 
    This field is Optional, because WE don't want to create an id when we 
    create a model instance. We want id creation to happen automatically by 
    mongodb. When we convert this python model instance to bson as part of 
    writing it to mongo (pymongo converts a python dict representing this 
    model instance into a bson when we tell it to store it in the database), 
    it won't have an _id field so that mongo can create it itself. But if we 
    read / rewrite / etc. a model object that had already been written to 
    mongodb once (and therefore it already has an id with the alias "_id"), it 
    will stay on, and will still be validated as the correct ObjectId type. 
    
    The to_json and to_bson methods are just for convenience to ensure correct 
    serialization with these strict typing schemas. For example, bson supports 
    native ObjectId and datetime types, but the json encoder converts ObjectId 
    to a string with its hex value, and datetime into an ISO8601 string. The 
    jsonable_dict method provides the same json encoding as to_json, but keeps 
    the result as a dict instead of the final string. 
    """
    id: Optional[PyObjectId] = Field(None, alias="_id")


    def to_json(self):
        """
        A simple wrapper around BaseModel.json() with a few keyword arguments 
        already set as the default json serialization behavior of MongoModel. 
        It excludes fields that are None from the json result by default (this
        includes optional fields that aren't set), and pretty-print-ifies the 
        json with sorted keys and indents for readability.
        """
        return self.json(exclude_none=True, indent=2, sort_keys=True)


    def jsonable_dict(self):
        """
        Encodes complex classes in relevant serialization types just as the 
        to_json() method, but return a dict representation with these 
        json-able contents instead of a json string. This is handy when you
        need the encoding but want to keep a dict, for example when you need
        to include it in another dict which will be encoded to json in its
        entirety. 
        While re-parsing a json dumped by BaseModel.json is slightly ridiculous, 
        pydantic.json.pydantic_encoder, pydantic.BaseModel.json, and 
        pydantic.BaseModel.dict are written in a way that this functionality
        is a bit difficult to ensure without writing a custom json encoder or 
        using an existing one (such as fastapi.encoders.jsonable_encoder), and
        it's simpler and more straightforward to just do this instead. The 
        performance difference is absolutely negligible for rankor's use cases.
        """
        return json.loads(self.to_json())


    def to_bson(self):
        """
        A simple wrapper around BaseModel.dict(). It has by_alias set to True, 
        which is very important, as we want the 'id' field of a MongoModel to 
        be recorded by its alias '_id' in a bson document to be written to 
        mongodb. There is more info on this in rankor/models/pyobjectid.py, 
        but basically we are avoiding calling the field '_id' directly to 
        avoid pydantic treating it as a private field. We get around this 
        by calling it 'id' and using the alias '_id' for it. Like to_json(),
        this also excludes fields that are set to None from the model's
        representation (including optional fields that are not set).
        """
        return self.dict(by_alias=True, exclude_none=True)

