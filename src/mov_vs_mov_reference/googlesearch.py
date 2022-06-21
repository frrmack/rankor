#!/usr/bin/python
"""
Python Wrapper around the Google API for search

It returns results for a google search.
A result is a dictionary with the following fields:

cacheUrl
content
title
titleNoFormatting
unescapedUrl
url
visibleUrl

"""

import json
import urllib

class GoogleSearch(object):
    
    api_url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s'

    def __init__(self, query):
        self.query = query
        self._ajax_query = urllib.urlencode({'q': self.query})
        self._result_data = None

    @property
    def result_data(self):
        if self._result_data is None:
            query_url = self.api_url % self._ajax_query
            search_response = urllib.urlopen(query_url).read()
            self._result_data = json.loads(search_response)['responseData']
        return self._result_data

    def count(self):
        "Number of results"
        return self.result_data['cursor']['estimatedResultCount']

    def top_result(self):
        """ First hit (what I'm feeling lucky would return)"""
        return self.result_data['results'][0]

    def top_results(self):
        """ Top hits (only four by default) """
        return self.result_data['results']

    def top_url(self):
        return self.top_result()['url']

    def top_urls(self):
        get_url = lambda result: result['url']
        return map(get_url, self.top_results())

    







# A few test cases and example uses
if __name__ == '__main__':

    from pprint import pprint

    gs = GoogleSearch("Testing")

    for hit in gs.top_results():
        pprint(hit)
        print

    print '------------------'
    print

    gs = GoogleSearch("wikipedia.com: Porcupine")
    print gs.top_result()['titleNoFormatting']
    print gs.top_url()

    print
    print '------------------'
    print
    
    color  = GoogleSearch("color").count()
    colour = GoogleSearch("colour").count()
    print 'color vs colour:'
    if   color > colour:
        print 'color wins with %s vs %s' % (color,colour)
    elif color < colour:
        print 'colour wins with %s vs %s' % (colour,color)
    else:
        print "it's a tie with %s each!" % color
    print


