"""
RankedThing endpoint for a given RankedList: 
/rankor/rankedlists/<ranked_list_id>/ranked_things/

List RankedThings  |  GET /rankor/rankedlists/<ranked_list_id>/ranked-things/
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
from pagination import Paginator

# Exception imports
from rankor.errors import ResourceNotFoundInDatabaseError

# Api settings import
import settings

# Database interface import
from rankor import db


# The blueprint with all the RankedThing endpoints
# This will be registered to the Flask app
ranked_thing_endpoints = Blueprint('ranked_thing_endpoints', __name__)


# List RankedThings  |  GET /rankor/rankedlists/<ranked_list_id>/ranked_things/
@ranked_thing_endpoints.route(
    "/rankor/rankedlists/<ObjectId:ranked_list_id>/ranked-things/", 
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
         -X GET 'http://localhost:5000/rankor/rankedlists/a4325678901234567890bcd5/ranked-things/'

    """
    # Get the RankedList
    doc = db.ranked_lists.find_one({"_id": ranked_list_id})
    if doc is None:
        raise ResourceNotFoundInDatabaseError(
            resource_type = "ranked list",
            resource_id = ranked_list_id
        )
    # Get the full list of RankedThings in this RankedList
    ranked_things = RankedList(**doc).ranked_things
    # Instead of returning RankedThings with only Thing ids, use those ids to
    # pull the full data of each Thing
    for ranked_thing in ranked_things:
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

    return to_json(
        {
            "result": "success",
            "msg": (
                f"Successfully retrieved full list of ranked things "
                f"in the ranked list with id {ranked_list_id}"
            ),
            "ranked_things": ranked_things,
            "http_status_code": 200
        }
    ), 200



    # paginator = Paginator(
    #     endpoint_name = endpoint_name, 
    #     model = RankedThing,
    #     query = db.ranked_lists.find_one({{"_id": ranked_list_id}}),
    #     num_all_docs_in_db = num_all_ranked_things_in_ranked_list
    # )
    # return paginator.paginate(requested_page=requested_page)
