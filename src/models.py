import simplejson as json

class ThingHasNoNameOrImageError(Exception):
    pass


class Thing(object):

    def __init__(self, name=None, image_url=None, **other_fields):
        if name is None and image_url is None:
            error_message = ("The Thing (to rank) which you are trying to " 
            "create has no name or an image url. It needs at least one of these " 
            "so that RANKOR can know how to refer to and represent it.")
            raise ThingHasNoNameOrImageError(error_message)

        self.name = name
        self.image_url = image_url    
        self.other_fields = other_fields

    def json(self):
        return json.dumps(self, default=lambda x: x.__dict__)

    def



if __name__ == '__main__':
    t = Thing(name="The Terminator", director="James Cameron", year=1982)
    print( t.json() )
    
