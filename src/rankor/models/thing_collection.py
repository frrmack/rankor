# THIS MODEL IS CURRENTLY UNUSED

# Data types and typing hints for the pydantic schema
from typing import List

# Rankor superclass for models, handling encodings and bson ObjectIds
from rankor.models.mongo_model import MongoModel

# This is used to help Pydantic handle the bson ObjectId field from mongodb
# More info in the module itself
from src.rankor.models.pyobjectid import PyObjectId


class ThingCollection(MongoModel):
    """
    A ThingCollection is a set of things. The data of each instance is basically
    a list of Thing ids. This allows us to form different collections to
    make ranked lists about. For example, the database might have a ton of
    movies saved as Things, but you may want to create a subset of them,
    let's say Action movies made after 2010s for example, you would make a 
    ThingCollection that encapsulates only the Things that meet this criterion,
    and you can make a lot of pairwise comparisons (Fights) just among them to 
    get a ranked list like 'My favorite action movies of the last decade'.
    """
    name: str
    things: List[PyObjectId]
