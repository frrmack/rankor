# Rankor Exceptions and Flask error handlers

# Flask imports
from flask import jsonify

# Error imports
from werkzeug.exceptions import HTTPException
from pymongo.errors import DuplicateKeyError


# Custom Exceptions --------
class ResourceNotFoundInDatabaseError(HTTPException):
    code = 404
    description = ("The requested resource was not found in the database. "
                   "Please check the requested id carefully and try again.")



# Error Handlers --------

# General catch all error handler to return error responses 
# as JSON (instead of Flask's default HTML)
def json_error_response(error):
    code = 500
    if isinstance(error, HTTPException):
        code = error.code
    elif isinstance(error, DuplicateKeyError):
        code = 400
    return jsonify({"error_type": type(error).__name__, "error": error.description}), code