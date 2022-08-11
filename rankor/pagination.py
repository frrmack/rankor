"""
Pagination code for endpoints.

This provides the logic with which endpoints that return long lists divide their
responses into multiple pages.
"""

# Flask imports
from flask import url_for

# Error imports
from werkzeug.exceptions import BadRequest, InternalServerError

# Model type imports (for explicit argument typing)
from pydantic import BaseModel

# Encoder imports
from rankor.json import to_jsonable_dict, to_json

# Database access
from rankor import db

# Api settings for page sizes and sorting keys
import settings


class Paginator(object):
    """
    A class that handles pagination for endpoints, which return a rather long
    list of items. 
    
    Examples of such endpoints are endpoints.things.list_all_things,
    endpoints.ranked_lists.list_all_ranked_lists,
    endpoints.fights.recorded_fights, and endpoints.full_ranked_list_of_things.
    
    Since such lists can get long, the results are partitioned into a set number
    of pages. The page size (number of list items to include in each page), as 
    well as what to sort the items by before partitioning into pages are 
    determined in the api settings for each endpoint (settings.py in the root).

    You can ask for a specific page, for example (in list_all_things):
    curl -i -X GET 'http://localhost:5000/rankor/things/?page=3'

    If you don't give a page parameter, it will return page 1. The response will
    also include the page number and the links to the following endpoint uris:
    - this_page
    - next_page     (if there is one)
    - previous_page (if there is one)
    - last_page
    These links are there to help iterate over all results.
    """

    def __init__(
        self, 
        endpoint_name: str, 
        model: BaseModel, 
        collection_query: dict = {}
    ):
        self.endpoint = endpoint_name
        self.model = model
        self.collection_query = collection_query
        def camel_case_to_snake_case(string):
            return ''.join(
                [
                    '_' + char.lower() if char.isupper()
                    else char 
                    for char in string
                ]
            ).lstrip('_')
        # how the model is referred to in text, i.e. RankedList --> ranked_list
        self.model_str = camel_case_to_snake_case(model.__name__)
        # connection to the database collection that houses docs of this model
        self.db_collection = getattr(db, self.model_str+"s")
        # read page size and sorting key settings from the api settings file,
        # throw informative exceptions if settings are not valid
        try:
            self.page_size = settings.NUMBER_ITEMS_IN_EACH_PAGE[self.model_str]
            if not isinstance(self.page_size, int): 
                raise ValueError
        except (ValueError, KeyError, IndexError, TypeError):
            raise InternalServerError(
                "NUMBER_OF_ITEMS_IN_EACH_PAGE setting (a dict "
                "in settings.py) should have the following "
                "format: Each key needs to be the snake_case "
                "name of a model, and the value needs to be an "
                "integer denoting how many instances of that "
                "model to include in each page of a response "
                "when a list of such model instances are requested. "
                "The current setting violates this requirement."
            )
        try:
            (
                self.sorting_field, 
                sorting_direction  
            ) = settings.SORT_ITEMS_BY_FIELD[self.model_str]
            if not isinstance(self.sorting_field, str): 
                raise ValueError
            if self.sorting_field not in model.__fields__.keys():
                raise ValueError
            if sorting_direction == "ascending":
                self.sort_reversed = False
            elif sorting_direction == "descending":
                self.sort_reversed = True
            else:
                raise ValueError
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise InternalServerError(
                "Entries in the SORT_ITEMS_BY_FIELD setting "
                "(a dict) should have the following format: "
                "Each key needs to be the snake_case name of "
                "a model, and the value needs to be a tuple "
                "with two elements. The first is the name of "
                "a field of the model, and the latter is either "
                "'ascending' or 'descending'. The current setting "
                "violates this requirement."
            )


    def paginate(self, requested_page=None):
        """
        Retrieve the list of items from the database, sort them, divide them
        into pages, and respond with the requested page.
        """
        
        # The default page in absence of a specific request is the first one
        if requested_page is None:
            requested_page = 1

        # Validate that the page number is an integer
        try:
            page = int(requested_page)
        except ValueError:
            raise BadRequest(
                f"Your request includes an invalid page parameter "
                f"({requested_page}). The value of the page "
                f"parameter needs to be an integer."
            )
            
        # Get the counts to help paginate
        num_all_docs = self.db_collection.count_documents(self.collection_query)
        num_docs_to_skip = self.page_size * (page - 1)
        num_pages = last_page = (num_all_docs // self.page_size) + 1

        # Let's make sure we don't get befuddled by a bad page parameter input
        if page < 1 or page > last_page:
            raise BadRequest(
                f"You have requested an invalid page number ({page}). "
                f"There are {num_pages} pages total, and the " 
                f"acceptable range for the page parameter value "
                f"is between and including 1 to {last_page}."
            )

        # We will retrieve all documents and sort them based on the relevant
        # sorting criterion, then divide this list into pages that only include
        # page_size items. Page sizes for each related endpoint, as well as how
        # to sort the items are defined in the api settings (settings.py in
        # rankor's root directory).
        #
        # For example, let's say we're listing all things (GET /rankor/things/),
        # the page size setting is 10 (each page has 10 things in it), sorting
        # field setting is by name, and we need to respond with page 6. We will
        # first retrieve all things from the database's things collection. We
        # will sort them by name, then skip the first 50 things (since they were
        # in the previous 5 pages), then use mongo's limit functionality to list
        # the 10 things that start from there (the 51st through 60th things).
        # This is page 6. We will also provide links to page 5 (previous_page),
        # page 7 (next_page), the very last page (last_page), and the url that
        # returns the exact same response (this_page). The last one is mostly
        # there to make it more convenient to keep track of which page you're
        # on.
        all_docs = self.db_collection.find(self.collection_query)
        sorted_docs = all_docs.sort(self.sorting_field)
        this_page_docs = sorted_docs.skip(num_docs_to_skip).limit(self.page_size)
        items_in_this_page = [to_jsonable_dict(self.model(**doc)) 
                              for doc in this_page_docs]
        
        # Create the links to this very page and the last page you can get
        links = {
            "this_page": {
                "href": url_for(self.endpoint, page=page, _external=True),
                "page": page
            },
            "last_page": {
                "href": url_for(self.endpoint, page=last_page, _external=True),
                "page": last_page
            }
        }
        # Add a link to the page before this one if this isn't the first page:
        if page > 1:
            links["previous_page"] = {
                "href": url_for(self.endpoint, page=page-1, _external=True),
                "page": page - 1
            }
        # Add a link to the page after this one if this isn't the last page:
        if page < last_page:
            links["next_page"] = {
                "href": url_for(self.endpoint, page=page+1, _external=True),
                "page": page + 1
            }

        # Return the full response
        return to_json(
            {
                "result": "success",
                "msg": (f"Successfully retrieved page {page} of {num_pages} "
                        f"for the list of all {num_all_docs} "
                        f"{self.model_str}s"),
                f"{self.model_str}s": items_in_this_page, 
                "_page": page,
                "_links": links,
                "http_status_code": 200
            }
        ), 200

