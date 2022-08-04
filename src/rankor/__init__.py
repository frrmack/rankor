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
from src.rankor.error_handlers import (http_error_response,
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
from src.rankor.routing_rules import SlashInsistingRoutingRule
app.url_rule_class = SlashInsistingRoutingRule


# Import and register all endpoints
from src.rankor.thing_endpoints import thing_endpoints
app.register_blueprint(thing_endpoints)

from src.rankor.ranked_list_endpoints import ranked_list_endpoints
app.register_blueprint(ranked_list_endpoints)

#------------------------------------------------------------------------------
# Thing endpoints: /rankor/things/
#
# Add a new Thing       |   POST    /rankor/things/
# Delete a Thing        |   DELETE  /rankor/things/<thing_id>
# Edit/Update a Thing   |   PUT     /rankor/things/<thing_id>
# List all Things       |   GET     /rankor/things/     
# Show one Thing        |   GET     /rankor/things/<thing_id>
#------------------------------------------------------------------------------
# RankedList endpoints: /rankor/rankedlists/
#
# Create a new RankedList   |   POST    /rankor/rankedlists/
# Delete a RankedList       |   DELETE  /rankor/rankedlists/<ranked_list_id>
# Edit/Update a RankedList  |   PUT     /rankor/rankedlists/<ranked_list_id>
# List all RankedLists      |   GET     /rankor/rankedlists/
# Get a RankedList          |   GET     /rankor/rankedlists/<ranked_list_id>
#------------------------------------------------------------------------------
# Score endpoint for a given RankedList: /rankor/rankedlists/<ranked_list_id>/scores/
#
# Get the scores of the ranked Things in a RankedList 
# GET     /rankor/rankedlists/<ranked_list_id>/scores/
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
