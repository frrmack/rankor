"""
Thing endpoints: /rankor/things/

Create a new Thing    |   POST    /rankor/things/
Edit a Thing          |   PUT     /rankor/things/<thing_id>/
Delete a Thing        |   DELETE  /rankor/things/<thing_id>/
Delete ALL Things     |   DELETE  /rankor/things/delete-all/
List all Things       |   GET     /rankor/things/     
Get one Thing         |   GET     /rankor/things/<thing_id>/
"""

# Python inspection imports 
# (to get the name of an endpoint from within)
from sys import _getframe

# Flask imports
from flask import Blueprint, request, url_for

# Pymongo query imports
from pymongo.collection import ReturnDocument

# Python datetime import for timestamps
from datetime import datetime

# Encoder imports
from rankor.json import to_json

# Rankor model imports
from rankor.models import Thing

# Pagination imports
from rankor.pagination import QueryPaginator

# Exception imports
from rankor.errors import (ResourceNotFoundInDatabaseError,
                           SameNameResourceAlreadyExistsError)

# Database interface import
from rankor import db


# The blueprint with all the Thing endpoints
# This will be registered to the Flask app
thing_endpoints = Blueprint('thing_endpoints', __name__)



# Create a new Thing    |   POST   /rankor/things/
@thing_endpoints.route(
    "/rankor/things/", 
    methods=["POST"]
)
def create_a_new_thing():
    """
    POST request to directly add a new Thing to the database.

    Fields you can define for a new Thing are:
    name: str
    image_url: Optional[AnyUrl]
    category: Optional[str]     
    other_data: Optional[Json]

    Attach the contents of the new Thing as data in JSON format.
    Example:
    curl -d '{"name": "Terminator", 
              "image_url": "https://m.media-amazon.com/images/I/61qCgQZyhOL._AC_SY879_.jpg", 
              "other_data": {"director": "James Cameron", "year": 1982}
             }' 
         -H "Content-Type: application/json" 
         -X POST http://localhost:5000/rankor/things/
    """
    # Retrieve the data from the request and record the timestamp of creation
    new_thing_data = request.get_json()
    new_thing_data["time_created"] = datetime.utcnow()

    # Check the database to ensure that there isn't another Thing with the exact 
    # same name, raise an error if it does
    if "name" in new_thing_data:
        same_name_thing = db.things.find_one({"name": new_thing_data["name"]})
        if same_name_thing:
            raise SameNameResourceAlreadyExistsError(
                resource_type="thing",
                same_name_resource=same_name_thing
            )

    # Create the new Thing instance, which also validates its data using pydantic,
    # insert it into the database, and retrieve the _id that mongodb automatically 
    # assigned it. When returning it as a success reponse, put the newly assigned id 
    # in as well.
    new_thing = Thing(**new_thing_data)
    insert_result = db.things.insert_one(new_thing.to_bsonable_dict())
    new_thing.id = insert_result.inserted_id

    # Success: respond in json with the added thing
    return to_json(
        {
            "result": "success",
            "msg": f"New thing created and given id {new_thing.id}",
            "thing": new_thing,
            "http_status_code": 200
        },
    ), 200



# Edit a Thing    |   PUT   /rankor/things/<thing_id>/
@thing_endpoints.route(
    "/rankor/things/<ObjectId:thing_id>/", 
    methods=["PUT"]
)
def edit_a_thing(thing_id):
    """
    PUT request to update the data of a Thing that already exists in the database.

    You can make partial updates like adding an optional field (like category in this
    example below) or change the value of a single field, change the values of multiple
    fields, etc. You can also fully replace the entire data of the Thing.

    Example (change the name from 'Terminator' to 'The Terminator' and add a category field):
    curl -d '{"name": "The Terminator", 
              "category": "Action Movies",
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
    # We want to validate this by creating a Thing instance with
    # it (which runs the pydantic schema checks). A Thing instance
    # always needs a name field, so we need to define the name field
    # when creating a new Thing instance. Unless they are also updating
    # the name field, thing_update_data does not have a name field. So,
    # before we validate the update data with Thing(**thing_update_data),
    # we need to retrieve the name of this thing from the database.
    if 'name' not in update_data:
        thing_doc_we_are_updating = db.things.find_one({"_id": thing_id})
        if thing_doc_we_are_updating is None:
            raise ResourceNotFoundInDatabaseError(
                resource_type="thing",
                resource_id=thing_id
            )
        update_data['name'] = thing_doc_we_are_updating['name']
    # Now we know for sure that our thing_update_data has a name.
    # Validate through instantiating it as a Thing and add a timestamp
    # to store when this update happened.
    validated_update = Thing(**update_data)
    validated_update.time_edited = datetime.utcnow()
    print(f'validated update: {validated_update.to_json()}')
    # Get our target thing with this id and apply these updates to the 
    # given fields in the database.
    updated_doc = db.things.find_one_and_update(
        {"_id": thing_id},
        {"$set": validated_update.to_bsonable_dict()},
        return_document=ReturnDocument.AFTER,
    )
    print(updated_doc)
    # If unsuccessful, abort and send an HTTP 404 error
    if updated_doc is None:
        raise ResourceNotFoundInDatabaseError(
            resource_type="thing",
            resource_id=thing_id
        )
    # Success: respond with the new, updated Thing
    return to_json(
        {
            "result": "success",
            "msg": f"Successfully edited thing with id {thing_id}",
            "thing": Thing(**updated_doc).to_json(),
            "http_status_code": 200
        },
    ), 200



# Delete a Thing    |   DELETE  /rankor/things/<thing_id>/
@thing_endpoints.route(
    "/rankor/things/<ObjectId:thing_id>/", 
    methods=["DELETE"]
)
def delete_a_thing(thing_id):
    """
    DELETE request to remove a Thing from the database

    Example:
    curl -i -X DELETE 'http://localhost:5000/rankor/things/12345678901234567890abcd/'   
    """
    # Kill the Thing document with this id in the database
    deleted_thing_doc = db.things.find_one_and_delete({"_id": thing_id})
    # If unsuccessful, abort and send an HTTP 404 error
    if deleted_thing_doc is None:
        raise ResourceNotFoundInDatabaseError(
            resource_type="thing",
            resource_id=thing_id
        )

    # Success: Respond with the deleted Thing document that's 
    # no longer in the database 
    return to_json(
        {
            "result": "success",
            "msg": f"thing with id {thing_id} deleted.",
            "thing": deleted_thing_doc,
            "http_status_code": 200
        },
    ), 200
    
    

# Delete ALL Things   |   DELETE  /rankor/things/delete-all/
@thing_endpoints.route(
    "/rankor/things/delete-all/", 
    methods=["DELETE"]
)
def delete_ALL_things():
    """
    DELETE request to delete ALL existing Things
    This purges the entire things collection in the database
    It's basically an endpoint to reset back to factory settings

    Example:
    curl -i -X DELETE 'http://localhost:5000/rankor/things/delete-all/'   
    """
    # Delete all documents in the database's things collection
    deletion_info = db.things.delete_many({})
    # Success: Respond with a message on the number of deleted documents
    return to_json(
        {
            "result": "success",
            "msg": f"{deletion_info.deleted_count} things deleted",
            "http_status_code": 200
        },
    ), 200



# List all Things    |   GET   /rankor/things/     
@thing_endpoints.route(
    "/rankor/things/", 
    methods=["GET"]
)
def list_all_things():
    """
    GET request to list all Things in the database.

    Since this list can get long, the results are paginated.
    Each page will list a set number of Things, this page size is determined
    in the api settings (in the root directory).

    You can ask for a specific page, for example:
    curl -i -X GET 'http://localhost:5000/rankor/things/?page=3'

    If you don't give a page parameter, it will return page 1. The response will
    also include the page number and the links to the following endpoint uris:
    - this_page
    - next_page     (if there is one)
    - previous_page (if there is one)
    - last_page
    These links are there to help iterate over all results.
    """
    # Read the page parameter
    requested_page = request.args.get("page", 1)
    # Python frame inspection code to get the name of this very function
    endpoint_name = "." + _getframe().f_code.co_name
    # Count the total number of documents in the database for this list
    num_all_docs_in_db = db.things.count_documents({})
    # Get the paginator for our case (list of all Things in db.things)
    # and use it to respond with the requested page
    paginator = QueryPaginator(
        endpoint_name = endpoint_name, 
        model = Thing,
        query = db.things.find(),
        num_all_docs_in_db = num_all_docs_in_db
    )
    return paginator.paginate(requested_page=requested_page)



# Get one Thing    |   GET   /rankor/things/<thing_id>/
@thing_endpoints.route(
    "/rankor/things/<ObjectId:thing_id>/", 
    methods=["GET"]
)
def get_one_thing(thing_id): 
    """
    GET request to retrieve the data for a single Thing using its id

    For example:
    curl -i -X GET 'http://localhost:5000/rankor/things/12345678901234567890abcd/'
    """
    # Retrieve the Thing document with this id from the database and respond
    # with it. If the database can't find such a document in there, respond
    # with an informative HTTP 404
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
    thing_doc = db.things.find_one({"_id": thing_id})
    # If failure: 404 Not Found Error
    if thing_doc is None:
        raise ResourceNotFoundInDatabaseError(
            resource_type="thing",
            resource_id=thing_id
        )
    # Success: respond with the thing 
    return to_json(
        {
            "result": "success",
            "msg": f"Successfully retrieved thing with id {thing_id}",
            "thing": Thing(**thing_doc),
            "http_status_code": 200
        }
    ), 200
