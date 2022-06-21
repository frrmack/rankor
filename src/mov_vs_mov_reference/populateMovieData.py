import sys, os
sys.path.append('../Web/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Web.settings")

import HTMLParser

from base.models import Movie


DATAFILE = '../data/currentRatings.tsv'

with open(DATAFILE, 'r') as datafile:
    count = 0
    for row in datafile:
        count += 1
        readName, readRating = row.split('\t')
        # unescape HTML entities from name
        h = HTMLParser.HTMLParser()
        readName = h.unescape(readName)
        # convert star rating to interger
        readRating = int(readRating)
        # report
        #print >> sys.stderr, readName, '(%s)' % ('*'*readRating)
        if count % 100 == 0:
            print >> sys.stderr, '%i movies saved' % count
        # add to the database
        movie = Movie(name=readName, starRating=readRating)
        movie.save()
    print >> sys.stderr, '%i movies saved.\nFinished.' % count


