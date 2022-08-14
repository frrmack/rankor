# Typing hint import
# This allows us to define an optional field in a pydantic schema
from typing import Optional

# Model template import
# Instances of this model are not stored in the database. They are put together
# based on the thing to score mapping saved in RankedList documents in the
# database. There is no ranked_things collection in the database. Therefore,
# they do not have a database id, and they don't inherit from MongoModel, but 
# simply from JsonableModel.
from rankor.models.jsonable_model import JsonableModel

# Model imports
# Thing is the model for what we are ranking
# Score is the model that contains all the score information for a Thing.
from rankor.models.thing import Thing
from rankor.models.score import Score

# Field import
# PyObjectIdString is a field that contains the hex string of a bson object id.
# It is used to store the id string of another model document (in this case, the
# id of a Thing). There's more info in the pyobjectid module itself.
from rankor.models.pyobjectid import PyObjectIdString


class RankedThing(JsonableModel):
    """
    A RankedThing instance represents where a Thing stands in terms of rankings
    within a RankedList.

    As Things are compared in Fights within the context of a given RankedList,
    their Scores are updated based on the Fight results. Every RankedList has a
    dict that maps each Thing to its Score. These scores allow the Things to be
    ranked, earning the RankedList its name. A Thing has only one Score per each
    RankedList it participates in, and each RankedList has only one Score for
    each Thing participating in it. When a RankedList is asked to provide
    rankings, it uses this model to report on what the rank and score of each
    Thing in it happens to be.

    The RankedList.ranked_things property of a RankedList instance provides a
    (sorted) list of RankedThing objects. This is how you see the full rankings.

    Note that it can either hold just the id of a thing, or the entire Thing
    itself, for different use cases. (It can also hold both or neither, but those are much rarer use cases) Any endpoint code that needs to report RankedThings can pull the
    actual Thing data from the database using these ids.
    """
    rank: int
    score: Score
    thing_id: Optional[PyObjectIdString]
    thing: Optional[Thing]

