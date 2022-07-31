# Error imports
from werkzeug.exceptions import HTTPException
from pymongo.errors import DuplicateKeyError

# Import the Flask app to register error handlers
from src.rankor import app

# Custom Errors and error handlers to return 
class ResourceNotFoundInDatabaseError(HTTPException):
    code = 404
    description = ("The requested resource was not found in the database. "
                   "Please check the requested id carefully and try again.")


# Return error responses as JSON (instead of Flask's default HTML)
@app.errorhandler(Exception)
def handle_error(error):
    code = 500
    if isinstance(error, HTTPException):
        code = error.code
    elif isinstance(error, DuplicateKeyError):
        code = 400
    return jsonify({"error": error.description}), code