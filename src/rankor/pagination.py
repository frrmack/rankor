"""
Pagination code for endpoints.

This provides the logic with which endpoints that return long lists divide their
responses into multiple pages.
"""

# Flask imports
from flask import url_for
from rankor.models.pyobjectid import PyObjectIdString

# Error imports
from werkzeug.exceptions import BadRequest, InternalServerError

# Database cursor typing import (for explicit argument typing)
import pymongo

# Function typing import (for explicit argument typing)
from typing import Callable

# Model typing import (for explicit argument typing)
from rankor.models import JsonableModel

# Encoder imports
from rankor.json import to_jsonable_dict, to_json

# Utility imports (helper functions)
from rankor.utils import model_name_to_instance_name, list_is_sorted

# Api settings for page sizes and sorting keys
import settings


class BasePaginator(object):
    """
    A template class for paginators, which handle pagination for endpoints that
    return a rather long list of items. 
    
    Examples of such endpoints are endpoints.things.list_all_things,
    endpoints.ranked_lists.list_all_ranked_lists,
    endpoints.fights.recorded_fights, and endpoints.full_ranked_list_of_things.
    
    Since such lists can get long, the results are partitioned into a set number
    of pages. The page size (number of list items to include in each page), as
    well as what to sort the items by before partitioning into pages are
    determined in the api settings for each endpoint (settings.py in the root).

    This is a base template for specialized paginators to build upon. It
    provides shared initialization code, setting validation checks, common 
    pagination code such as creating the navigation links and packaging of 
    the page response. From this jumping point, different Paginators specialize 
    in handling different types of data. For example, QueryPaginator takes a 
    database query for a list of items and paginates that, while ListPaginator 
    handles an already existing list in memory.

    It provides a common template:
    You can ask for a specific page, for example (in list_all_things): 
    curl -X GET 'http://localhost:5000/rankor/things/?page=3'

    If you don't give a page parameter, the endpoint will return page 1. 
    The response will also include the page number and the links to the 
    following endpoint uris: 
    - this_page 
    - next_page     (if there is one) 
    - previous_page (if there is one) 
    - last_page 
    These links are there to help iterate over all results.
    """

    def __init__(
        self, 
        endpoint_name: str,
        model: JsonableModel,
        model_encoder: Callable = to_jsonable_dict,
        final_page_list_processor: Callable = None,
        url_for_kwargs: dict = {}
    ):
        self.endpoint_name = endpoint_name
        self.model = model
        self.model_encoder = model_encoder
        self.final_page_list_processor = final_page_list_processor
        self.url_for_kwargs = url_for_kwargs
        # Make sure we have _external=True in url_for() kwargs,
        # so that it returns an absolute url instead of a relative one
        self.url_for_kwargs.update({"_external": True})
        # self.model_str: how the model is referred to in text
        # i.e. RankedList --> ranked_list
        self.model_str = model_name_to_instance_name(model.__name__)
        # pagination settings
        (
            self.page_size, 
            self.sorting_field, 
            self.sorting_direction
        ) = self.read_and_validate_pagination_settings(model)
        self.num_all_docs = None


    def read_and_validate_pagination_settings(self, model):
        """
        Reads page size and sorting key settings from the api settings file,
        throws informative exceptions if settings are not valid.    
        """
        model_str = model_name_to_instance_name(model.__name__)
        # page size setting
        try:
            page_size = settings.NUMBER_ITEMS_IN_EACH_PAGE[model_str]
            if not isinstance(page_size, int): 
                raise ValueError(
                    f"Page size for this case is '{page_size}', "
                    f"which is not an integer."
                )
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise InternalServerError(
                f"NUMBER_OF_ITEMS_IN_EACH_PAGE setting (a dict "
                f"in settings.py) should have the following "
                f"format: Each key needs to be the snake_case "
                f"name of a model, and the value needs to be an "
                f"integer denoting how many instances of that "
                f"model to include in each page of a response "
                f"when a list of such model instances are requested. "
                f"The current setting violates this requirement. "
                f"{type(error).__name__}: {str(error)}"
            )
        # sorting field and sorting direction settings
        try:
            (
                sorting_field, 
                sorting_direction  
            ) = settings.SORT_ITEMS_BY_FIELD[model_str]
            if not isinstance(sorting_field, str): 
                raise ValueError(
                    f"The first element of the tuple, the field, "
                    f"is {repr(sorting_field)}, which is "
                    f"not a string."
                )
            if sorting_field not in model.__fields__.keys():
                raise ValueError(
                    f"The first element of the tuple, the field, "
                    f"is '{sorting_field}', which is not a "
                    f"valid field of the {model.__name__} model."
                )
            # sorting direction uses pymongo.ASCENDING or pymongo.DESCENDING
            if sorting_direction not in {"ascending", "descending"}:
                raise ValueError(
                    f"The second element of the tuple, the sorting direction, "
                    f"is '{sorting_direction}', which is neither 'ascending' "
                    f"nor 'descending'."
                )
            sorting_direction = getattr(pymongo, sorting_direction.upper())
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise InternalServerError(
                f"Entries in the SORT_ITEMS_BY_FIELD setting "
                f"(a dict) should have the following format: "
                f"Each key needs to be the snake_case name of "
                f"a model, and the value needs to be a tuple "
                f"with two elements. The first is the name of "
                f"a field of the model, and the latter is either "
                f"'ascending' or 'descending'. The current setting "
                f"violates this requirement. "
                f"{type(error).__name__}: {str(error)}"
            )
        return page_size, sorting_field, sorting_direction


    def paginate(self, requested_page=None):
        """
        Gets the items for the requested page; crafts and returns a response
        with them.
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
            
        # Calculate number of total pages (which is also last page's page number)
        num_pages = last_page = (self.num_all_docs // self.page_size) + 1

        # Let's make sure we don't get befuddled by a bad page parameter input
        if page < 1 or page > last_page:
            raise BadRequest(
                f"You have requested an invalid page number ({page}). "
                f"There are {num_pages} pages total, and the " 
                f"acceptable range for the page parameter value "
                f"is between and including 1 to {last_page}."
            )

        # Get the contents of the page
        items_in_this_page = self.get_page_items(page)

        # Apply final processor function (such as database reads to update each
        # item) if there is one given
        if self.final_page_list_processor is not None:
            items_in_this_page = self.final_page_list_processor(items_in_this_page)

        # Create the links to this very page and the last page you can get
        links = {
            "this_page": {
                "href": url_for(self.endpoint_name, 
                                **self.url_for_kwargs,
                                page=page),
                "page": page
            },
            "last_page": {
                "href": url_for(self.endpoint_name, 
                                **self.url_for_kwargs,
                                page=last_page),
                "page": last_page
            }
        }
        # Add a link to the page before this one if this isn't the first page:
        if page > 1:
            links["previous_page"] = {
                "href": url_for(self.endpoint_name, 
                                **self.url_for_kwargs,
                                page=page-1),
                "page": page - 1
            }
        # Add a link to the page after this one if this isn't the last page:
        if page < last_page:
            links["next_page"] = {
                "href": url_for(self.endpoint_name, 
                                **self.url_for_kwargs,
                                page=page+1),
                "page": page + 1
            }

        # Return the full response
        return to_json(
            {
                "result": "success",
                "msg": (f"Successfully retrieved page {page} of {num_pages} "
                        f"for the list of all {self.num_all_docs} "
                        f"{self.model_str}s"),
                f"{self.model_str}s": items_in_this_page, 
                "_page": page,
                f"_num_{self.model_str}s_in_page": len(items_in_this_page),
                "_links": links,
                "http_status_code": 200
            }
        ), 200


    def get_page_items(self, page: int) -> list:
        """
        Each specialized Paginator that inherits from BasePaginator needs to
        override this method to implement its specific way to retrieve and
        process the items in the requested page.
        """
        raise NotImplementedError("""This is the BasePaginator, which is a
                                  template for other specialized Paginators. It
                                  does not have a specific pagination algorithm.
                                  A subclass of this should be used to paginate
                                  responses instead.""")



class QueryPaginator(BasePaginator):
    """
    A class that handles pagination for endpoints, which return a list of items
    retrieved from a single database query.
    
    Examples of such endpoints:
    - endpoints.things.list_all_things
    - endpoints.ranked_lists.list_all_ranked_lists

    It takes two specialized arguments beyond standard BasePaginator args:
    - query:                a db query that retrieves a list of documents
    - num_all_docs_in_db:   size of the query (how many docs it retrieves)  

    You can ask for a specific page, for example (in list_all_things):
    curl -X GET 'http://localhost:5000/rankor/things/?page=3'

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
        model: JsonableModel,
        query: pymongo.cursor.Cursor,
        num_all_docs_in_db: int,
        model_encoder: Callable = to_jsonable_dict,
        url_for_kwargs: dict = {}
    ):
        super(QueryPaginator, self).__init__(
            endpoint_name=endpoint_name,
            model=model,
            model_encoder=model_encoder,
            url_for_kwargs=url_for_kwargs
        )
        self.query = query
        self.num_all_docs = num_all_docs_in_db


    def get_page_items(self, page):
        """
        We will retrieve all documents and sort them based on the relevant
        sorting criterion, then divide this list into pages that only include
        page_size items. Page sizes for each related endpoint, as well as how to
        sort the items are defined in the api settings (settings.py in rankor's
        root directory). 
        
        Sorting, skipping forward to the current page, and limiting the number
        of items to page_size are all applied to the query cursor before reading
        the page's documents from the database.
        
        For example, let's say we're listing all things (GET /rankor/things/),
        the page size setting is 10 (each page has 10 things in it), sorting
        field setting is by "name", and we need to respond with page 6. We will
        query all things from the database's things collection (the query to do
        this will be given when the Paginator instance was created). We will add
        a step to sort by name field, then another to skip the first 50 things
        (since they were in the previous 5 pages), then a limit step to list
        only 10 things that start from there. Once we execute the command to
        iterate over the cursor in a list comprehension, we will get a list of
        51st through 60th Thing documents from the database. We will initiate a
        Thing model instance with each of this documents, and finally, we will
        use the model_encoder we're given to encode these Things. We return this
        list of encoded Things as the page items for page 6.
        
        Later, in the paginate method, we will also provide links to page 5
        (previous_page), page 7 (next_page), the very last page (last_page), and
        the url that returns this exact response (this_page). That last one is
        there in case to you need to keep track of which page you're on.
        """
        # Sort
        sorted_docs = self.query.sort(self.sorting_field, 
                                      self.sorting_direction)
        # Slice
        num_docs_to_skip = self.page_size * (page - 1)
        page_docs = sorted_docs.skip(num_docs_to_skip).limit(self.page_size)
        # Respond
        return [self.model_encoder(self.model(**doc)) for doc in page_docs]       



class ListPaginator(BasePaginator):
    """
    A class that handles pagination for endpoints, which takes an existing list
    of items and paginates said link.
    
    Examples of such endpoints:
    - endpoints.fights.recorded_fights
    - endpoints.ranked_things.list_ranked_things

    A use case for this paginator is when we have a list of document ids and we 
    want to respond with a list of the actual documents these ids refer to. To 
    respond fast and in short chunks, we partition the id list into pages, and 
    only read the full documents for one page at a time. In this use case, the 
    pulling of the documents using ids can be done utilizing the 
    final_page_list_processor argument.

    It takes one specialized argument beyond standard BasePaginator args: -
    - item_list:                the list we are paginating

     You can ask for a specific page, for example (in list_ranked_things):
    curl -X GET 'http://localhost:5000/rankor/ranked-lists/<id>/ranked-things?page=3'

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
        model: JsonableModel,
        item_list: list,
        final_page_list_processor: Callable = None,
        url_for_kwargs: dict = {}
    ):
        super(ListPaginator, self).__init__(
            endpoint_name=endpoint_name,
            model=model,
            final_page_list_processor=final_page_list_processor,
            url_for_kwargs=url_for_kwargs
        )
        self.item_list = item_list
        self.num_all_docs = len(item_list)
        # Validate that item_list items are instances of the declared model
        # or id strings
        for item in item_list:
            try:
                PyObjectIdString.validate(item)
            except ValueError:
                item_is_id_string = False
            else:
                item_is_id_string = True
            if not isinstance(item, model) and \
                not item_is_id_string:
                raise ValueError(f"The following item in the list given to "
                                 f"ListPaginator is not an instance of "
                                 f"{model.__name__} or an id string: {item}. "
                                 f"It is a {type(item).__name__}.")


    @property
    def sorted_item_list(self):
        """
        Returns a sorted version of the provided item list.
        
        Pagination needs to partition a sorted list into pages, we need to make
        sure that our list is indeed sorted. This method does that.

        We can just go ahead and tell python to sort it regardless of if it may
        already be sorted or not, that's the sensible approach to make sure it's
        sorted. However, if it is already sorted, quicksort may end up closer to
        O(n^2) (if an early item is chosen as a pivot) instead of O(nlogn), so
        this checks if it's already sorted with an O(n) operation first to avoid
        that.
        
        In almost all practical rankor use cases, this won't matter as python's
        implementation won't directly fall into this extremely unlucky pivot
        selection by taking the first element, and n won't be nearly large
        enough for this to make any difference anyway. We could just go ahead
        and sort it without checking, but technically it could matter if a list
        gets REALLY long. You can safely consider the 'is it already sorted?'
        check unecessary overengineering "just in case".
        """
        # Define the sorting direction and sorting key first
        is_sorting_reversed = {
            pymongo.ASCENDING: False,
            pymongo.DESCENDING: True,
        }
        try:
            sort_reversed = is_sorting_reversed[self.sorting_direction]
        except KeyError:
            raise ValueError("Sorting direction is not set to either ascending "
                            f"or descending in settings for {self.model_str}.")
        def sorting_key(model):
            return getattr(model, self.sorting_field)
                
        # Now either directly return the list if already sorted,
        # or return a sorted version if it isn't
        try:
            if list_is_sorted(
                self.item_list, 
                key = sorting_key, 
                reverse = sort_reversed
            ):
                return self.item_list
            else:
                return sorted(
                    self.item_list,
                    key = sorting_key,
                    reverse = sort_reversed
                )
        except AttributeError:
            # if the items do not have the sorting field, this means that the
            # items are not instances of the model, but another data type (such
            # as the ids of model documents in the database). Since we do not
            # have access to that information in that case (and pulling it from
            # the db would need to be done for the whole list, defeating the
            # goal of pagination to be fast and nimble), we can't sort by field,
            # we will therefore just return the list as is
            return self.item_list


    def get_page_items(self, page):
        """
        Sorts the list if not already sorted (via the sorted_item_list
        property), then figures out a slicing index corresponding to the
        requested page. 
        
        For example, let's say we're listing all RankedThings of a RankedList
        (GET /rankor/ranked-lists/<ranked-list-id>/ranked-things/?page=6), the
        page size setting is 10 (each page has 10 RankedThings in it), sorting
        field setting is (somewhat obviously) "rank", and we need to respond
        with page 6. An endpoint code will already have pulled the specific
        RankedList, and it will have provided us with the list
        RankedList.ranked_things. We will sort the list if not already sorted
        then figure out the indices of the list that denote our page. In this
        case they are [51:61], since the 6th page has the 51st to 61st ranks. We
        will slice the list to this sublist of ten. Finally, we will apply a
        final_page_list_processor, which reads the Thing id in each list element
        and reads the full Thing from the database to replace it in each of the
        ten RankedThings. This is what we return.
        
        Later, in the paginate method, we will also provide links to page 5
        (previous_page), page 7 (next_page), the very last page (last_page), and
        the url that returns this exact response (this_page). That last one is
        there in case to you need to keep track of which page you're on.
        """
        from_item = self.page_size * (page - 1)
        to_item = from_item + self.page_size
        return self.sorted_item_list[from_item:to_item]
