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


# Import settings for a specific instance of the rankor api (settings.py in the root dir)
import settings

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
    name: str
    image_url: Optional[AnyUrl]
    category: Optional[str]     # Future idea: Turn categories into a class? Also add a tag class?
    extra_data: Optional[Json]
    date_created: Optional[datetime]
    date_updated: Optional[datetime]



class Fight(MongoModel):
    """
    Ranking is done by pairwise comparisons. A Fight is a pairwise comparison.
    A Fight's result only makes sense in the context of a given RankedList.
    Every Fight is part of a RankedList and affects the scores of the things
    within that RankedList.
    Each Fight depicts a comparison of two Things. It keeps information about 
    what the two compared Things were, and what the result was. If there is
    a winner (not a draw), the winner's id is also saved as a convenience to
    the application(s) on top of this api. The time of the fight is kept as well.
    Available results are "FIRST_THING_WINS" (winner is the first element of
    the fighting_things list which is a list with two items), "SECOND_THING_WINS" 
    (winner is the last element of fighting_things) or "DRAW" (a tie).
    There may be multiple Fights between two things in a single RankedList. One 
    such usecase: a user keeps doing comparisons at different times for a RankedList,
    and the same couple of things comes up for comparison multiple times -- the result 
    may be the same every time, or maybe different based on their mood and thinking at 
    different times. Another usecase: multiple users are voting on Fights within the 
    same RankedList, and different users have different opinions on which Thing is better, 
    hence different results in multiple Fights between the same pair of Things.
    Think of a Fight as a chess game between two players. The same players may play 
    multiple games and get different results, even if one is a stronger player. The 
    stronger player will likely win more of the Fights, but not necessarily all, and 
    they may even lose the majority just by random chance -- even if that's less likely.
    """
    ranked_list: PyObjectId
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


class Score(BaseModel):
    """
    A Score instance represents the score of a Thing in a specific RankedList.
    As Things are compared in Fights within the context of a given RankedList,
    their scores are updated based on the Fight results. Every RankedList
    has a dictionary mapping it things to their scores. These scores allow them
    to be ranked. A thing has only one score per each RankedList it participates in, 
    and each RankedList has only one score for each thing participating in it. 

    Rankor uses the TrueSkill Bayesian inference algorithm to calculate ranking
    scores for Things based on Fight results. A Score has the mu and sigma values 
    of the TrueSkill Rating. TrueSkill uses a Gaussian posterior for estimating 
    the strength of a Thing (for ranking purposes). mu is the mean of this posterior,
    it's our current best guess for a Thing's strength. sigma is its standard
    deviation. The higher the sigma, the less sure we are that the Thing's strength
    is indeed very near mu. We know with 99% confidence that the Thing's strength is
    within the range of (mu - 3*sigma) and 
    
    It also reports a min_possible_score, which is the equivalent of a TrueSkill 
    score that Microsoft uses for ranking users based on their skill in competitive 
    games. They also use this for matchmaking.The min_possible_score is (mu - 3 * sigma). 
    We are 99% sure that the Thing's strength is at least this min_possible_score. 
    It can definitely be higher. It also could actually be lower than this but that's 
    a very low probability. So the 'min_possible_score' name is technically misleading,
    but accurate enough in practice.
    Why is Microsoft using this? As players play more (or Things fight more), the 
    uncertainty around their skill level goes down, they have smaller sigmas. For
    players / Things that didn't fight a lot yet, min_possible_score will be low due
    to high sigma values. That's desired. If a min_possible_score is high, you know
    that it's really high due to information from their fights, and not just because
    of a small number of data points. Think about it like this: On Amazon, would you
    buy a product that has 12000 reviews with an average of 4.1 stars, or another one
    that has 5 reviews with an average of 4.2 stars? With the first one, you feel a lot
    more certain of the average star rating due to the large number of reviews. This is
    aking to a Thing that has been in many Fights and therefore has a low sigma. The latter
    is like a Thing that only has been in a few Fights. The former would have a min_possible_score
    that actually is close to 4.1 (if we are using stars as our score unit), whereas the
    min_possible_score of the latter could still be at 2.5 stars or something like that,
    since there still is a ton of uncertainty / high sigma due to lack of review data.
    Microsoft has chosen to value this a lot. It ranks people based on the 99% certainty 
    about their minimum skill level. This also creates the desired experience that a new player
    is ranked low at the beginning (due to high sigma), they they rise up the ranks
    
    While Rankor provides the min_possible_score value usually used with TrueSkill rankings,
    it also reports its own approach to reducing mu and sigma to a single score to sort by 
    for ranking. This is because the ranking it wants to achieve is a different problem than
    leaderboards for multiplayer games or the experience design for a new player in both 
    matchmaking and rising up the ranks. Rankor calculates a rankor_score, and recommends
    using this for ranking. The rankor_score is (mu-sigma). The same idea of valuing high data,
    low sigma idea is still considered, but instead of the 99% certainty level, a 68% certainty
    level is preferred. rankor_score still punishes high sigma, but to a much lower extent than
    Miscrosoft TrueSkill rankings. One of the most important reasons for this is the difference
    in sigma variance. In Microsoft's case, some players just play the game a lot, and others 
    don't, which means there are some players with very high sigma, some with middle values, some
    with very low, etc. Sigma values vary a lot. Whereas in Rankor, Things do not have different
    preferred fighting frequencies, the number of fights that each Thing will experience in a 
    RankedList will be a lot more comparable (with some noise of course). Both because each Thing
    is 'willing' to participate to the same degree unlike game players, and also because of the 
    matchmaking. When matching players to play a game, Microsoft tries to optimize for similar
    skill levels, meaning they match people that are likeliest to draw -- that's to avoid a pro
    dominating a newbie situation. But Rankor optimizes to maximize information gain. This means
    that if we know less about a Thing (high sigma), that Thing is more likely to be called to 
    a new fight: A fight involving them will give us a lot more new information than a fight between
    two veteran Things that have already been in hundreds of fights---we already know a lot about them,
    their sigmas are low, another fight data point wouldn't teach us much more. Therefore, rankor's
    matchmaking keeps sigma variance low among all Things. This means we have to worry less about a 
    12000 reviews 4.1 stars vs 5 reviews 4.2 stars situation, the review numbers of products would be
    comparable in this analogy. This gives us the chance to use a value closer to mu (our best guess),
    therefore while rankor still adjusts by going ine stdev below the mean, it is less cautious than
    Microsoft due to the different nature of the problem and matchmaking.

    You can of course design your own ranking score calculation using mu or sigma, or you may prefer
    to directly rank Things by mu (our best guess for their underlying 'true' score). rankor_score
    is only what this rankor api suggests as a good ranking score design.
    """
    mu    = settings.DEFAULT_INITIAL_SCORE_MU_VALUE
    sigma = settings.DEFAULT_INITIAL_SCORE_SIGMA_VALUE

    @property
    def min_possible_score(self) -> float:
        return self.mu - 3 * self.sigma

    @property
    def rankor_score(self) -> float:
        return self.mu - self.sigma



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
    name: str
    # collection: PyObjectId                     # The sourcing ThingCollection
    thing_scores: Dict[PyObjectId, float]
    fights: List[PyObjectId]
    date_created: Optional[datetime]
    date_updated: Optional[datetime]



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
                             image_url = "https://m.media-amazon.com/images/I/61qCgQZyhOL._AC_SY879_.jpg",
                             extra_data = """{"director":"James Cameron", "year":1982}""",
                             _id = PyObjectId("12345678901234567890abcd")
                            )
    aliens_thing = Thing(name = "Aliens",
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





    
