# Flask imports
from flask import Blueprint, request

# Pymongo query imports
from pymongo.collection import ReturnDocument

# Python datetime import for timestamps
from datetime import datetime

# Rankor model imports
from src.rankor.models import Thing, RankedList, Score

# Exception imports
from src.rankor.errors import ResourceNotFoundInDatabaseError

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

    # A RankedList has a dictionary that maps each thing to its score
    # in this RankedList, we are going to initialize the scores for all of them
    # with the default initialization scores defined in the api settings.
    # It also has a list of fights, which will be empty now, at the time
    # of creation. 
    things_in_ranked_list = [Thing(**doc) for doc in db.things.find()]
    initial_scores = [Score(thing_id=thing.id) for thing in things_in_ranked_list]
    new_ranked_list_data["thing_scores"] = initial_scores
    new_ranked_list_data["fights"] = []

    # Create the RankedList instance, which also validates its data using pydantic,
    # insert it into the database, and retrieve the _id that mongodb automatically 
    # assigned it. When returning it as a success reponse, put the newly assigned id 
    # in as well.
    new_ranked_list = RankedList(**new_ranked_list_data)
    insert_result = db.ranked_lists.insert_one(new_ranked_list.to_bson())
    new_ranked_list.id = insert_result.inserted_id

    # Success: respond with the new ranked list
    return new_ranked_list.to_json()

