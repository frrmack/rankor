"""
Fight endpoints for a given RankedList: 
/rankor/ranked-lists/<ranked_list_id>/fights/

Arrange a new Fight   | GET    /rankor/ranked-lists/<ranked_list_id>/fights/new/
Save a Fight result   | POST   /rankor/ranked-lists/<ranked_list_id>/fights/      
Delete a Fight        | DELETE /rankor/ranked-lists/<ranked_list_id>/fights/<fight_id>
Get recorded Fights   | GET    /rankor/ranked-lists/<ranked_list_id>/fights/
Get Fights of a Thing | GET    /rankor/ranked-lists/<ranked_list_id>/fights/of-a-thing/<thing_id>
------------------------------------------------------------------------------
"""

# Python inspection imports 
# (to get the name of an endpoint from within)
from sys import _getframe

# Flask imports
from flask import Blueprint, request

# Python datetime import for timestamps
from datetime import datetime

# Encoder imports
from rankor.json import to_json

# Rankor model imports
from rankor.models import (Fight, 
                           RankedList,
                           PyObjectId)

# Pagination imports
from pagination import ListPaginator

# Exception imports
from rankor.errors import ResourceNotFoundInDatabaseError

# Database interface import
from rankor import db


# The blueprint with all the RankedThing endpoints
# This will be registered to the Flask app
fight_endpoints = Blueprint('fight_endpoints', __name__)


# processor function to fill the RankedThings response with Thing data from db
def fight_ids_to_full_fight_data(fight_ids, thing_id_to_filter_for = None):
    """
    Takes a list of Fight ids, pulls the data for each Fight from the database,
    and returns a list of actual Fight instances.
    """
    fights = []
    for fight_id in fight_ids:
        fight_doc = db.fights.find_one({"_id": PyObjectId(fight_id)})
        if fight_doc is None:
            raise ResourceNotFoundInDatabaseError(
                resource_type = "fight (referred to in this ranked list)",
                resource_id = fight_id
            )
        fights.append(Fight(**fight_doc))

    if thing_id_to_filter_for is not None:
        def thing_filter(fight):
            return thing_id_to_filter_for in fight.fighting_things
        fights = filter(thing_filter, fights)

    return fights



# Delete a Fight        | DELETE /rankor/ranked-lists/<ranked_list_id>/fights/<fight_id>
@fight_endpoints.route(
    "/rankor/ranked-lists/<ObjectId:ranked_list_id>/fights/<ObjectId:fight_id>", 
    methods=["DELETE"]
)
def delete_a_fight(ranked_list_id, fight_id):
    """
    DELETE request to remove a Fight from a RankedList and the database

    Example:
    curl -i -X DELETE 'http://localhost:5000/rankor/ranked-lists/a4325678901234567890bcd5/fights/12345678901234567890abcd/'   
    """
    # Update the RankedList in the database to remove ("pull" in mongo lingo)
    # this Fight from its fights field
    og_ranked_list = db.ranked_lists.update(
        { '_id': ranked_list_id },
        { '$pull': {'fights': fight_id} }
    )
    # Kill the Fight document with this id in the database.
    deleted_fight_doc = db.fights.find_one_and_delete({"_id": fight_id})
    # If unsuccessful, abort and send an HTTP 404 error
    if deleted_fight_doc is None:
        raise ResourceNotFoundInDatabaseError(
            resource_type="fight",
            resource_id=fight_id
        )
    # Success: Respond with the deleted Thing document that's 
    # no longer in the database 
    return to_json(
        {
            "result": "success",
            "msg": f"deleted fight with id {fight_id} of the ranked list with id {ranked_list_id}.",
            "fight": deleted_fight_doc,
            "http_status_code": 200
        },
    ), 200


# Get recorded Fights   | GET    /rankor/ranked-lists/<ranked_list_id>/fights/
@fight_endpoints.route(
    "/rankor/ranked-lists/<ObjectId:ranked_list_id>/fights/", 
    methods=["GET"]
)
def get_recorded_fights(ranked_list_id):
    """
    GET request to list all Fights fought for a given RankedList.

    This is a sorted list of Fights, paginated according to the api settings
    (settings.py in the root). While we read the entire list of fights from a
    RankedList and sort it in memory (if necessary), that list only contains
    Fight ids. We still need to read the Fight data for each of those from the
    database, so this endpoint is paginated like all other list endpoints to
    stay nimble. (Of course, like with any other paginated endpoint, one can
    always set the page size setting for Fights to a very large number and
    effectively disable pagination by shoving everything into a single page).

    For example: 
    curl -i 
         -X GET
         'http://localhost:5000/rankor/ranked-lists/a4325678901234567890bcd5/fights/'

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

    # Get the full list of Fight ids in this RankedList
    fight_ids = RankedList(**doc).fights

    # Paginate the fights list
    paginator = ListPaginator(
        endpoint_name = endpoint_name,
        model = Fight,
        item_list = fight_ids,
        final_page_list_processor = fight_ids_to_full_fight_data,
        url_for_kwargs = {"ranked_list_id": ranked_list_id}
    )
    return paginator.paginate(requested_page=requested_page)



# Get Fights of a Thing | GET    /rankor/ranked-lists/<ranked_list_id>/fights/of-a-thing/<thing_id>
@fight_endpoints.route(
    ("/rankor/ranked-lists/<ObjectId:ranked_list_id>/fights/"
     "of-a-thing/<ObjectId:thing_id>"), 
    methods=["GET"]
)
def get_fights_of_a_thing(ranked_list_id, thing_id):
    """
    GET request to list all Fights that a specific Thing has fought for a given
    RankedList.

    Like get_recorded_fights, this endpoint returns a sorted list of Fights,
    paginated according to the api settings (settings.py in the root). The only
    difference is that while get_recorded_fights provides all the fights in a
    RankedList, this one limits its scope to the fights that a specific Thing
    has fought (within the context of this RankedList, not all of its Fights in
    all RankedLists).

    For example: 
    curl -i 
         -X GET
         'http://localhost:5000/rankor/ranked-lists/a4325678901234567890bcd5/fights/of-a-thing/12345678901234567890abcd/'

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

    # Get the full list of Fight ids in this RankedList
    fight_ids = RankedList(**doc).fights

    # Prepare the final page list processor to also filter for our thing
    def filtered_fight_ids_to_fight_data(fight):
        return fight_ids_to_full_fight_data(
            fight,
            thing_id_to_filter_for = thing_id
        )

    # Paginate the fights list
    paginator = ListPaginator(
        endpoint_name = endpoint_name,
        model = Fight,
        item_list = fight_ids,
        final_page_list_processor = fight_ids_to_full_fight_data,
        url_for_kwargs = {"ranked_list_id": ranked_list_id}
    )
    return paginator.paginate(requested_page=requested_page)
