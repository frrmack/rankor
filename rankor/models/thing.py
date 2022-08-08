# Data types and type hints for the pydantic schema
from pydantic import AnyUrl
from typing import Optional, Dict
from datetime import datetime

# Rankor superclass for models, handling encodings and bson ObjectIds
from rankor.models.mongo_model import MongoModel


class Thing(MongoModel):
    """ 
    We rank Things, by picking pairs of Things to have Fights, adjusting
    these Things' scores as a result of these Fights, then ranking them
    based on these scores. A Thing is the main element of Rankor, it's
    the thing we want to understand the ranking of among others of its kind.
    """
    name: str
    image_url: Optional[AnyUrl]
    category: Optional[str]        # Make new models: Category, Tag
    other_data: Optional[Dict]
    time_created: Optional[datetime]
    time_edited: Optional[datetime]
