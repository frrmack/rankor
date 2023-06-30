"""
The logic to update Things' Scores in a RankedList based on Fight results.

It relies on Microsoft's Trueskill algorithm, which is a Bayesian rating system.
It is a step on the path of development from Elo to Glicko algorithms in chess
to leaderboard rankings and matchmaking in online multiplayer video games.

Elo rating system was developed for rating chess players. It pioneered the model
where:

1) Each player's underlying skill/strength is represented by a single number

2) In a given game, the player's performance is a normally distributed random
   variable, centered around that single skill number.

So, let's say a player's underlying skill level is 2210. In a given game, they
may end up performing at a level realistically (95%) ranging from 2050 to 2370
(with numbers towards either end of that range being A LOT less likely than
those closer to the center). When two players play, they each randomly choose a
number from their respective performance probability distributions, and
whoever's performance number is higher wins the game. This is the model of how
chess matches go.

Once we decide to use this model, we can develop algorithms to infer the
underlying skill number of each player based on the results of the games they
play against each other. All the following algorithms / rating systems are based
on this same model, they differ in how they calculate and report their estimates
of the underlying skill levels.

The Elo system (developed by Arpad Elo in 1960) assumes that the standard
deviation of the performance distribution is the same for all players to
simplify calculations. This means that the performance range is the same size
for everyone, the only difference is where it's centered. With this assumption,
we can also easily calculate the expected result probabilities if we know the
skill numbers for each player. For example a player playing another with the
same exact underlying skill level has 50% probability to win. If they are
playing someone with a skill level 150 less than theirs, they have a 70.34%
probability to win. (Note that these calculations do not take draw chance into
account, which is a big caveat for chess where there are a lot draws and drawing
against a great player can carry a ton of information. There is a reference link
below to help you better understand how draws factor into Elo. All the following
rating systems below take draws into account in a natural way). The goal of the
Elo algorithm is to estimate the underlying skill level for each player. Elo
starts by estimating the same number for everyone, calculating the win/loss
probabilities, and then updating these estimates if the actual result statistics
are above or below these probabilistic win/loss expectations.

https://en.wikipedia.org/wiki/Elo_rating_system
https://www.researchgate.net/publication/341384358_Understanding_Draws_in_Elo_Rating_Algorithm

Glicko and Glicko-2 rating systems (by Mark Glickmann in 1995) came later as an
improvement on Elo, and rather than reporting a single number (our best estimate
for a player's underlying skill level), it reports two, our best estimate and
how certain we are about this estimate (the "rating deviation" RD), based on how
much game data we've seen and how much time has passed since the player's last
game. Note that this RD is not the standard deviation of the performance
distribution. It is the standard deviation of our estimate for the skill level
(mean of the player's performance distribution). We have a Gaussian estimate
about this skill number, think of this as our belief on what the underlying
skill could be (in a Bayesian posterior sense). The higher the RD, the wider our
belief distribution ("It could be anywhere between 1600 to 2500 really"). The
lower the RD, the more certain we feel about estimating the underlying skill
level ("I'm pretty sure this guy is somewhere right between 2140 and 2150). In
the latter case, even though we are really sure about their skill level due to
lots of very recent data, they may still perform way above or below this skill
level, because the performance distribution stays the same. Only the standard
deviation of our estimate prior decreases as we learn more about the player from
their latest games. RD is about uncertainty, not performance.

This is Glicko. Glicko-2 improved on this by adding a rating volatility
parameter, which does consider the standard deviation of the performance
distribution. Players with high volatility have erratic performances, sometimes
really high, sometimes really low. Players with low volatility perform in a
consistent manner. Glicko-2 basically stopped assuming that the performance
distribution widths are the same for everyone.

https://tomrocksmaths.com/2021/07/16/elo-and-glicko-standardised-rating-systems/
https://www.englishchess.org.uk/wp-content/uploads/2012/04/The_Glicko_system_for_beginners1.pdf
http://www.glicko.net/glicko/glicko2.pdf

Microsoft developed TrueSkill for Halo 3 (and other) leaderboards in 2004 as a
follow up to the initial skill-based matchmaking algorithm in Halo 2. Then they
developed TrueSkill 2 as an update to it for Gears of War and Halo 5. TrueSkill
and TrueSkill 2 are Bayesian systems, and just like Glicko, they report two
numbers:

- mu:       The current skill estimate of the player
- sigma:    The degree of uncertainty in our estimate

For players that played a ton of games, we have a lot of data and therefore a
lot less uncertainty. As we see more games from a player, sigma goes down and mu
starts changing less and less after each game. 

Unlike Glicko, it doesn't take time into account. Rather than our uncertainty
steadily increasing with time as the player doesn't play, TrueSkill increases
the uncertainty a set amount between each game to account for the potential
underlying skill change between the games. 

One big development for TrueSkill was that it could also use data from team
matches, where multiple players on each side play a game against each other.
TrueSkill updated all team player's estimates based on the team match result
(assuming each player contributed equally to the team). TrueSkill 2 later made
this more precise by taking into account different performance contributions of
each player to the team.

https://www.microsoft.com/en-us/research/project/trueskill-ranking-system/)
https://www.microsoft.com/en-us/research/publication/trueskill-2-improved-bayesian-skill-rating-system/
https://www.peachpit.com/articles/article.aspx?p=443596

Of course, while these algorithms were developed for chess and Halo players,
they are general rating systems, and are not limited to rating players of
specific games. The core idea is that we are estimating an underlying
level/skill based on pairwise comparisons. A chess game is a pairwise comparison
of two players where either one of them is greater (win/loss) or they are equal
(a draw). You can do this for rating books, movies, video games, etc. The
underlying skill level in that case becomes how 'good' the book really is, or
how much love it deserves, for example. Not necessarily an intrinsic value, it
can be how much one person truly likes it, or how much a group of people like
it. Each Fight is a comparison asking 'do you like this book more or this book
more when you think about it right now?'. Again, we pull performance numbers
from a distribution centered around the underlying true rating. You may feel
like one answer one day, and another the other day, the point is, if you like
one book more in the sense of its underlying true rating, you will choose that
over the other MORE OF THE TIME. With more comparisons, it's expected to be
chosen more times over the other. You also don't have to pose the question
around liking something. It could be a question like 'which of these two
presidents oversaw more effective economic policies in your opinion', and the
underlying rating becomes the opinion on economic policy effectiveness. Any type
of rating can be achieved by these systems, whether for a single person's
opinion, or a collective group's, where eveyone joins in voting on these
pairwise comparisons (Fights in rankor) to see how the community thinks about
these ratings collectively.

You can find more information on rankor's score metrics (based on the TrueSkill
estimate mu and sigma) in rankor.models.score, but here is a quick copy paste:
    ----------------------------------------------------------------------------
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
    This is akin to a Thing that has been in many Fights and therefore has a
    low sigma. The latter is like a Thing that only has been in a few Fights.
    The former would have a min_possible_score that actually is close to 4.1 (if
    we are using stars as our score unit), whereas the min_possible_score of the
    latter could still be at 2.5 stars or something like that, since there still
    is a ton of uncertainty / high sigma due to lack of review data. Microsoft
    has chosen to value this a lot. It ranks people based on the 99% certainty
    about their minimum skill level. This also creates the desired experience
    that a new player is ranked low at the beginning (due to high sigma), they
    then rise up the ranks as they play and the uncertainty goes down.
    
    While Rankor provides the min_possible_score value usually used with
    TrueSkill rankings, it also reports its own approach to reducing mu and
    sigma to a single score to sort by for ranking. This is because the ranking
    it wants to achieve is a different problem than leaderboards for multiplayer
    games or the experience design for a player in both matchmaking and
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
    to mu (our best guess), therefore while rankor still adjusts by going one
    stdev below the mean, it is less cautious than Microsoft due to the
    different nature of the problem and matchmaking.

    You can of course design your own ranking score calculation using mu or
    sigma, or you may prefer to directly rank Things by mu (our best guess for
    their underlying 'true' score). rankor_score is only what this rankor api
    suggests as a good ranking score design.
    --------------------------------------------------------------------------
"""


class ScoreCalculator(object):
    pass