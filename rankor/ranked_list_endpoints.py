"""
RankedList endpoints: /rankor/rankedlists/

Create a new RankedList    |   POST    /rankor/rankedlists/
Edit a RankedList          |   PUT     /rankor/rankedlists/<ranked_list_id>/
Delete a RankedList        |   DELETE  /rankor/rankedlists/<ranked_list_id>/
Delete ALL RankedLists     |   DELETE  /rankor/rankedlists/delete-all/
List all RankedLists       |   GET     /rankor/rankedlists/
Get one RankedList         |   GET     /rankor/rankedlists/<ranked_list_id>/
[Raw data of a RankedList] |   GET     /rankor/rankedlists/raw/<ranked_list_id>/
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
from rankor.models import (Thing, 
                           Fight, 
                           RankedList, 
                           Score, 
                           PyObjectId, 
                           PyObjectIdString)


# Pagination imports
from pagination import Paginator

# Exception imports
from werkzeug.exceptions import Forbidden
from rankor.errors import (ResourceNotFoundInDatabaseError,
                           SameNameResourceAlreadyExistsError)

# Api settings import
import settings

# Database interface import
from rankor import db


# The blueprint with all the RankedList endpoints
# This will be registered to the Flask app
ranked_list_endpoints = Blueprint('ranked_list_endpoints', __name__)


# The following function is used to represent a ranked_list whenever an endpoint
# needs to respond with one. It provides a much more useful response than
# directly returning how a ranked_list is stored in the database. You can check
# the last endpoint here, raw_data_of_a_ranked_list, to see how and why the
# response cooked below is chosen as the standard ranked list representation.
def ranked_list_response(ranked_list):
    """
    Creates a response with the useful information of a RankedList and links to
    other (paginated) endpoints for the full list of things (ranked with scores)
    and all the recorded fights within this RankedList. 
    """
    # Get the RankedList summary with practical information useful for a user
    ranked_list_representation = ranked_list.summary_dict()

    # top_3_things & last_3_fights only have id strings for Things and Fights.
    # Retrieve their actual data to respond with. 
    # First the Things:
    for thing_score_dict in ranked_list_representation["top_3_things"]:
        thing_id = thing_score_dict["thing"]
        thing_doc = db.things.find_one({"_id": PyObjectId(thing_id)})
        if thing_doc is None:
            raise ResourceNotFoundInDatabaseError(
                resource_type = "thing (referred to in this ranked list)",
                resource_id = thing_id
            )
        thing_score_dict["thing"] = Thing(**thing_doc).to_jsonable_dict()
    # Now the Fights:
    last_3_fights_with_details = []
    for fight_id in ranked_list_representation["last_3_fights"]:
        fight_doc = db.fights.find_one({"_id": PyObjectId(fight_id)})
        if fight_doc is None:
            raise ResourceNotFoundInDatabaseError(
                resource_type = "fight (referred to in this ranked list)",
                resource_id = fight_id
            )
        last_3_fights_with_details.append(Fight(**fight_doc).to_jsonable_dict())
    ranked_list_representation["last_3_fights"] = last_3_fights_with_details

    # Add links to the paginated endpoints for both the ranked list of all
    # Things (with their Scores) and the list of all fights fought within the
    # context of this RankedList.
    links = {
        "full_ranked_list_of_things": {
            "href": f"/rankor/rankedlists/{ranked_list.id}/ranks/"
        },
        "recorded_fights": {
            "href": f"/rankor/rankedlists/{ranked_list.id}/fights/"
        }
    }

    # The response dict includes all this
    return {
        "data": ranked_list_representation,
        "_links": links
    }



# Create a new RankedList   |   POST    /rankor/rankedlists/
@ranked_list_endpoints.route(
    "/rankor/rankedlists/", 
    methods=["POST"]
)
def create_a_new_ranked_list():
    """
    POST request to directly create a new RankedList

    The only field you can define for a new RankedList is:
    name: str

    Attach the contents of the new RankedList as data in JSON format.
    For example:
    curl -d '{"name": "My Favorite Movies"}' 
         -H "Content-Type: application/json" 
         -X POST http://localhost:5000/rankor/rankedlists/
    """
    # Retrieve the data from the request and record the timestamp of creation
    new_ranked_list_data = request.get_json()
    new_ranked_list_data["time_created"] = datetime.utcnow()

    # Check the database to ensure that there isn't another one with the exact 
    # same name, raise an error if it does
    if "name" in new_ranked_list_data:
        same_name_ranked_list = db.ranked_lists.find_one(
            {"name": new_ranked_list_data["name"]}
        )
        if same_name_ranked_list:
            raise SameNameResourceAlreadyExistsError(
                resource_type="ranked list",
                same_name_resource=same_name_ranked_list
            )

    # A RankedList has a dictionary that maps each thing to its score
    # in this RankedList, we are going to initialize the scores for all of them
    # with the default initialization scores defined in the api settings.
    # It also has a list of fights, which will be empty now, at the time
    # of creation. 
    things_of_ranked_list = [Thing(**doc) for doc in db.things.find()]
    initial_scores = {
        PyObjectIdString(thing.id): Score() 
        for thing in things_of_ranked_list
    }
    new_ranked_list_data["thing_scores"] = initial_scores
    new_ranked_list_data["fights"] = []

    # Create, validate, and insert the RankedList instance into the database,
    # retrieve the auto-assigned id to include in the success response
    new_ranked_list = RankedList(**new_ranked_list_data)
    insert_result = db.ranked_lists.insert_one(new_ranked_list.to_bsonable_dict())
    new_ranked_list.id = insert_result.inserted_id

    # Success: respond with the new ranked list
    return to_json(
        {
            "result": "success",
            "msg": (
                f"New ranked list created and "
                f"given id {new_ranked_list.id}"
            ),
            "ranked_list": ranked_list_response(new_ranked_list),
            "http_status_code": 200
        }
    ), 200

        



# Edit a RankedList         |   PUT     /rankor/rankedlists/<ranked_list_id>/
@ranked_list_endpoints.route(
    "/rankor/rankedlists/<ObjectId:ranked_list_id>/", 
    methods=["PUT"]
)
def edit_a_ranked_list(ranked_list_id):
    """
    PUT request to update the data of a RankedList that already exists in the
    database.

    By default, you can only edit the basic data of a RankedList with this
    endpoint, which is just its name and score_used_to_rank (and the
    time_created timestamp if you want to override the automatically assigned
    value for some reason). Fights can be saved to or deleted from RankedLists
    via other endpoints (fight_endpoints.py), and this is normally the only way
    to influence the fights list and (indirectly) the thing_scores dict of a
    RankedList. If settings.ALLOW_MANUAL_EDITING_OF_RANKEDLIST_FIGHTS_OR_SCORES
    is set to True instead of the default False, this endpoint will allow you to
    directly update these fields. Doing this is NOT recommended, as it's not a
    good way of handling the data, it's prone to introducing silent errors that
    will come back to bite you later, and it's easy to mess up unless you know
    exactly what you're doing.

    Properties of a RankedList, such as top_3_things or last_3_fights are not
    stored, but calculated using the other fields. Therefore they are never
    editable. They will change based on the fights list and the thing_scores
    dict.

    Example (name change from 'My Favorite Movies' to 'Action Movie Ranked 
    List with Max'):
    curl -d '{"name": "Action Movie Ranked List with Max"}'
         -H "Content-Type: application/json" 
         -X PUT http://localhost:5000/rankor/things/12345678901234567890ffff/       
    """
    # Retrieve the request data. 
    update_data = request.get_json()
    
    # Raise a 403 Forbidden Error if they are trying to edit the untouchables
    # (unless they are explicitly allowed in the settings)
    if not settings.ALLOW_MANUAL_EDITING_OF_RANKEDLIST_FIGHTS_OR_SCORES:
         if "fights" in update_data or "thing_scores" in update_data:
              raise Forbidden("Directly editing the thing_scores or the fights "
                              "of a ranked list using this endpoint is not allowed. "
                              "You can affect these indirectly through saving new "
                              "fights or deleting existing fights using the .../fights/"
                              " endpoints of a ranked list. If the "
                              "ALLOW_MANUAL_EDITING_OF_RANKEDLIST_FIGHTS_OR_SCORES "
                              "setting of the api is set to True, editing them "
                              "directly here gets allowed, but it is not recommended.")

    # Retrieve the update target document from the database to fill the remaining
    # essential fields for full validation
    doc_to_update = db.ranked_lists.find_one({"_id": ranked_list_id})
    if doc_to_update is None:
        raise ResourceNotFoundInDatabaseError(
            resource_type="ranked list",
            resource_id=ranked_list_id
            )
    for field in ("name", "thing_scores", "fights"):
         if field not in update_data:
              update_data[field] = doc_to_update[field]

    # Validate through instantiating it as a RankedList and add a timestamp
    # to record when this update happened.
    validated_update = RankedList(**update_data)
    validated_update.time_edited = datetime.utcnow()

    # Apply these updates to the given fields in the database.
    updated_doc = db.ranked_lists.find_one_and_update(
        {"_id": ranked_list_id},
        {"$set": validated_update.to_bsonable_dict()},
        return_document=ReturnDocument.AFTER
        )

    # If unsuccessful, abort with a 404 Not Found error
    if updated_doc is None:
        raise ResourceNotFoundInDatabaseError(
            resource_type="ranked list",
            resource_id=ranked_list_id
            )
    # Success: respond with the new, updated RankedList
    edited_ranked_list = RankedList(**updated_doc)
    return to_json(
        {
            "result": "success",
            "msg": f"Successfully edited ranked list with id {ranked_list_id}",
            "ranked_list": ranked_list_response(edited_ranked_list),
            "http_status_code": 200
        }
    ), 200



# Delete a RankedList       |   DELETE  /rankor/rankedlists/<ranked_list_id>/
@ranked_list_endpoints.route(
    "/rankor/rankedlists/<ObjectId:ranked_list_id>/", 
    methods=["DELETE"]
)
def delete_a_ranked_list(ranked_list_id):
    """
    DELETE request to remove a RankedList from the database

    Example:
    curl -i -X DELETE 'http://localhost:5000/rankor/rankedlists/12345678901234567890ffff/'   
    """
    deleted_doc = db.ranked_lists.find_one_and_delete(
        {"_id": ranked_list_id}
    )
    if deleted_doc is None:
        raise ResourceNotFoundInDatabaseError(
            resource_type="ranked list",
            resource_id=ranked_list_id
        )
    # Success: Respond with the basic data of the deleted document that's no
    # longer in the database
    deleted_doc.pop("thing_scores", None)
    deleted_doc.pop("fights", None)
    return to_json(
        {
            "result": "success",
            "msg": f"Ranked list with id {ranked_list_id} deleted.",
            "ranked_list": {"data": deleted_doc},
            "http_status_code": 200
        }
    ), 200



# Delete ALL RankedLists    |   DELETE  /rankor/rankedlists/delete-all/
@ranked_list_endpoints.route(
    "/rankor/rankedlists/delete-all/", 
    methods=["DELETE"]
)
def delete_ALL_ranked_lists():
    """
    DELETE request to delete ALL existing RankedLists
    This nuclear bomb purges the entire ranked_lists collection in the database
    It's basically an endpoint to reset back to factory settings to start over

    Example: curl -i -X DELETE 'http://localhost:5000/rankor/rankedlists/delete-all/'   
    """
    deletion_info = db.ranked_lists.delete_many({})
    # Success: Respond with the number of deleted documents
    return to_json(
        {
            "result": "success",
            "msg": f"{deletion_info.deleted_count} ranked lists deleted",
            "http_status_code": 200
        }
    ), 200



# List all RankedLists    |   GET   /rankor/rankedlists/     
@ranked_list_endpoints.route(
    "/rankor/rankedlists/", 
    methods=["GET"]
)
def list_all_ranked_lists():
    """
    GET request to list all RankedLists in the database.

    Since this list can get long, the results are paginated.
    Each page will list a set number of RankedLists, this page size is determined
    in the api settings (in the root directory).

    You can ask for a specific page, for example:
    curl -i -X GET 'http://localhost:5000/rankor/rankedlists/?page=5'

    If you don't give a page parameter, it will return page 1. The response will
    also include the page number and the links to the following endpoint uris:
    - this_page
    - next_page     (if there is one)
    - previous_page (if there is one)
    - last_page
    These links are there to help iterate over all results.
    """
    # Python frame inspection code to get the name of this very function
    endpoint_name = "." + _getframe().f_code.co_name
    # Read the page parameter
    requested_page = request.args.get("page", 1)
    # Get the paginator for our case (list of all RankedLists in db.ranked_lists)
    # and use it to respond with the requested page
    paginator = Paginator(endpoint_name=endpoint_name, model=RankedList)
    return paginator.paginate(requested_page=requested_page)



# Get one RankedList        |   GET     /rankor/rankedlists/<ranked_list_id>/
@ranked_list_endpoints.route(
    "/rankor/rankedlists/<ObjectId:ranked_list_id>/", 
    methods=["GET"]
)
def get_one_ranked_list(ranked_list_id): 
    """
    GET request to retrieve details of a single RankedList using its id. 
    
    Besides the basic data of the RankedList, it provides some useful summary
    data, such as "number of fights", "top_3_things", "last_3_fights". It also
    contains links to the relevant paginated endpoints to a) get the ranked
    Thing list with their scores, and b) details of all the Fights fought within
    the context of this RankedList.

    For example: 
    curl -i -X GET 'http://localhost:5000/rankor/rankedlists/raw/a4325678901234567890bcd5/'
    """
    # Retrieve the RankedList document with this id from the database or raise 
    # an HTTP 404 if you can't find it
    doc = db.ranked_lists.find_one({"_id": ranked_list_id})
    if doc is None:
        raise ResourceNotFoundInDatabaseError(
            resource_type = "ranked list",
            resource_id = ranked_list_id
        )
    return to_json(
        {
            "result": "success",
            "msg": (
                f"Successfully retrieved ranked list "
                f"with id {ranked_list_id}"
            ),
            "ranked_list": ranked_list_response(RankedList(**doc)),
            "http_status_code": 200
        }
    ), 200

    
    
    ranked_list_response(RankedList(**doc)),200



# [Raw data of a RankedList] |   GET  /rankor/rankedlists/raw/<ranked_list_id>/
@ranked_list_endpoints.route(
    "/rankor/rankedlists/raw/<ObjectId:ranked_list_id>/", 
    methods=["GET"]
)
def raw_data_of_a_ranked_list(ranked_list_id): 
    """
    Special GET request to retrieve the underlying raw data for a single
    RankedList using its id. Not intented for regular use, just for
    development/debugging purposes---to check under the hood if necessary.
    
    This returns how a RankedList is stored in the database. It doesn't have
    informative properties of the regular RankedList endpoint (like
    "top_3_things", "number of fights", "last_3_fights"), no links to a
    paginated ranked_things list with Thing details, or a paginated fights list
    with Fight details. Besides the basic data (like "name", "time_created",
    "time_edited", "score_used_to_rank"), it has a dict that maps Thing ids to
    Score data ("thing_scores"), and a list of fight ids ("fights"). 
    
    No pagination, just a json encoding of the full single bson document storing
    the raw data of the RankedList. With only id references to Things and
    Fights, it's not too useful to a user facing front end app for most use
    cases. It is convenient to check things during development or debugging, and
    potentially for a few behind-the-scenes use cases.

    For example: curl -i -X GET
    'http://localhost:5000/rankor/rankedlists/raw/a4325678901234567890bcd5/'
    """
    # Retrieve the document with this id from the database and respond
    # with it, or raise an HTTP 404 if you can't find it
    doc = db.ranked_lists.find_one({"_id": ranked_list_id})
    if doc is None:
        raise ResourceNotFoundInDatabaseError(
            resource_type = "ranked list",
            resource_id = ranked_list_id
        )
    # Success: respond with the raw ranked list 
    return to_json(
        {
            "result": "success",
            "msg": (
                f"Successfully retrieved raw data of ranked list "
                f"with id {ranked_list_id}"
            ),
            "ranked_list_raw_data": RankedList(**doc).to_jsonable_dict(),
            "http_status_code": 200
        }
    ), 200


