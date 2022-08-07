# Data types and type hints for the pydantic schema
from typing import Optional, Dict, List, Literal
from datetime import datetime

# Rankor superclass for models, handling encodings and bson ObjectIds
from rankor.models.mongo_model import MongoModel

# Scores are a rankor model without a separate database collection
from rankor.models.score import Score

# This is used to help Pydantic handle the bson ObjectId field from mongodb
# More info in the module itself
from rankor.models.pyobjectid import PyObjectIdString


class RankedList(MongoModel):
    """
    A RankedList is a set of Things, each associated with a score. (It's called 
    a ranked list because we can use those scores to rank them.) When we start 
    a RankedList, we assign a default starting score to each Thing and we now 
    have a set of things with scores. Of course, at this point all the scores 
    are the same, which does not give us a meaningful ranking. We then start 
    having some Fights among these Things, which update the scores of the Things 
    that have fought, and this way the scores start differentiating. As a result, 
    we start getting a more meaningful ranking. This model knows the list of scores 
    (which is a mapping of Things to scores, since each score is associated with a 
    unique Thing in this RankedList) and the associated Fights that gave rise to 
    these scores.
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
        Sort the list of things (and their score objects) based on the chosen
        score metric from the score object and return this as the ranked list of
        things
        """
        thing_list_with_scores = [
            { 
                "thing": thing_id,
                "score": score.dict()
            } 
            for thing_id, score 
            in self.thing_scores.items()
        ]

        def sorting_metric(thing_with_score_dict):
            return thing_with_score_dict["score"][self.score_used_to_rank]

        return sorted(
            thing_list_with_scores, 
            key=sorting_metric, 
            reverse=True
        )

    @property
    def top_5_things(self):
        return self.ranked_things[:5]

    @property
    def number_of_fights(self):
        return len(self.fights)

    @property
    def last_5_fights(self):
        time_of_fight = lambda fight: getattr(fight, 
                                              "date_fought", 
                                              datetime.utcnow())
        return sorted(self.fights, key=time_of_fight)



    # actually get this from a mixin class: ScoreCalculator
    def calculate_scores_from_scratch(self):
        pass

    # actually get this from a mixin class: ScoreCalculator
    def update_scores(self, fight):
        pass

    # actually get this from a mixin class: Matchmaker
    def arrange_new_fight(self):
        pass

    def summary_dict(self):
        sum_dict = self.dict(exclude_none=False)
        sum_dict.pop("thing_scores")
        sum_dict.pop("fights")
        sum_dict.update(dict(top_5_things=self.top_5_things,
                             number_of_fights=self.number_of_fights,
                             last_5_fights=self.last_5_fights)
                       )
        return sum_dict
