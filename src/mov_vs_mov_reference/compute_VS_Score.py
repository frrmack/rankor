# Starts from scratch, iterates over every match
# in the database, updates Score mu and sigmas
# for every user's movie scores, then
# saves these mu and sigmas into the database
#
#
# This complete reset and recalculation of VS Score
# from the entire history of matches is necessary:
# At individual comparisons, Score is updated using
# the result of that match, BUT if it is not a new comparison,
# but revoting on a previously done comparison, the results
# will not be accurate. They won't be far from the actual
# results, but not 100% accurate. Since the design decision
# is made to treat every comparison with only a single outcome
# (and no repeat-matches), revoting on a match basically changes
# history (it deletes the old match from history). To find the
# accurate results with this change, a reset and recalculation
# is necessary. Of course, this 'revoting' should be a VERY RARE
# event, so running this script at a low frequency for corrections
# is completely fine.
#
#
# (This also gives a way to play with game parameters
# and see the final results.)
#



import sys, os

SCRIPTPOS = os.path.abspath(__file__).rsplit('/',1)[0] + '/'
WEBSITEDIR = SCRIPTPOS + '../'
sys.path.append(WEBSITEDIR)
sys.path.append(SCRIPTPOS)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Web.settings")


from base.models import Movie, Score, Fight, User
from django.db import transaction, reset_queries

import time
from datetime import datetime
from django.utils.timezone import utc

import trueskill as ts

def log(msg):
    timestamp = datetime.utcnow().replace(tzinfo=utc)
    print >> sys.stderr, '%s --- %s' %(timestamp, msg)


def update_true_skill(fight, true_skill_dict):
    """ incremental TrueSkill update function after one fight
    """
    TrueSkill = true_skill_dict
    movie_1, movie_2 = fight.movie1.imdb_id, fight.movie2.imdb_id    
    if movie_1 in TrueSkill and movie_2 in TrueSkill:
        if fight.isDraw():
            id1, id2 = movie_1, movie_2
        else:
            id1, id2 = fight.winner().imdb_id, fight.loser().imdb_id
        new_ratings = ts.rate_1vs1(TrueSkill[id1], TrueSkill[id2], drawn=fight.isDraw())
        TrueSkill[id1], TrueSkill[id2] = new_ratings

def compute_true_skills(user):
    """ recalculate TrueSkills from the entire history of fights
    """
    # True Skill parameters for Movie ratings
    # Details and reasoning can be found at: 
    # https://www.evernote.com/Home.action#st=p&n=ea2365e1-fe1c-4f4c-97b6-18cf78431fa4
    ts.setup(mu=3.0, sigma=1.0, beta=0.3, tau=0.005, draw_probability=0.05)

    # initiate TrueSkill dict
    seededTS = {}

    # initialize TrueSkill for each rated movie
    for score in Score.objects.filter(user=user).exclude(starRating=0):
        imdb_id = score.movie_imdb_id()
        starRating = score.starRating
        seededTS[imdb_id] = ts.Rating(mu=1.*starRating, sigma=0.5)
    # iterate over fightes (over time) and incrementally update
    # TrueSkill dict
    count = 0
    for fight in sorted(Fight.objects.filter(user=user),
                       key = lambda m: m.timestamp):
        update_true_skill(fight, seededTS)
        if count and count % 200 == 0: print >> sys.stderr, '%i fights processed.' % count
        count += 1


    # record new ratings in the database
    count = 0
    for score in Score.objects.filter(user=user):
        movie_id = score.movie_imdb_id()
        try:
            new_TS = seededTS[movie_id]
        except KeyError:
            # this movie was just saved in between starting the TrueSkill
            # calculations and recording the results. we'll get it in the
            # next round.
            continue
        update_score(user, movie_id, new_TS)
        count += 1
    #log('--- a total of %i ratings recorded. ---' % (count))
    return count

@transaction.atomic
def update_score(user, movie_id, new_TS):
    score = Score.objects.get(user=user, movie=movie_id)
    score.mu = new_TS.mu
    score.sigma = new_TS.sigma
    score.save()


def main():
    # If this is run in an infinite loop, you need reset_queries
    # to avoid a memory leak. Read more here:
    # http://stackoverflow.com/questions/2338041/python-django-polling-of-database-has-memory-leak
    reset_queries()
    user_count, score_count = 0, 0
    for user in User.objects.values_list('id', flat=True):
        #log('Updating scores for user: %s' % User.objects.get(id=user).username)
        score_count += compute_true_skills(user)
        user_count += 1
    log('Updated %i scores from %i users.' % (score_count, user_count))

if __name__ == '__main__':
    
    if len(sys.argv) > 1 and sys.argv[1] == '-c':
        # infinite loop
        while True:
            main()
            time.sleep(5)
    else:
        main()


