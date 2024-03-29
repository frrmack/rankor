"""
Error handlers to return valid and useful responses in case of errors. 

These are critical to provide JSON responses instead of Flask's default HTML
responses. They also try to provide enough information for maximum context.
"""

# specific errors to handle differently
from rankor.errors import SameNameResourceAlreadyExistsError

# JSON encoding of error responses
from rankor.json import to_json


def http_error_response(http_exception):
    """
    HTTP exceptions raised by Werkzeug or Flask (or directly Rankor itself):
    werkzeug.exceptions.HTTPException

    Errors with an existing specific HTTP status code, either denoting a client 
    side issue, such as 400 Bad request, 403 Forbidden, 404 Not Found, 405 Method
    Not Allowed, etc. or a server side issue, such as 500 Internal Server Error,
    504 Gateway Timeout, etc.
    """
    http_status_code = http_exception.code
    response_dict = {
        "result": "failure",
        "error_category": "HTTP error",
        "error_type": type(http_exception).__name__,  
        "error": http_exception.description,
        "http_status_code": http_status_code
    }
    if isinstance(http_exception, SameNameResourceAlreadyExistsError):
        response_dict.update(
            {"existing_resource": http_exception.same_name_resource}
        )
    return to_json(response_dict), http_status_code


def data_validation_error_response(validation_error):
    """
    Validation exceptions raised by Pydantic:
    pydantic.error_wrappers.ValidationError

    Data validation errors encountered when the input data does not correctly
    fulfill the type requirements defined by the api. For example, when a 
    string value is provided for a field that's supposed to be a float.
    """
    http_status_code = 400      # Bad Request
    err_msg = ("The data of this resource does not fully match the validation "
               "requirements. Please ensure existence of all required fields, "
               "valid field names, and valid data types for those fields' "
               "values.")    
    num_validation_issues = len(validation_error.errors())
    details = {
        "number_of_validation_errors": num_validation_issues,
        "validation_error_list": validation_error.errors()
    }
    return to_json(
        {
            "result": "failure",
            "error_category": "Data validation error",            
            "error_type": type(validation_error).__name__, 
            "error": err_msg,
            "error_details": details,
            "http_status_code": http_status_code
        }
    ), http_status_code


def database_error_response(pymongo_error):
    """
    Database exceptions raised by Pymongo:
    pymongo.errors.PyMongoError

    Errors encountered when an interaction with the database is gone wrong. 
    For example, a DuplicateKeyError, a DocumentTooLargeError, or an 
    ExecutionTimeout that results due to or during a database operation.
    """
    http_status_code = 500      # Internal Server Error
    return to_json(
        {
            "result": "failure",
            "error_category": "Database error",
            "error_type": type(pymongo_error).__name__,  
            "error": pymongo_error.message,
            "http_status_code": http_status_code
        }
    ), http_status_code


def bson_format_error_response(bson_error):
    """
    Bson exceptions raised by bson or Pymongo:
    bson.errors.BSONError

    Errors in the bson format mongodb uses to store the data documents. 
    For example, an InvalidBSON, an InvalidDocument, or an InvalidStringData.

    A more specific example: You may have defined a model to have a dictionary,
    where the keys are BSON ObjectIds and the values are another type. Perhaps
    you wanted to map Things to their Scores with a pydantic field in RankedList,
    defined as Dict[PyObjectId, Score]. A model instance with this format will pass
    the pydantic checks, but will cause an InvalidDocument exception when you
    try to write it to mongodb, because the BSON format does not acccept the 
    ObjectId type in keys, it only accepts it in values.
    """
    http_status_code = 400      # Bad Request
    return to_json(
        {
            "result": "failure",
            "error_category": "Bson format error",            
            "error_type": type(bson_error).__name__,  
            "error": bson_error.args[0],
            "http_status_code": http_status_code
        }
    ), http_status_code

