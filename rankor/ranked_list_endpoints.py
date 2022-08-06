# RankedList endpoints: /rankor/rankedlists/
#
# Create a new RankedList   |   POST    /rankor/rankedlists/
# Delete a RankedList       |   DELETE  /rankor/rankedlists/<ranked_list_id>
# Edit a RankedList         |   PUT     /rankor/rankedlists/<ranked_list_id>
# List all RankedLists      |   GET     /rankor/rankedlists/
# Get one RankedList        |   GET     /rankor/rankedlists/<ranked_list_id>


# Flask imports
from flask import Blueprint, request

# Pymongo query imports
from pymongo.collection import ReturnDocument

# Python datetime import for timestamps
from datetime import datetime

# Encoder imports
from fastapi.encoders import jsonable_encoder

# Rankor model imports
from rankor.models import Thing, RankedList, ThingScore

# Exception imports
from werkzeug.exceptions import Forbidden
from rankor.errors import (ResourceNotFoundInDatabaseError,
                               SameNameResourceAlreadyExistsError)

# Api settings import
import settings

# Database interface import
from rankor import db


# The blueprint with all the Thing endpoints
# This will be registered to the Flask app
ranked_list_endpoints = Blueprint('ranked_list_endpoints', __name__)


@ranked_list_endpoints.route("/rankor/rankedlists/", methods=["POST"])
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
    same_name_ranked_list = db.ranked_lists.find_one({
                                            "name": new_ranked_list_data["name"]
                                            })
    if same_name_ranked_list:
        raise SameNameResourceAlreadyExistsError(resource_type="ranked list",
                                       same_name_resource=same_name_ranked_list)

    # A RankedList has a dictionary that maps each thing to its score
    # in this RankedList, we are going to initialize the scores for all of them
    # with the default initialization scores defined in the api settings.
    # It also has a list of fights, which will be empty now, at the time
    # of creation. 
    things_in_ranked_list = [Thing(**doc) for doc in db.things.find()]
    initial_scores = [ThingScore(thing=thing.id) for thing in things_in_ranked_list]
    new_ranked_list_data["thing_scores"] = initial_scores
    new_ranked_list_data["fights"] = []

    # Create, validate, and insert the RankedList instance into the database,
    # retrieve the auto-assigned id to include in the success response
    new_ranked_list = RankedList(**new_ranked_list_data)
    insert_result = db.ranked_lists.insert_one(new_ranked_list.to_bson())
    new_ranked_list.id = insert_result.inserted_id

    # Success: respond with the new ranked list
    return new_ranked_list.to_json()



@ranked_list_endpoints.route("/rankor/rankedlists/<ObjectId:ranked_list_id>/", 
                             methods=["DELETE"])
def delete_a_ranked_list(ranked_list_id):
    """
    DELETE request to remove a RankedList from the database

    Example:
    curl -i -X DELETE 'http://localhost:5000/rankor/rankedlists/12345678901234567890ffff/'   
    """
    deleted_doc = db.ranked_lists.find_one_and_delete({"_id": ranked_list_id})
    if deleted_doc is None:
        raise ResourceNotFoundInDatabaseError(resource_type="ranked list",
                                              resource_id=ranked_list_id)
    # Success: Respond with the deleted document that's no longer in the database
    # (Don't instantiate it, as we don't need validation of a doc we just deleted)
    return jsonable_encoder(deleted_doc)


@ranked_list_endpoints.route("/rankor/rankedlists/<ObjectId:ranked_list_id>/", 
                             methods=["PUT"])
def edit_a_ranked_list(ranked_list_id):
    """
    PUT request to update the data of a RankedList that already exists in the database.

    By default, you can only edit the metadata of a RankedList, which is just its name.
    This means that you can only change their name using the edit endpoint. Fights can 
    be saved to or deleted from RankedLists via other endpoints (fight_endpoints.py),
    and this is normally the only way to influence the fights list and as a result 
    the thing_scores list in a RankedList. 
    If settings.ALLOW_MANUAL_EDITING_OF_RANKEDLIST_FIGHTS_OR_SCORES is set to True 
    instead of the default False, this endpoint will allow you to directly update these 
    lists.    
    Doing this is NOT recommended, as it's not a good way of handling the data, it's 
    prone to introducing silent errors that will come back to bite you later, and it's 
    easy to mess up unless you know exactly what you're doing.

    Example (name change from 'My Favorite Movies' to 'Action Movie Ranked List with Max'):
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
        raise ResourceNotFoundInDatabaseError(resource_type="ranked list",
                                              resource_id=ranked_list_id)
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
                                             {"$set": validated_update.to_bson()},
                                             return_document=ReturnDocument.AFTER
                                             )

    # If unsuccessful, abort with a 404 Not Found error
    if updated_doc is None:
        raise ResourceNotFoundInDatabaseError(resource_type="ranked list",
                                              resource_id=ranked_list_id)
    # Success: respond with the new, updated RankedList
    return RankedList(**updated_doc).to_json()





@ranked_list_endpoints.route("/rankor/rankedlists/<ObjectId:ranked_list_id>/", 
                       methods=["GET"])
def get_one_ranked_list(ranked_list_id): 
    """
    GET request to retrieve the data for a single RankedList using its id

    For example:
    curl -i -X GET 'http://localhost:5000/rankor/rankedlists/a4325678901234567890bcd5/'
    """
    # Retrieve the document with this id from the database and respond
    # with it, or raise an HTTP 404 if you can't find it
    doc = db.ranked_lists.find_one({"_id": ranked_list_id}, )
    if doc is None:
        raise ResourceNotFoundInDatabaseError(resource_type="ranked list",
                                              resource_id=ranked_list_id)
    # Success: respond with the ranked list 
    return RankedList(**doc).to_json()

