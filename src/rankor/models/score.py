# Model template import
# Instances of this model are not stored in the database. They are put together
# based on the thing to score mapping saved in RankedList documents in the
# database. There is no ranked_things collection in the database. Therefore,
# they do not have a database id, and they don't inherit from MongoModel, but 
# simply from JsonableModel.
from rankor.models.jsonable_model import JsonableModel

# Api configuration (for scoring priors)
from rankor.config import rankor_config

class Score(JsonableModel):
    """
    A Score instance represents the score of a Thing in a specific RankedList.
    As Things are compared in Fights within the context of a given RankedList,
    their Scores are updated based on the Fight results. Every RankedList has a
    dict that maps each Thing to its Score. These scores allow the Things to be
    ranked, earning the RankedList its name. A Thing has only one Score per each
    RankedList it participates in, and each RankedList has only one Score for
    each Thing participating in it. 

    Rankor uses the TrueSkill Bayesian inference algorithm to calculate ranking
    scores for Things based on Fight results. A Score has the mu and sigma
    values of the TrueSkill rating. TrueSkill uses a Gaussian posterior for
    estimating the underlying 'strength' of a Thing (for ranking purposes). mu
    is the mean of this posterior, it's our current best guess for a Thing's
    strength. sigma is the standard deviation of this posterior, it represents
    our uncertainty around our best guess. The higher the sigma, the less sure
    we are that the Thing's strength is indeed very near mu. 
    
    - We know with 99% confidence that the Thing's strength is within the range
      of (mu - 3*sigma) and (mu + 3*sigma)

    - We know with 95% confidence that the Thing's strength is within the range
      of (mu - 2*sigma) and (mu + 2*sigma)      

    - We know with 68% confidence that the Thing's strength is within the range
      of (mu - sigma) and (mu + sigma)

    It also reports a min_possible_score, which is the equivalent of a TrueSkill
    score that Microsoft uses for ranking users based on their skill in
    competitive games. They also use this for matchmaking. The
    min_possible_score is (mu - 3 * sigma). We are 99% sure that the Thing's
    strength is at least this min_possible_score. It can definitely be higher.
    It also could actually be lower than this but that's a very low probability.
    So the 'min_possible_score' name is technically misleading, but accurate
    enough in practice. Why is Microsoft using this? As players play more (or
    Things fight more), the uncertainty around their skill level goes down, they
    have smaller sigmas. For players / Things that didn't fight a lot yet,
    min_possible_score will be low due to high sigma values. That's desired. If
    a min_possible_score is high, you know that it's really high due to
    information from their fights, and not just because of a small number of
    data points. Think about it like this: On Amazon, would you buy a product
    that has 12000 reviews with an average of 4.1 stars, or another one that has
    5 reviews with an average of 4.2 stars? With the first one, you feel a lot
    more certain of the average star rating due to the large number of reviews.
    This is aking to a Thing that has been in many Fights and therefore has a
    low sigma. The latter is like a Thing that only has been in a few Fights.
    The former would have a min_possible_score that actually is close to 4.1 (if
    we are using stars as our score unit), whereas the min_possible_score of the
    latter could still be at 2.5 stars or something like that, since there still
    is a ton of uncertainty / high sigma due to lack of review data. Microsoft
    has chosen to value this a lot. It ranks people based on the 99% certainty
    about their minimum skill level. This also creates the desired experience
    that a new player is ranked low at the beginning (due to high sigma), they
    they rise up the ranks
    
    While Rankor provides the min_possible_score value usually used with
    TrueSkill rankings, it also reports its own approach to reducing mu and
    sigma to a single score to sort by for ranking. This is because the ranking
    it wants to achieve is a different problem than leaderboards for multiplayer
    games or the experience design for a new player in both matchmaking and
    rising up the ranks. Rankor calculates a rankor_score, and recommends using
    this for ranking. The rankor_score is (mu-sigma). The same idea of valuing
    high data, low sigma idea is still considered, but instead of the 99%
    certainty level, a 68% certainty level is preferred. rankor_score still
    punishes high sigma, but to a much lower extent than Miscrosoft TrueSkill
    rankings. One of the most important reasons for this is the difference in
    sigma variance. In Microsoft's case, some players just play the game a lot,
    and others don't, which means there are some players with very high sigma,
    some with middle values, some with very low, etc. Sigma values vary a lot.
    Whereas in Rankor, Things do not have different preferred fighting
    frequencies, the number of fights that each Thing will experience in a
    RankedList will be a lot more comparable (with some noise of course). Both
    because each Thing is 'willing' to participate to the same degree unlike
    game players, and also because of the matchmaking. When matching players to
    play a game, Microsoft tries to optimize for similar skill levels, meaning
    they match people that are likeliest to draw -- that's to avoid a pro
    dominating a newbie situation. But Rankor optimizes to maximize information
    gain. This means that if we know less about a Thing (high sigma), that Thing
    is more likely to be called to a new fight: A fight involving them will give
    us a lot more new information than a fight between two veteran Things that
    have already been in hundreds of fights---we already know a lot about them,
    their sigmas are low, another fight data point wouldn't teach us much more.
    Therefore, rankor's matchmaking keeps sigma variance low among all Things.
    This means we have to worry less about a 12000 reviews 4.1 stars vs 5
    reviews 4.2 stars situation, the review numbers of products would be
    comparable in this analogy. This gives us the chance to use a value closer
    to mu (our best guess), therefore while rankor still adjusts by going ine
    stdev below the mean, it is less cautious than Microsoft due to the
    different nature of the problem and matchmaking.

    You can of course design your own ranking score calculation using mu or
    sigma, or you may prefer to directly rank Things by mu (our best guess for
    their underlying 'true' score). rankor_score is only what this rankor api
    suggests as a good ranking score design.
    """
    mu: float    = rankor_config['score_parameters']['initial_mu_value'] 
    sigma: float = rankor_config['score_parameters']['initial_sigma_value']

    @property
    def min_possible_score(self) -> float:
        return self.mu - 3 * self.sigma

    @property
    def rankor_score(self) -> float:
        return self.mu - self.sigma

    def dict(self, *args, **kwargs):
        """
        Overwrites BaseModel's dict method to include calculated score
        properties in the dict representation of the model instance. This dict
        method in all models is used for
        
        -  bson encodings (such as MongoModel.to_bsonable_dict() converted to
           bson through pymongo) 

        -  json encodings (such as MongoModel.to_jsonable_dict() and
           MongoModel.to_json() using pydantic's json encoder)
           
        -  direct dict representations in native python without any specified
           encoding purposes
        """
        obj_dict = super(Score, self).dict(*args, **kwargs)
        properties_dict = dict(min_possible_score=self.min_possible_score,
                               rankor_score=self.rankor_score)
        obj_dict.update(properties_dict)
        return obj_dict
                   

