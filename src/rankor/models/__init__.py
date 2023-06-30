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





if __name__ == '__main__':
    
    # Test and log model instantiation ensure correct behavior

    # Note: normally, we would not create these instances by assigning them _id values 
    # ourselves. Instead of creating them with written _id fields, we'd let _ids be
    # automatically assigned by mongo when pymongo writes them to the db. We are only
    # explicitly defining _id fields ourselves here, so that we know the _id values already
    # to test other models that reference these stuff. It's just so we can run some basic
    # tests to ensure the code works as intended, without having to write to and read from
    # the database, just to get _ids assigned.

    terminator_thing = Thing(name = "The Terminator", 
                             image_url = "https://m.media-amazon.com/images/I/61qCgQZyhOL._AC_SY879_.jpg",
                             other_data = {"director":"James Cameron", "year":1982},
                             _id = PyObjectId("12345678901234567890abcd")
                            )
    aliens_thing = Thing(name = "Aliens",
                         image_url = "https://m.media-amazon.com/images/I/91kkGWtyqTL._AC_SL1500_.jpg",
                         _id = PyObjectId("12345678901234567890ffff")
                        )
    print( terminator_thing.to_json() )
    print( aliens_thing.to_bsonable_dict())
    #
    aliens_vs_terminator = Fight(fighting_things = ["12345678901234567890abcd",
                                                    "12345678901234567890ffff"
                                                   ],
                                 result = "FIRST_THING_WINS",
                                 ranked_list= "aaaaabbbbbcccccdddddefef",
                                 _id = "5647382910aaaa0192837465"
                                )
    print(aliens_vs_terminator.to_json())
    #
    best_to_worst_james_cameron_movies = RankedList(
        name = "Favorite Cameron Movies",
        thing_scores  = {
            "12345678901234567890abcd" : Score(),
            "12345678901234567890ffff" : Score()
        },
        fights = ["5647382910aaaa0192837465"],
        _id = "aaaaabbbbbcccccdddddefef"
    )
    print( best_to_worst_james_cameron_movies.to_json() )
    print( best_to_worst_james_cameron_movies.top_3_things )
    print( best_to_worst_james_cameron_movies.last_3_fights )
    print( best_to_worst_james_cameron_movies.summary_dict())

