"""
This determines how we choose Things to arrange a new Fight for a RankedList,
based on existing Scores and information.

You can learn more about the rating system in rankor.score_calculation and
rankor.models.score.

There are many different ways of matchmaking (choosing which two Things should
fight next). First of all, we can do it just randomly. This will still give us
information, but we can be more efficient at lowering uncertainties in our
underlying skill/strength estimates by being more careful at matchmaking.

For example, in multiplayer games, matchmaking tries to maximize draw chance
(which means they try match players of roughly equal skill levels, so that games
are competitive and fun, rather than one side wiping out the other easily). This
is not a concern for rankor, as the Things do not experience joy or despair as a
result of a Fight experience and that's not rankor's focus. Also, multiplayer
games cannot choose which players out of their entire player base should play
next. They are limited to whoever is online and willing to play at the moment.

Rankor's focus is to lower our uncertainties as fast as possible. Therefore, the
main matchmaking algorithm that rankor uses is maximizing expected information
entropy. In other words rankor wants to find Fights, the results of which we
expect to give us the most information. This usually means that Things with high
sigma values are favored to be picked for a Fight, as we need to gather more
data about them and a single Fight will teach us a lot; whereas Things that we
have a ton of Fight data about won't be updated by much with one more Fight
result, so they are less likely to be picked for a Fight.

We can calculate the expected win/draw/loss probabilities based on our current
estimates, and we can also calculate how much sigma we are reducing in total by
the update in each case. This means we can calculated the expected value of
total sigma loss. We want to pick the Fights that maximize this expected sigma
loss. This means that we are maximizing fights that will reduce our uncertainty
about ratings.
"""


class BaseMatchmaker(object):
    pass


class RandomMatchmaker(BaseMatchmaker):
    pass


class MaxExpectedInformation(BaseMatchmaker):
    pass
