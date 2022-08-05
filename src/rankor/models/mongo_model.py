# This is a Flask project, not a FastAPI project, but this
# single function from FastAPI is a great way to handle converting
# stuff between JSON and Python types (datetime, for example)
from fastapi.encoders import jsonable_encoder


# Pydantic provides data validation and creates a schema using typing,
# which is Python's own runtime support for type hints. This is good
# and necessary for a robust api. 
from pydantic import BaseModel, Field
from typing import Optional


# This is used to help Pydantic handle the bson ObjectId field from mongodb.
# You can find more discussion and examples around how to handle this issue
# at https://stackoverflow.com/questions/59503461/how-to-parse-objectid-in-a-pydantic-model
# and more notes in rankor's pyobjectid.py as well
from src.rankor.models.pyobjectid import PyObjectId



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
    
    We are using Pydantic to have strict data validation, and what we do below
    (creating a custom field with an ObjectId type) method ensures that Pydantic 
    validates  this _id field correctly as a bson object id type. This field
    is Optional, because WE don't want to create an id when we create a model instance.
    We want id creation to happen automatically by mongo. When we convert this python
    model object instance to bson as part of writing it to mongo (pymongo converts a 
    python dict representing this model instance into a bson when we tell it to store 
    it in the database), it won't have an _id field so that mongo can create it itself. 
    But if we read / rewrite / etc. a model object that had already been written to 
    mongo once (and therefore it already has an id with the alias "_id"), it will stay
    on, and will still be validated as the correct ObjectId type. 
    
    The json and bson encoders are just convenience functions to ensure correct 
    serialization with these strict typing schemas. bson supports native ObjectId and 
    datetime types, but the json encoder converts ObjectId to a string with its hex value,
    and datetime into an ISO8601 string.
    """
    id: Optional[PyObjectId] = Field(None, alias="_id")

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        return self.dict(by_alias=True, exclude_none=True)
