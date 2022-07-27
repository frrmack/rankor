# Standard Python library imports
from datetime import datetime
import os

# Database interface imports
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask_pymongo import PyMongo

# Flask imports
import flask
from flask import Flask, request, url_for, jsonify

# Rankor imports
from src.rankor.models import Thing
from src.rankor.pyobjectid import PyObjectId

# Settings for this specific server instance
import settings

# Configure Flask & Flask-PyMongo
app = Flask(__name__)
app.config["MONGO_URI"] = settings.MONGO_DATABASE_URI
pymongo = PyMongo(app)


# Error handlers to return errors as JSON (instead of Flask's default HTML)
@app.errorhandler(404)
def resource_not_found(e):
    """
    404
    """
    return jsonify(error=str(e)), 404


@app.errorhandler(DuplicateKeyError)
def resource_not_found(e):
    """
    MongoDB duplicate key errors
    """
    return jsonify(error=f"Duplicate key error"), 400



# Thing endpoints: List (GET), Add New (POST), Update (PUT), Delete (DELETE)
@app.route("/things/", methods=["GET"])
def list_all_things():
    """
    GET request to list all Things in the database.
    Since this list can get long, the results are paginated.
    You can ask for a specific page, like for example:
    curl -i -xGET 'http://localhost:5000/things/?page=3'
    The response will also include the following links:
    self: the link to get this very page
    last: the link to get the last page
    prev: the link to get the previous page
    next: the link to get the next page
    These links are there to help iterate over all results
    """

    # Define the parameters / counts to help paginate
    # Note: if no page parameter is given, we will default to page 1
    page = int(request.args.get("page", 1))
    page_size = settings.NUMBER_OF_ITEMS_IN_EACH_RESPONSE_PAGE 
    number_of_all_things = recipes.count_documents({})

    # We will sort all things alphabetically, then divide this list into pages
    # that only include page_size items. Page size is a constant setting defined
    # in settings.py in the root of the repository.
    #
    # For example, if the page size is 10 (each page has 10 things in it),
    # and we need to respond with page 6, we will first retrieve all things from 
    # the database, sort them by name, then skip the first 50 things (since they
    # were in the previous 5 pages), then use mongo's limit functionality to list 
    # the 10 things that start from there (the 51st through 60th things). 
    # This is page 6. We will also provide links to page 5, page 7, and the last page.
    page_items_query = recipes.find().sort("name").skip(page_size*(page-1)).limit(page_size)

    things_in_this_page = [Thing(**item).to_json() for item in page_items_query]

    # Add links to this very page and the last page you can get
    links = {
        "self": {"href": url_for(".list_all_things", page=page, _external=True)},
        "last": {"href": url_for(".list_all_things", 
                                 page=(number_of_all_things // page_size) + 1,
                                 _external=True
                                )
                },
    }
    # Add a 'prev' link if it's not on the first page:
    if page > 1:
        links["prev"] = {"href": url_for(".list_all_things", 
                                          page=page - 1, 
                                          _external=True
                                        )
                        }
    # Add a 'next' link if it's not on the last page:
    if page - 1 < number_of_all_things // page_size:
        links["next"] = {"href": url_for(".list_all_things", 
                                          page=page + 1,
                                          _external=True
                                        )
                        }

    # Return the full response
    return {"things in this page": things_in_this_page, 
            "_page": page,
            "_links": links,
           }
