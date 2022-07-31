# Standard Python library imports
from datetime import datetime

# Database interface imports
from flask_pymongo import PyMongo

# Flask imports
from flask import Flask, request, url_for, jsonify

# Rankor imports
from src.rankor.models import Thing, RankedList, Fight, Score
from src.rankor.pyobjectid import PyObjectId

# Settings for this specific server instance
import settings

# Endpoint routing imports
from src.rankor.thing_endpoints import thing_endpoints



# Configure Flask & Flask-PyMongo
app = Flask(__name__)
app.config["MONGO_URI"] = settings.MONGO_DATABASE_URI
pymongo = PyMongo(app)
db = pymongo.db


# Register all endpoints

# # Thing endpoints: /rankor/things/
# #
# # Add a new Thing       |   POST    /rankor/things/
# # Delete a Thing        |   DELETE  /rankor/things/<thing_id>
# # Edit/Update a Thing   |   PUT     /rankor/things/<thing_id>
# # List all Things       |   GET     /rankor/things/     
# # Show one Thing        |   GET     /rankor/things/<thing_id>
app.register_blueprint(thing_endpoints)




# RankedList endpoints: /rankor/rankedlists/
#
# Create a new RankedList               
#                       |   POST    /rankor/rankedlists/
#
# Delete a RankedList                   
#                       |   DELETE  /rankor/rankedlists/<ranked_list_id>
#
# Edit/Update a RankedList              
#                       |   PUT     /rankor/rankedlists/<ranked_list_id>
#
# List all RankedLists                  
#                       |   GET     /rankor/rankedlists/
#
# Show a RankedList with its ranked Things and their scores  
#                       |   GET     /rankor/rankedlists/<ranked_list_id>


@app.route("/rankor/rankedlists/", methods=["POST"])
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
    new_ranked_list_data["thing_scores"] = {thing.id: Score() for thing in things_in_ranked_list}
    new_ranked_list_data["fights"] = []  

    # Create the RankedList instance, which also validates its data using pydantic,
    # insert it into the database, and retrieve the _id that mongodb automatically 
    # assigned it (for purposes of returning its id in the response)
    ranked_list = RankedList(**new_ranked_list_data)
    insert_result = db.ranked_lists.insert_one(ranked_list.to_bson())
    
    # When logging and returning it as a success reponse, put the newly assigned id
    # in, but leave the thing_scores dict out to avoid too long of a response here, 
    # as that dictionary includes all the Things participating in the RankedList
    ranked_list.id = PyObjectId(str(insert_result.inserted_id))
    ranked_list.thing_scores = {}

    # log and respond
    print(ranked_list)
    return ranked_list.to_json()



# Fight endpoints for a given RankedList: /rankor/rankedlists/<ranked_list_id>/fights/
#
# Get a new Fight between two Things in a RankedList  
#                       |   GET     /rankor/rankedlists/<ranked_list_id>/fights/new/
#
# Save the result of a Fight            
#                       |   POST    /rankor/rankedlists/<ranked_list_id>/fights/
#
# Delete a Fight in a RankedList        
#                       |   DELETE  /rankor/rankedlists/<ranked_list_id>/fights/<fight_id>
#
# Show all recorded Fights in a RankedList  
#                       |   GET     /rankor/rankedlists/<ranked_list_id>/fights/
#
# Retrieve all Fights of a Thing in a RankedList 
#                       |   GET     /rankor/rankedlists/<ranked_list_id>/fights/things/<thing_id>


