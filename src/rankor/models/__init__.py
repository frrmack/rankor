"""
The data models used by rankor built with pydantic.

Pydantic provides data validation and creates a schema using typing,
which is Python's own runtime support for type hints. This is good
and necessary for a robust api. 
"""

# Import the main models from their respective files, so the rest of rankor can
# import them directly from rankor.models (Note that models.ranked_thing imports
# Thing and Score, models.ranked_list imports Score and RankedThing)
from rankor.models.jsonable_model import JsonableModel
from rankor.models.mongo_model import MongoModel
from rankor.models.thing import Thing
from rankor.models.fight import Fight, ProposedFight
from rankor.models.score import Score
from rankor.models.ranked_thing import RankedThing
from rankor.models.ranked_list import RankedList


# Import the ObjectId-related pydantic fields so they can be imported
# directly from rankor.models
from rankor.models.pyobjectid import PyObjectId, PyObjectIdString
