# This is a Flask project, not a FastAPI project, but this
# single function from FastAPI is a great way to handle converting
# stuff between JSON and Python types (datetime, for example)
from fastapi.encoders import jsonable_encoder


# Pydantic provides data validation and creates a schema using typing,
# which is Python's own runtime support for type hints. This is good
# and necessary for a robust api. We import datetime to use as Python's 
# native datetime type in this pydantic schema creation.
from pydantic import BaseModel, Field, AnyUrl, Json, conlist
from typing import List, Dict, Literal, Optional, Union
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


class MongoModel(BaseModel):
    """
    Parent class for all Rankor models to inherit. It handles the bson object
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


class Thing(MongoModel):
    """ 
    We rank Things, by picking pairs of Things to have Fights, adjusting
    these Things' scores as a result of these Fights, then ranking them
    based on these scores. A Thing is the main element of Rankor, it's
    the thing we want to understand the ranking of among others of its kind.
    """
    slug: str
    name: str
    image_url: Optional[AnyUrl]
    category: Optional[str]     # Future idea: Turn categories into a class? Also add a tag class?
    extra_data: Optional[Json]
    date_added: Optional[datetime]
    date_updated: Optional[datetime]



class Fight(MongoModel):
    """
    Ranking is done by pairwise comparisons. A Fight is a pairwise comparison.
    Each Fight depicts a comparison of two Things. It keeps information about 
    what the two compared Things were, and what the result was. If there is
    a winner (not a draw), the winner's id is also saved as a convenience to
    the application(s) on top of this api. The time of the fight is kept as well.
    Available results are "FIRST_THING_WINS" (winner is the first element of
    the fighting_things list which is a list with two items), "SECOND_THING_WINS" 
    (winner is the last element of fighting_things) or "DRAW" (a tie).
    There may be multiple Fights between two things. One such usecase: a user keeps 
    doing comparisons at different times, and the same couple comes up for comparison
    multiple times -- the result may be the same every time, or maybe different based 
    on their mood and thinking at different times. Another usecase: multiple users are
    voting on Fights within the same RankedList, and different users have
    different opinions on which Thing is better, hence different results in multiple
    Fights between the same pair of Things.
    Think of a Fight as a chess game between two players. The same players may play 
    multiple games and get different results, even if one is a stronger player. The 
    stronger player will likely win more of the Fights, but not necessarily all, and 
    they may even lose the majority just by random chance -- even if that's less likely.
    """
    fighting_things: conlist(PyObjectId, min_items=2, max_items=2) 
    result: Literal['FIRST_THING_WINS', 'SECOND_THING_WINS', 'DRAW']
    winner: Optional[PyObjectId]
    date_fought: Optional[datetime]



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



class RankedList(MongoModel):
    """
    A RankedList is a set of Things, each associated with a score. (It's called 
    a ranked list because we can use those scores to rank them.) When we start 
    a RankedList, we pick a ThingCollection. We assign a default starting score
    to each Thing in this ThingCollection, and we now have a set of things with 
    scores. Of course, at this point all the scores are the same, which does not 
    give us a meaningful ranking. We then start having some Fights among these
    Things, which update the scores of the Things that have fought, and this way
    the scores start differentiating, we start getting a more meaningful ranking.
    This model knows which ThingCollection the Things came from, the mapping of 
    Things to scores, and the associated Fights that gave rise to those scores.
    """
    collection: PyObjectId             # The sourcing ThingCollection
    thing_scores: Dict[PyObjectId, float]
    fights: List[PyObjectId]



# class User(object):
#     # collections
#     # ranked_lists
#     # fights
#     # things
#     pass



if __name__ == '__main__':
    
    # Note: normally, we would not create these instances by assigning them _id
    # values ourselves. Instead of creating them with written _id fields, we'd let _ids be
    # automatically assigned by mongo when pymongo writes them to the db. We are only
    # explicitly defining _id fields ourselves here, so that we know the _id values already
    # to test other models that reference these stuff. It's just so we can run some basic
    # tests to ensure the code works as intended, without having to write to and read from
    # the database, just to get _ids assigned.

    terminator_thing = Thing(name = "The Terminator", 
                             slug = "the-terminator", 
                             jess = "yay",
                             image_url = "https://m.media-amazon.com/images/I/61qCgQZyhOL._AC_SY879_.jpg",
                             extra_data = """{"director":"James Cameron", "year":1982}""",
                             _id = PyObjectId("12345678901234567890abcd")
                            )
    aliens_thing = Thing(name = "Aliens",
                         slug = "aliens",
                         image_url = "https://m.media-amazon.com/images/I/91kkGWtyqTL._AC_SL1500_.jpg",
                         _id = PyObjectId("12345678901234567890ffff")
                        )
   
    print( terminator_thing.to_json() )
    print( aliens_thing.to_bson())
    #
    aliens_vs_terminator = Fight(fighting_things = ["12345678901234567890abcd",
                                                    "12345678901234567890ffff"
                                                   ],
                                 result = "FIRST_THING_WINS",
                                 winner = "12345678901234567890abcd",
                                 _id = "5647382910aaaa0192837465"
                                )
    print(aliens_vs_terminator.to_json())
    #
    movies = ThingCollection(name = "Movies",
                             things = ["12345678901234567890abcd", "12345678901234567890ffff"],
                             _id = "dddd09876543210987654321"
                            )
    print( movies.to_json() )
    #
    best_to_worst_james_cameron_movies = RankedList(collection = "dddd09876543210987654321",
                                                    thing_scores  = {"12345678901234567890abcd" : 4.35,
                                                                     "12345678901234567890ffff": 5.10
                                                                    },
                                                    fights = ["5647382910aaaa0192837465"]
                                                    )
    print( best_to_worst_james_cameron_movies.to_json() )



    
