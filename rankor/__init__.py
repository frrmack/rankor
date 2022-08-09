# Flask
from flask import Flask

# Database interface
from flask_pymongo import PyMongo

# Settings for this specific server instance
import settings


# Configure Flask & Flask-PyMongo
app = Flask(__name__)
app.config["MONGO_URI"] = settings.MONGO_DATABASE_URI
pymongo = PyMongo(app)
db = pymongo.db


# Import and register error handlers
from rankor.error_handlers import (http_error_response,
                                   data_validation_error_response,
                                   database_error_response,
                                   bson_format_error_response)

from werkzeug.exceptions import HTTPException
app.register_error_handler(HTTPException, http_error_response)

from pydantic import ValidationError
app.register_error_handler(ValidationError, data_validation_error_response)

from pymongo.errors import PyMongoError
app.register_error_handler(PyMongoError, database_error_response)

from bson.errors import BSONError
app.register_error_handler(BSONError, bson_format_error_response)


# Import and register routing rules
from rankor.routing_rules import SlashInsistingRoutingRule
app.url_rule_class = SlashInsistingRoutingRule


# Import and register all endpoints
from rankor.thing_endpoints import thing_endpoints
app.register_blueprint(thing_endpoints)

from rankor.ranked_list_endpoints import ranked_list_endpoints
app.register_blueprint(ranked_list_endpoints)

#------------------------------------------------------------------------------
# Thing endpoints: /rankor/things/
#
# Create a new Thing    |   POST    /rankor/things/
# Edit a Thing          |   PUT     /rankor/things/<thing_id>/
# Delete a Thing        |   DELETE  /rankor/things/<thing_id>/
# Delete ALL Things     |   DELETE  /rankor/things/delete-all/
# List all Things       |   GET     /rankor/things/     
# Get one Thing         |   GET     /rankor/things/<thing_id>/
#------------------------------------------------------------------------------
# RankedList endpoints: /rankor/rankedlists/
#
# Create a new RankedList   |   POST    /rankor/rankedlists/
# Edit a RankedList         |   PUT     /rankor/rankedlists/<ranked_list_id>/
# Delete a RankedList       |   DELETE  /rankor/rankedlists/<ranked_list_id>/
# Delete ALL RankedLists    |   DELETE  /rankor/rankedlists/delete-all/
# List all RankedLists      |   GET     /rankor/rankedlists/
# Get one RankedList        |   GET     /rankor/rankedlists/<ranked_list_id>/
#------------------------------------------------------------------------------
# Ranks endpoint for a given RankedList: /rankor/rankedlists/<ranked_list_id>/ranks/
#
# Get the list of the ranked Things and their Scores in a RankedList 
# GET     /rankor/rankedlists/<ranked_list_id>/ranks/
#------------------------------------------------------------------------------
# Fight endpoints for a given RankedList: /rankor/rankedlists/<ranked_list_id>/fights/
#
# Get a new Fight between two Things in a RankedList (fight matchmaking)
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
#------------------------------------------------------------------------------
