"""
RankedThing endpoint for a given RankedList: 
/rankor/ranked-lists/<ranked_list_id>/ranked_things/

List RankedThings  |  GET /rankor/ranked-lists/<ranked_list_id>/ranked-things/
"""

# Python inspection imports 
# (to get the name of an endpoint from within)
from sys import _getframe

# Flask imports
from flask import Blueprint, request

# Pymongo query imports
from pymongo.collection import ReturnDocument

# Python datetime import for timestamps
from datetime import datetime

# Encoder imports
from rankor.json import to_json

# Rankor model imports
from rankor.models import (RankedThing,
                           RankedList,
                           Thing,
                           PyObjectId)

# Pagination imports
from pagination import ListPaginator

# Exception imports
from rankor.errors import ResourceNotFoundInDatabaseError

# Api settings import
import settings

# Database interface import
from rankor import db


# The blueprint with all the RankedThing endpoints
# This will be registered to the Flask app
ranked_thing_endpoints = Blueprint('ranked_thing_endpoints', __name__)



# processor function to fill the RankedThings response with Thing data from db
def pull_actual_things_from_database(id_based_ranked_thing_list):
    """
    Turns a list of RankedThings that have the 'thing_id' field into a list of
    RankedThings that have actual Things in their 'thing' field.
    """
    for ranked_thing in id_based_ranked_thing_list:
        thing_doc = db.things.find_one(
            {"_id": PyObjectId(ranked_thing.thing_id)}
        )
        if thing_doc is None:
            raise ResourceNotFoundInDatabaseError(
                resource_type = "thing (referred to in this ranked list)",
                resource_id = ranked_thing.thing_id
            )
        ranked_thing.thing = Thing(**thing_doc)
        ranked_thing.thing_id = None
    return id_based_ranked_thing_list



# List RankedThings  |  GET /rankor/ranked-lists/<ranked_list_id>/ranked_things/
@ranked_thing_endpoints.route(
    "/rankor/ranked-lists/<ObjectId:ranked_list_id>/ranked-things/", 
    methods=["GET"]
)
def list_ranked_things(ranked_list_id):
    """
    GET request to list all RankedThings in a given RankedList.

    This is a sorted list of Things, from the first rank to the last rank, along
    with their Scores. All this information about each Thing is packaged in a
    RankedThing model instance. This list is what makes a RankedList "ranked"
    and a "list".

    Normally, list endpoints are are paginated. However, this endpoint requires
    reading the RankedList's Score for each Thing, then sorting them all based
    on these scores. Therefore, the entire sorted list of RankedThings is
    already in memory, pagination does not cut out on database read speeds or
    processing time, the overhead stays the same. A large number of Things may
    still slow the response down, but this will be negligible compared to other
    list endpoints unless we are talking about a huge number of Things.
    Therefore, this endpoint doesn't use pagination at this point. In the
    future, this can implement a ListPaginator, but it is a lower priority.

    For example: 
    curl -i 
         -X GET 'http://localhost:5000/rankor/ranked-lists/a4325678901234567890bcd5/ranked-things/'

    """
   # Python frame inspection code to get the name of this very function
    endpoint_name = "." + _getframe().f_code.co_name
    # Read the page parameter
    requested_page = request.args.get("page", 1)
    # Get the RankedList
    doc = db.ranked_lists.find_one({"_id": ranked_list_id})
    if doc is None:
        raise ResourceNotFoundInDatabaseError(
            resource_type = "ranked list",
            resource_id = ranked_list_id
        )

    # Get the full list of RankedThings in this RankedList
    ranked_things = RankedList(**doc).ranked_things

    # Paginate the ranked_things list
    paginator = ListPaginator(
        endpoint_name = endpoint_name,
        model = RankedThing,
        item_list = ranked_things,
        final_page_list_processor = pull_actual_things_from_database,
        url_for_kwargs = {"ranked_list_id": ranked_list_id}
    )
    return paginator.paginate(requested_page=requested_page)
