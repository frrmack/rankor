# Data types and type hints for the pydantic schema
from typing import Optional, Dict, List, Literal
from datetime import datetime

# Model template import
# Rankor superclass for models, handling encodings and bson ObjectIds
from rankor.models.mongo_model import MongoModel

# Model imports 
# Score is a rankor model to package ranking score information for a Thing.
# RankedThing is a rankor model that contains the rank, score, and id of a Thing
# within a RankedList.
from rankor.models.score import Score
from rankor.models.ranked_thing import RankedThing

# PyObjectIdString is a field that contains the hex string of a bson object id.
# It is used to store the id string of another model document (in this case, the
# id of a Thing or a Fight). There's more info in the pyobjectid module itself.
from rankor.models.pyobjectid import PyObjectIdString


class RankedList(MongoModel):
    """
    A RankedList is a set of Things, each associated with a score. 
    
    It's called a ranked list because we can use those scores to rank them. When
    we create a RankedList, we assign a default starting score to each Thing and
    we now have a set of things with scores. Each Thing is associated with only
    one score in a RankedList. Of course, at this point all the scores are the
    same, which does not give us a meaningful ranking. We then start having some
    Fights among these Things, which update the scores of the Things that have
    fought based on the results, and this way the scores start differentiating.
    As a result, we start getting a more meaningful ranking. With more fights,
    the uncertainty around the underlying strength of each Thing goes down. This
    uncertainty is represented by the sigma field in a Score model, and is taken
    into account by a couple of score metrics.

    Fields:
    
    name:               name of this RankedList

    thing_scores:       a dict that maps Thing ids to their scores

    fights:             a list of all Fights fought for this RankedList

    time_created & 
    time_edited:        automatically assigned timestamps

    score_used_to_rank: which field of the Score objects to rank Things by (You
                        can find more information on what each option means in
                        the rankor.models.score module)
    
    Properties:
     
    ranked_things:      ranked list of all Thing ids with their ranks and scores in
                        this RankedList (a list of RankedThing models)

    

    top_3_things:       The first three RankedThings in RankedList.ranked_things
                        (top three ranked Thing ids with their scores)

    number_of_fights:   Total number of recorded fights for this RankedList

    last_3_fights:      The last three fights 
                        (last three items of RankedList.fights sorted by time)
    """

    name: str
    thing_scores: Dict[PyObjectIdString, Score]
    fights: List[PyObjectIdString]
    time_created: Optional[datetime]
    time_edited: Optional[datetime]
    score_used_to_rank: Literal["rankor_score", 
                                "min_possible_score", 
                                "mu"] = "rankor_score"

    @property
    def ranked_things(self):
        """
        Ranked list of all RankedThings in the RankedList.

        Sorts the list of things (and their score objects) based on the chosen
        score metric from the score object. Represents each Thing, its rank, and
        its score with a RankedThing in this ranked list. Returns this list of
        RankedThings.
        """
        def sorting_metric(thing_scores_item):
            thing_id, score = thing_scores_item
            return getattr(score,
                           self.score_used_to_rank)

        sorted_thing_id_and_score_list = sorted(self.thing_scores.items(), 
                                                key=sorting_metric, 
                                                reverse=True)
        return [
            RankedThing(rank = zero_based_index + 1, 
                        thing_id = thing_id, 
                        score = score)
            for zero_based_index, (thing_id, score)
            in enumerate(sorted_thing_id_and_score_list)
        ]


    @property
    def top_3_things(self):
        return self.ranked_things[:3]

    @property
    def number_of_fights(self):
        return len(self.fights)

    @property
    def last_3_fights(self):
        time_of_fight = lambda fight: getattr(fight, 
                                              "date_fought", 
                                              datetime.utcnow())
        return sorted(self.fights, key=time_of_fight, reverse=True)[:3]


    # actually let a ScoreCalculator class do this in score_calculation.py
    def calculate_scores_from_scratch(self):
        pass

    # actually let a ScoreCalculator class do this in score_calculation.py
    def update_scores(self, fight):
        pass

    # actually let a Matchmaker class (which takes a ranked list in init) do
    # this in matchmaking,py
    def arrange_new_fight(self):
        pass

    def summary_dict(self):
        sum_dict = self.dict(exclude_none=True)
        sum_dict.pop("thing_scores")
        sum_dict.pop("fights")
        sum_dict.update(
            dict(
                top_3_things = self.top_3_things,
                number_of_fights = self.number_of_fights,
                last_3_fights = self.last_3_fights
            )   
        )
        return sum_dict
