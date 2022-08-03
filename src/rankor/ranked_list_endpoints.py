# RankedList endpoints: /rankor/rankedlists/
#
# Create a new RankedList   |   POST    /rankor/rankedlists/
# Delete a RankedList       |   DELETE  /rankor/rankedlists/<ranked_list_id>
# Edit/Update a RankedList  |   PUT     /rankor/rankedlists/<ranked_list_id>
# List all RankedLists      |   GET     /rankor/rankedlists/
# Get a RankedList          |   GET     /rankor/rankedlists/<ranked_list_id>


# Flask imports
from flask import Blueprint, request

# Pymongo query imports
from pymongo.collection import ReturnDocument

# Python datetime import for timestamps
from datetime import datetime

# Rankor model imports
from src.rankor.models import Thing, RankedList, ThingScore

# Exception imports
from src.rankor.errors import (ResourceNotFoundInDatabaseError,
                               SameNameResourceAlreadyExistsError)

# Api settings import
import settings

# Database interface import
from src.rankor import db


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
    curl -d '{"name": "Favorite Movies"}' 
         -H "Content-Type: application/json" 
         -X POST http://localhost:5000/rankor/rankedlists/
    """
    # Retrieve the data from the request and record the timestamp
    new_ranked_list_data = request.get_json()
    new_ranked_list_data["date_created"] = datetime.utcnow()

    # Check the database to ensure that there isn't another one with the exact 
    # same name, raise an error if it does
    same_name_ranked_list = db.ranked_lists.find_one({
                                            "name": new_ranked_list_data["name"]
                                            })
    if same_name_ranked_list:
        raise SameNameResourceAlreadyExistsError(same_name_ranked_list)

    # A RankedList has a dictionary that maps each thing to its score
    # in this RankedList, we are going to initialize the scores for all of them
    # with the default initialization scores defined in the api settings.
    # It also has a list of fights, which will be empty now, at the time
    # of creation. 
    things_in_ranked_list = [Thing(**doc) for doc in db.things.find()]
    initial_scores = [ThingScore(thing_id=thing.id) for thing in things_in_ranked_list]
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
def delete_ranked_list(ranked_list_id):
    """
    DELETE request to remove a RankedList from the database

    Example:
    curl -i -X DELETE 'http://localhost:5000/rankor/rankedlists/12345678901234567890ffff/'   
    """
    deleted_doc = db.ranked_lists.find_one_and_delete({"_id": ranked_list_id})
    if deleted_doc is None:
        raise ResourceNotFoundInDatabaseError(f"Ranked list with the id {ranked_list_id} "
                                               "not found in the database.")
    # Success: Respond with the deleted document that's no longer in the database
    return RankedList(**deleted_doc).to_json()











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
        raise ResourceNotFoundInDatabaseError(f"Ranked list with the id {ranked_list_id} "
                                               "not found in the database.")
    # Success: respond with the ranked list 
    return RankedList(**doc).to_json()

