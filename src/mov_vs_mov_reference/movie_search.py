from googlesearch import GoogleSearch
from bs4 import BeautifulSoup
import urllib2
import urlparse
import sys

from logtemplate import get_log
log = get_log('movie_search', level="info")


class NotFoundError(Exception):
    pass



def get_name_content_url(search_result):
    return (search_result['titleNoFormatting'],
            search_result['content'],
            search_result['url'])


def find_possible_movies( movie_name ):

    query = 'imdb.com: %s' % movie_name
    search = GoogleSearch( query )
    matches = search.top_results()
    # return a list of tuples: (name, short description, url) 
    return map(get_name_content_url, matches)


def find( movie_name ):
    # I'm feeling lucky
    # Return the top result
    try:
        return find_possible_movies(movie_name)[0]
    except IndexError:
        raise NotFoundError("No movie found with name %s" % movie_name)

def connect(url):
    try:
        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page)
        log.debug('connected to %s' % url)
    except Exception:
        err_msg = "\n\n Failed to connect or parse %s\n" % url
        log.error( err_msg )
        raise NotFoundError( err_msg )
        
    return soup


def download(url, target_file_name=None):

    if target_file_name is None:
        filename = url.split('/')[-1]
    else:
        filename = target_file_name

    page = urllib2.urlopen(url)
    local = open(filename,'w')
    local.write(page.read())
    local.close()
    log.debug('%s downloaded.' % filename)

        
def parse_poster_url(imdb_soup):
    """ go parse the page and get the url
        for the poster
    """
    #~~ The 'td' tag with id "img_primary" --> the "src" of the 'img' tag within it                                                                                                  
    try:
        return imdb_soup.find('td', {'id':'img_primary'}).img.attrs['src']
    except AttributeError:
        raise NotFoundError('No poster for this title')

def get_poster(movie_url, target_filename=None):
    movie_id = urlparse.urlsplit(movie_url).path.strip('/').split('/')[-1]
    soup = connect(movie_url)
    poster_url = parse_poster_url(soup)
    if target_filename is None:
        target_filename =  movie_id + '.jpg'
    
    download(url, target_filename)

def get_imdb_url(imdb_id):
    base = "http://www.imdb.com/title/"
    return urlparse.urljoin(base, imdb_id)

def get_imdb_id(url):
    return urlparse.urlparse(url).path.strip('/').split('/',2)[1]

def get_imdb_type(url):
    return urlparse.urlparse(url).path.strip('/').split('/',1)[0]

        
def parse_description(imdb_soup):
    p = imdb_soup.find('td', {'id':'overview-top'}).find('p',{'itemprop':'description'})
    if p is None:
        return 'N/A'
    else:
        removed_links = [a.extract() for a in p('a')]
        desc = p.get_text()
        # if there was a summary link, remove excess
        if removed_links:
            desc = desc.rsplit('...', 1)[0] + '...'
        return desc

def parse_name_year_director(imdb_soup):
    
    # shorter name for the soup
    soup = imdb_soup

    #~~ the h1 tag with class "header" and itemprop "name"                                                                                                                           
    name_header = soup.findAll('h1', {'class':'header'})[0]

    name = name_header.span.get_text()
    year = name_header.find('span', {'class':'nobr'}).get_text().strip('()')

    #~~ first 'div' tag with the class 'txt-block'--> first 'a' tag within it                                                                                                        
    director = soup.findAll('div', {'class': "txt-block"})[0].a.get_text()

    # done                                                                                                                                                                       
    return name, year, director

def parse_genres(imdb_soup):

    #~~ the h4 tag that says Genres:
    genres = imdb_soup.findAll('h4', text="Genres:")[0]

    #~~ genres are all the links in the div that has the "Genres:" h4
    return [genre_link.string for genre_link in genres.parent.findAll('a')]


    

if __name__ == "__main__":
    

    # manual
    usage = "Usage: python movie_search.py The Unbearable Lightness of Being"

    # parge args (movie name)
    if len(sys.argv) < 2:
        print usage
        sys.exit()
    else:
        movie_name = ' '.join(sys.argv[1:])
    
    # log
    print 'Looking for: %s' % movie_name
    print '-------------' + '-'*len(movie_name)

    try:
        # perform search
        title, content, url = find(movie_name)
    except NotFoundError:
        # log if not found
        print 'No movie found with this name.'
    else:
        # report the top result
        #get_poster(url)
        print title.rstrip('- IMDb')
        print
        for sentence in content.split('. '):
            print sentence.replace('\n', ' ') + '.'


