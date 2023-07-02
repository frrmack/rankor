"""
Fight endpoints for a given RankedList: 
/rankor/ranked-lists/<ranked_list_id>/fights/

Arrange a new Fight    | GET    /rankor/ranked-lists/<ranked_list_id>/fights/new/
Save a Fight result    | POST   /rankor/ranked-lists/<ranked_list_id>/fights/      
Delete a Fight         | DELETE /rankor/ranked-lists/<ranked_list_id>/fights/<fight_id>/
List recorded Fights   | GET    /rankor/ranked-lists/<ranked_list_id>/fights/
List Fights of a Thing | GET    /rankor/ranked-lists/<ranked_list_id>/fights/of-a-thing/<thing_id>/
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
                           PyObjectId,
                           PyObjectIdString)

# Pagination imports
from rankor.pagination import ListPaginator

# Exception imports
from rankor.errors import ResourceNotFoundInDatabaseError

# Database interface import
from rankor.database import get_database_connection
db = get_database_connection()

# Api configuration import
from rankor.config import rankor_config


# The blueprint with all the RankedThing endpoints
# This will be registered to the Flask app
fight_endpoints = Blueprint('fight_endpoints', __name__)


# processor function to fill the RankedThings response with Thing data from db
def fight_ids_to_full_fight_data(
    fight_ids: list, 
    thing_id_to_filter_for: PyObjectIdString = None
):
    """
    Takes a list of Fight ids, pulls the data for each Fight from the database,
    and returns a list of actual Fight instances.
    """
    # retrieve all fight data for these fight ids
    fights = []
    for fight_id in fight_ids:
        fight_doc = db.fights.find_one({"_id": PyObjectId(fight_id)})
        if fight_doc is None:
            raise ResourceNotFoundInDatabaseError(
                resource_type = "fight (referred to in this ranked list)",
                resource_id = fight_id
            )
        fights.append(Fight(**fight_doc))

    # filter out just our thing's fights if needed
    if thing_id_to_filter_for is not None:
        def thing_filter(fight):
            return (
                PyObjectIdString(thing_id_to_filter_for) 
                in fight.fighting_things
            )
        fights = list( 
            filter(thing_filter, fights) 
        )

    return fights



# Save a Fight result   | POST   /rankor/ranked-lists/<ranked_list_id>/fights/      
@fight_endpoints.route(
    "/rankor/ranked-lists/<ObjectId:ranked_list_id>/fights/", 
    methods=["POST"]
)
def save_a_fight_result(ranked_list_id):
    """
    POST request to directly add a Fight (with a result) to the database in its
    own collection and to the RankedList it belongs to.

    Fields to provide for a saved Fight are:
    ranked_list:        The id string (PyObjectIdString)
                        of the RankedList the Fight belongs to 
    fighting_things:    A list of two id strings (PyObjectIdString), 
                        the ids of the fighting Things
    result:             one of these three strings (str): 
                        'FIRST_THING_WINS', 'SECOND_THING_WINS', 'DRAW'

    Attach the contents of the new Thing as data in JSON format.
    Example:
    curl -d '{"name": "Terminator", 
              "image_url": "https://m.media-amazon.com/images/I/61qCgQZyhOL._AC_SY879_.jpg", 
              "other_data": {"director": "James Cameron", "year": 1982}
             }' 
         -H "Content-Type: application/json" 
         -X POST http://localhost:5000/rankor/things/
    """
    # Retrieve the data from the request and record the timestamp
    new_fight_data = request.get_json()
    new_fight_data["time_fought"] = datetime.utcnow()

    # Create the new Fight instance, which also validates its data using pydantic,
    # inserts it into the database, and retrieves the _id that mongodb automatically 
    # assigned it. 
    new_fight = Fight(**new_fight_data)
    insert_result = db.fights.insert_one(new_fight.to_bsonable_dict())
    new_fight.id = insert_result.inserted_id

    # Save the new Fight's id to the beginning of the fights list of the RankedList 
    og_ranked_list = db.ranked_lists.find_one_and_update(
        { '_id': ranked_list_id },
        { 
            '$push': {
                'fights': {
                    '$each': [PyObjectIdString(new_fight.id)],
                    '$position': 0
                }
            }
        } 
    )    

    # Success: respond in json with the recorded Fight
    return to_json(
        {
            "result": "success",
            "msg": (f"Fight is given id {new_fight.id} and recorded to "
                    f"RankedList with id {ranked_list_id}."),
            "fight": new_fight,
            "http_status_code": 200
        },
    ), 200



# Delete a Fight        | DELETE /rankor/ranked-lists/<ranked_list_id>/fights/<fight_id>/
@fight_endpoints.route(
    "/rankor/ranked-lists/<ObjectId:ranked_list_id>/fights/<ObjectId:fight_id>/", 
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
    og_ranked_list = db.ranked_lists.find_one_and_update(
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


# List recorded Fights   | GET    /rankor/ranked-lists/<ranked_list_id>/fights/
@fight_endpoints.route(
    "/rankor/ranked-lists/<ObjectId:ranked_list_id>/fights/", 
    methods=["GET"]
)
def list_recorded_fights(ranked_list_id):
    """
    GET request to list all Fights fought for a given RankedList.

    This is a sorted list of Fights, paginated according to the api
    configuration (src/rankor/config/rankor_config.toml). While we read the
    entire list of fights from a RankedList and sort it in memory (if
    necessary), that list only contains Fight ids. We still need to read the
    Fight data for each of those from the database, so this endpoint is
    paginated like all other list endpoints to stay nimble. (Of course, like
    with any other paginated endpoint, one can always set the page size setting
    for Fights to a very large number and effectively disable pagination by
    shoving everything into a single page).

    For example: curl -i 
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

    # Special case: if the sorting field of fights is not the default 'latest
    # fight at the top', we have to pull all the fight data so the paginator can
    # sort on the non-default field determined by the rankor configuration.
    # Doing this defeats the agility purpose of pagination, as we can no longer
    # avoid reading ALL the data rather than just what's on one page. Therefore
    # it is not recommended to change this setting, as described in the
    # configuration file itself.
    if rankor_config['sorting']['fight'] == {
        'direction': 'descending', 
        'field': 'time_fought'
    }:
        item_list = fight_ids
        final_page_list_processor = fight_ids_to_full_fight_data
    else:
        item_list = fight_ids_to_full_fight_data(fight_ids)
        final_page_list_processor = None

    # Paginate the fights list
    paginator = ListPaginator(
        endpoint_name = endpoint_name,
        model = Fight,
        item_list = item_list,
        final_page_list_processor = final_page_list_processor,
        url_for_kwargs = {"ranked_list_id": ranked_list_id}
    )
    return paginator.paginate(requested_page=requested_page)



# List Fights of a Thing | GET    /rankor/ranked-lists/<ranked_list_id>/fights/of-a-thing/<thing_id>/
@fight_endpoints.route(
    ("/rankor/ranked-lists/<ObjectId:ranked_list_id>/fights/"
     "of-a-thing/<ObjectId:thing_id>/"), 
    methods=["GET"]
)
def list_fights_of_a_thing(ranked_list_id, thing_id):
    """
    GET request to list all Fights that a specific Thing has fought for a given
    RankedList.

    Like get_recorded_fights, this endpoint returns a sorted list of Fights,
    paginated according to the api configuration
    (src/rankor/config/rankor_config.toml). The only difference is that while
    get_recorded_fights provides all the fights in a RankedList, this one limits
    its scope to the fights that a specific Thing has fought (within the context
    of this RankedList, not all of its Fights in all RankedLists).

    For example: curl -i 
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

    # Retrieve the fight data so that we can see which things are involved in
    # each fight and filter out the ones where our thing has fought.
    fights_of_our_thing = fight_ids_to_full_fight_data(
        fight_ids,
        thing_id_to_filter_for = thing_id
    )

    # Paginate the fights list
    paginator = ListPaginator(
        endpoint_name = endpoint_name,
        model = Fight,
        item_list = fights_of_our_thing,
        url_for_kwargs = {
            "ranked_list_id": ranked_list_id,
            "thing_id": thing_id
        }
    )
    return paginator.paginate(requested_page=requested_page)
