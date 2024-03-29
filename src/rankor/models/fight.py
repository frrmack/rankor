# Data types and type hints for the pydantic schema
from pydantic import conlist
from typing import Optional, Literal
from datetime import datetime

# Rankor base classes for models, handling encodings and bson ObjectIds
from rankor.models.mongo_model import JsonableModel, MongoModel

# This is used to help Pydantic handle the bson ObjectId field from mongodb
# More info in the module itself
from rankor.models.pyobjectid import PyObjectIdString


class Fight(MongoModel):
    """
    A Fight is a pairwise comparison between two things; its result may be
    either one thing winning or a draw.
    
    Ranking in a RankedList is achieved by pairwise comparisons called Fights.
    The result is determined by a user voting for one of the two things or for a
    draw. A Fight's result only makes sense in the context of a given
    RankedList. Every Fight is part of a RankedList and affects the scores of
    the things within that RankedList. Each Fight depicts a comparison of two
    Things. It keeps information about what the two compared Things were, and
    what the result was. If there is a winner (not a draw), the winner's or the
    loser's id can also be obtained via a property as a convenience to the
    application(s) on top of this api. The time of the fight is kept as well.
    Available results are "FIRST_THING_WINS" (winner is the first element of the
    fighting_things list which is a list with two items), "SECOND_THING_WINS"
    (winner is the last element of fighting_things) or "DRAW" (a tie). 
    
    There may be multiple Fights between two things in a single RankedList. One
    such usecase: A user keeps doing comparisons at different times for a
    RankedList, and the same couple of things comes up for comparison multiple
    times -- the result may be the same every time, or maybe different based on
    their mood and thinking at different times. 
    
    Another usecase for multiple fights between two Things: Multiple users are
    voting on Fights within the same RankedList, and different users have
    different opinions on which Thing is better, hence different results in
    multiple Fights between the same pair of Things. Think of a Fight as a chess
    game between two players. The same players may play multiple games and get
    different results, even if one is a stronger player. The stronger player
    will likely win more of the Fights, but not necessarily all, and they may
    even lose the majority just by random chance -- even if that's less likely.
    """

    ranked_list: PyObjectIdString
    fighting_things: conlist(PyObjectIdString, min_items=2, max_items=2) 
    result: Literal['FIRST_THING_WINS', 'SECOND_THING_WINS', 'DRAW']
    time_fought: Optional[datetime]

    @property
    def winner(self):
        return {
            'FIRST_THING_WINS':  self.fighting_things[0],
            'SECOND_THING_WINS': self.fighting_things[1],
            'DRAW':              None
        }[self.result]

    @property
    def loser(self):
        return {
            'FIRST_THING_WINS':  self.fighting_things[1],
            'SECOND_THING_WINS': self.fighting_things[0],
            'DRAW':              None
        }[self.result]



class ProposedFight(JsonableModel):
    """
    A ProposedFight is pretty much a Fight without a result.

    Rankor's matchmaking proposes that two things fight, when they do, a Fight
    instance with their ids and the result is saved in the database. Before they
    actually fight (a user voting for one or for a draw), at the proposal stage,
    we have a ProposedFight. Matchmaking creates ProposedFights, and users will
    vote for the results to create Fight instances together with saved results.

    ProposedFights are not saved in the database.
    """

    ranked_list: PyObjectIdString
    fighting_things: conlist(PyObjectIdString, min_items=2, max_items=2) 

