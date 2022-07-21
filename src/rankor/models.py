# This is a Flask project, not a FastAPI project, but this
# single function from FastAPI is a great way to handle converting
# stuff between JSON and Python types (datetime, for example)
from fastapi.encoders import jsonable_encoder


# Pydantic provides data validation and creates a schema using typing,
# which is Python's own runtime support for type hints. This is good
# and necessary for a robust api. We import datetime to use as Python's 
# native datetime type in this pydantic schema creation.
from pydantic import BaseModel, Field, AnyUrl, Json
from typing import List, Optional, Union
from datetime import datetime


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
from src.rankor.pyobjectid import PyObjectId



class Thing(BaseModel):
    """ 
    We rank Things, by picking pairs of Things to have Fights, adjusting
    these Things' scores as a result of these Fights, then ranking them
    based on these scores. A Thing is the main element of Rankor, it's
    the thing we want to understand the ranking of among others of its kind.
    """
    id: Optional[PyObjectId] = Field(None, alias="_id")
    slug: str
    name: str
    image_url: Optional[AnyUrl]
    category: Optional[str]     # Future idea: Turn categories into a class? Also add a tag class?
    extra_data: Optional[Json]
    date_added: Optional[datetime]
    date_updated: Optional[datetime]

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        thing_contents = self.dict(by_alias=True, exclude_none=True)
        if thing_contents.get("_id") is None:
            thing_contents.pop("_id", None)
        return thing_contents



# class User(object):
#     # collections
#     # ranked_lists
#     pass

# class Collection(object):
#     pass

# class RankedList(object):
#     # user: User
#     # collection : Collection
#     # fights : list
#     # thing_scores: dict
#     pass

# class TierList(object):
#     # ranked_list
#     pass

# class Fight(object):
#     # thing_red_corner
#     # thing_blue_corner
#     # result
#     pass

# class Thing(object):
#     # name: str
#     # image: url = None
#     # other_fields: dict = None
#     pass



if __name__ == '__main__':
    t = Thing(name="The Terminator", 
              slug="the-terminator", 
              image_url="https://m.media-amazon.com/images/I/61qCgQZyhOL._AC_SY879_.jpg",
              extra_data = """{"director":"James Cameron", "year":1982}"""
             )
    print( t.to_json() )


    
