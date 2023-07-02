"""
Rankor api is a Flask app to create ranked lists of things on the basis of
fights. Fights are pairwise comparisons of things within the specific context of
a ranked list.

All specific endpoints of the rankor api are listed below.
------------------------------------------------------------------------------

Thing endpoints: 
/rankor/things/

Create a new Thing    |   POST    /rankor/things/
Edit a Thing          |   PUT     /rankor/things/<thing_id>/
Delete a Thing        |   DELETE  /rankor/things/<thing_id>/
Delete ALL Things     |   DELETE  /rankor/things/delete-all/
List all Things       |   GET     /rankor/things/     
Get one Thing         |   GET     /rankor/things/<thing_id>/

------------------------------------------------------------------------------

RankedList endpoints: 
/rankor/ranked-lists/

Create a new RankedList   |   POST    /rankor/ranked-lists/
Edit a RankedList         |   PUT     /rankor/ranked-lists/<ranked_list_id>/
Delete a RankedList       |   DELETE  /rankor/ranked-lists/<ranked_list_id>/
Delete ALL RankedLists    |   DELETE  /rankor/ranked-lists/delete-all/
List all RankedLists      |   GET     /rankor/ranked-lists/
Get one RankedList        |   GET     /rankor/ranked-lists/<ranked_list_id>/

------------------------------------------------------------------------------

RankedThing endpoint for a given RankedList: 
/rankor/ranked-lists/<ranked_list_id>/ranked-things/

List RankedThings  |  GET /rankor/ranked-lists/<ranked_list_id>/ranked-things/

------------------------------------------------------------------------------

Fight endpoints for a given RankedList: 
/rankor/ranked-lists/<ranked_list_id>/fights/

Arrange a new Fight    | GET    /rankor/ranked-lists/<ranked_list_id>/fights/new/
Save a Fight result    | POST   /rankor/ranked-lists/<ranked_list_id>/fights/      
Delete a Fight         | DELETE /rankor/ranked-lists/<ranked_list_id>/fights/<fight_id>/
List recorded Fights   | GET    /rankor/ranked-lists/<ranked_list_id>/fights/
List Fights of a Thing | GET    /rankor/ranked-lists/<ranked_list_id>/fights/of-a-thing/<thing_id>/

------------------------------------------------------------------------------
"""

# Flask
from flask import Flask


# Settings for this specific server instance
import settings


# Configure Flask & Flask-PyMongo with an application factory
def create_app(mongo_uri=settings.MONGO_DATABASE_URI):
    
    app = Flask(__name__)


    # Initialize the database connection
    from rankor.database import RANKOR_PYMONGO_INTERFACE
    app.config["MONGO_URI"] = mongo_uri
    RANKOR_PYMONGO_INTERFACE.init_app(app)


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


    # Remove Werkzeug's strict slashes behavior to avoid "Redirecting..." 
    # responses - a more elegant solution is to overwrite Werkzeug's MapAdapter
    # and Map classes and providing this SlashInsistingMap class to Flask
    # as the app.url_map_class attribute, but this route proved problematic
    # as Werkzeug's codebase around this changed multiple times, and supporting
    # further versions of Flask and Werkzeug is better than doing this (speaking
    # from experience)
    app.url_map.strict_slashes = False


    # Import and register all endpoints
    from rankor.endpoints.things import thing_endpoints
    app.register_blueprint(thing_endpoints)

    from rankor.endpoints.ranked_lists import ranked_list_endpoints
    app.register_blueprint(ranked_list_endpoints)

    from rankor.endpoints.ranked_things import ranked_thing_endpoints
    app.register_blueprint(ranked_thing_endpoints)

    from rankor.endpoints.fights import fight_endpoints
    app.register_blueprint(fight_endpoints)

    # The app is now ready for use
    return app

