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



# Configure Flask & Flask-PyMongo
app = Flask(__name__)
app.config["MONGO_URI"] = settings.MONGO_DATABASE_URI
pymongo = PyMongo(app)
db = pymongo.db


# Import and register error handlers
from rankor.errors import json_error_response
app.register_error_handler(Exception, json_error_response)


# Import and register all endpoints

# # Thing endpoints: /rankor/things/
# #
# # Add a new Thing       |   POST    /rankor/things/
# # Delete a Thing        |   DELETE  /rankor/things/<thing_id>
# # Edit/Update a Thing   |   PUT     /rankor/things/<thing_id>
# # List all Things       |   GET     /rankor/things/     
# # Show one Thing        |   GET     /rankor/things/<thing_id>
from src.rankor.thing_endpoints import thing_endpoints
app.register_blueprint(thing_endpoints)


# RankedList endpoints: /rankor/rankedlists/
#
# Create a new RankedList   |   POST    /rankor/rankedlists/
# Delete a RankedList       |   DELETE  /rankor/rankedlists/<ranked_list_id>
# Edit/Update a RankedList  |   PUT     /rankor/rankedlists/<ranked_list_id>
# List all RankedLists      |   GET     /rankor/rankedlists/
# Get a RankedList          |   GET     /rankor/rankedlists/<ranked_list_id>
from src.rankor.ranked_list_endpoints import ranked_list_endpoints
app.register_blueprint(ranked_list_endpoints)



# Fight endpoints for a given RankedList: /rankor/rankedlists/<ranked_list_id>/fights/
#
# Get a new Fight between two Things in a RankedList  
# GET     /rankor/rankedlists/<ranked_list_id>/fights/new/
#
# Save the result of a Fight            
# POST    /rankor/rankedlists/<ranked_list_id>/fights/
#
# Delete a Fight in a RankedList        
# DELETE  /rankor/rankedlists/<ranked_list_id>/fights/<fight_id>
#
# Show all recorded Fights in a RankedList  
# GET     /rankor/rankedlists/<ranked_list_id>/fights/
#
# Retrieve all Fights of a Thing in a RankedList 
# GET     /rankor/rankedlists/<ranked_list_id>/fights/things/<thing_id>


