# Standard Python library imports
from datetime import datetime
import os

# Serialization imports (fastapi's nice json encoder)
from fastapi.encoders import jsonable_encoder

# Database interface imports
from pymongo.collection import ReturnDocument
from pymongo.errors import DuplicateKeyError
from flask_pymongo import PyMongo

# Flask imports
import flask
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

# Error handlers to return errors as JSON (instead of Flask's default HTML)
@app.errorhandler(404)
def resource_not_found(e):
    """
    HTTP 404 Resource not found error
    """
    return jsonify(error=str(e)), 404


@app.errorhandler(DuplicateKeyError)
def resource_not_found(e):
    """
    HTTP 400 MongoDB duplicate key errors
    """
    return jsonify(error=f"Duplicate key error"), 400



# Thing endpoints: /rankor/things/
#
# Add a new Thing       |   POST    /rankor/things/
# Delete a Thing        |   DELETE  /rankor/things/<thing_id>
# Edit/Update a Thing   |   PUT     /rankor/things/<thing_id>
# List all Things       |   GET     /rankor/things/     
# Show one Thing        |   GET     /rankor/things/<thing_id>

@app.route("/rankor/things/", methods=["POST"])
def add_new_thing():
    """
    POST request to directly add a new Thing to the database.

    Fields you can define for a new Thing are:
    name: str
    image_url: Optional[AnyUrl]
    category: Optional[str]     
    extra_data: Optional[Json]

    Attach the contents of the new Thing as data in JSON format.
    Example:
    curl -d '{'name': 'Terminator', 
              'image_url': https://m.media-amazon.com/images/I/61qCgQZyhOL._AC_SY879_.jpg', 
              'extra_data': {'director': 'James Cameron', 'year': 1982}
             }' 
         -H "Content-Type: application/json" 
         -X POST http://localhost:5000/rankor/things/
    """
    # Retrieve the data from the request and record the timestamp of creation
    new_thing_data = request.get_json()
    new_thing_data["date_created"] = datetime.utcnow()

    # Create the new Thing instance, which also validates its data using pydantic,
    # insert it into the database, and retrieve the _id that mongodb automatically 
    # assigned it (for purposes of returning the full thing, including its id, 
    # in the response)
    new_thing = Thing(**new_thing_data)
    insert_result = db.things.insert_one(new_thing.to_bson())
    new_thing.id = PyObjectId(str(insert_result.inserted_id))
    
    # log the added thing and return it (in json) as the success response
    print(new_thing)
    return new_thing.to_json()


@app.route("/rankor/things/<thing_id>/", methods=["DELETE"])
def delete_thing(thing_id):
    """
    DELETE request to remove a thing from the database

    Example:
    curl -i -X DELETE 'http://localhost:5000/rankor/things/12345678901234567890abcd/'   
    """
    # Kill the Thing document with this id in the database
    deleted_thing_doc = db.things.find_one_and_delete({"_id": PyObjectId(thing_id)})
    # If successful, respond with the deleted Thing document that's 
    # no longer in the database
    # If unsuccessful, abort and send an HTTP 404 error
    if deleted_thing_doc:
        return Thing(**deleted_thing_doc).to_json()
    else:
        flask.abort(404, f"Thing with id {thing_id} not found")


@app.route("/rankor/things/<thing_id>", methods=["PUT"])
def update_thing_data(thing_id):
    """
    PUT request to update the data of a Thing that already exists in the database.

    You can make partial updates like adding an optional field (like category in this
    example below) or change the value of a single field, change the values of multiple
    fields, etc. You can of course fully replace the entire data of the Thing.

    Example (change the name from 'Terminator' to 'The Terminator' and add a category field):
    curl -d '{'name': 'The Terminator', 
              'category: 'Action Movies',
             }' 
         -H "Content-Type: application/json" 
         -X PUT http://localhost:5000/rankor/things/12345678901234567890abcd       

    If you would like to use the safest approach to avoid any unforeseen inconsistencies
    due to user error when using this endpoint with partial field updates, the most robust
    way is always to retrieve the Thing first with a GET request to /rankor/things/<thing_id>,
    update its data and send this updated version with a PUT request to store these updates
    in the database.
    """
    # Retrieve the request data. 
    update_data = request.get_json()
    # We want to validate it this creating a Thing instance with
    # it (which runs the pydantic schema checks). A Thing instance
    # always needs a name field, so we need to define the name field
    # when creating a new Thing instance. Unless they are also updating
    # the name field, thing_update_data does not have a name field. So,
    # before we validate the update data with Thing(**thing_update_data),
    # we need to retrieve the name of this thing from the database.
    if 'name' not in update_data:
        thing_doc_we_are_updating = db.things.find_one({"_id": PyObjectId(thing_id)})
        print(thing_doc_we_are_updating)
        if not thing_doc_we_are_updating:
            flask.abort(404, f"Thing with id {thing_id} not found")
        thing_doc_we_are_updating['name'] = thing_doc_we_are_updating['name']
    # Now we know for sure that our thing_update_data has a name.
    # Validate through instantiating it as a Thing and add a timestamp
    # to store when this update happened.
    validated_update = Thing(**update_data)
    validated_update.date_updated = datetime.utcnow()
    print(f'validated update: {validated_update.to_json()}')
    # Get our target thing with this id and apply these updates to the 
    # given fields in the database.
    updated_doc = db.things.find_one_and_update({"_id": PyObjectId(thing_id)},
                                                 {"$set": validated_update.to_bson()},
                                                 return_document=ReturnDocument.AFTER,
                                                )
    print(updated_doc)
    # If successful, respond with the new, updated Thing
    # If unsuccessful, abort and send an HTTP 404 error
    if updated_doc:
        return Thing(**updated_doc).to_json()
    else:
        flask.abort(404, f"Thing with id {thing_id} not found")


@app.route("/rankor/things/", methods=["GET"])
def list_all_things():
    """
    GET request to list all Things in the database.

    Since this list can get long, the results are paginated.
    Each page will list a set number of Things, this page size is determined
    in the api settings (in the root directory).

    You can ask for a specific page, for example:
    curl -i -X GET 'http://localhost:5000/rankor/things/?page=3'

    If you don't give a page parameter, it will return page 1.
    The response will also include the page number and the following links:
    self: the link to get this very page
    last: the link to get the last page
    prev: the link to get the previous page
    next: the link to get the next page
    These links are there to help iterate over all results.
    """
    # Define the parameters / counts to help paginate
    # Note: if no page parameter is given, we will default to page 1
    page = int(request.args.get("page", 1))
    page_size = settings.NUMBER_OF_ITEMS_IN_EACH_RESPONSE_PAGE 
    num_skip = number_of_thing_docs_to_skip_to_reach_this_page = page_size * (page-1)
    number_of_all_things = db.things.count_documents({})
    last_page = (number_of_all_things // page_size) + 1

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
    page_docs_query = db.things.find().sort("name").skip(num_skip).limit(page_size)
    things_in_this_page = [Thing(**doc).to_json() for doc in page_docs_query]

    # Links to this very page and the last page you can get
    links = {
        "self": {"href": url_for(".list_all_things", page=page, _external=True)},
        "last": {"href": url_for(".list_all_things", page=last_page, _external = True)},
    }
    # Add a 'prev' link if it's not on the first page:
    if page > 1:
        links["prev"] = {"href": url_for(".list_all_things", page=page-1, _external=True)}
    # Add a 'next' link if it's not on the last page:
    if page - 1 < number_of_all_things // page_size:
        links["next"] = {"href": url_for(".list_all_things", page=page+1, _external=True)}

    # Return the full response
    return {
            "things": things_in_this_page, 
            "_page": page,
            "_links": links,
           }


@app.route("/rankor/things/<thing_id>/", methods=["GET"])
def get_one_thing(thing_id): 
    """
    GET request to retrieve the data for a single Thing using its id

    For example:
    curl -i -X GET 'http://localhost:5000/rankor/things/12345678901234567890abcd/'
    """
    # Retrieve the Thing document with this id from the database and respond
    # with it. If the database can't find such a document in there, find_one_or_404
    # will respond nicely with an HTTP 404.
    #
    # Why are we not just returning thing_doc directly instead of creating
    # a Thing instance with it, which we then re-serialize to JSON? Because
    # 1) The Thing doc in the database is stored as a bson. When pymongo
    # retrieves it for us, it converts that into a native python dict. What we
    # want to return is a json. We want to use the to_json encoder of the Thing
    # class, which serializes certain things always in the same way for all Thing
    # instances (for example, it encodes _id fields with as a string representing
    # the 24 character hex value of the bson object id assigned by mongodb, and it 
    # encodes all datetime stamps using ISO8601 strings)
    # 2) Creating this instance runs all the pydantic typing validation code,
    # ensuring much more robust, well defined, reliable api behavior. We want
    # to create Thing instances whenever data goes into or out of the database
    # to ensure robustness through data validation. If there is something wrong
    # with the data formats anywhere, the system will fail at these validation
    # checkpoints rather than somewhere random in the middle of the code when
    # the data is actually used.
    thing_doc = db.things.find_one_or_404({"_id": PyObjectId(thing_id)})
    return Thing(**thing_doc).to_json()



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
    curl -d '{'name': 'Favorite Movies'}' 
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


