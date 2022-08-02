# Error handlers to return valid and useful responses in case of errors. 
# These are critical to provide JSON responses instead of Flask's default HTML
# responses; they also try to provide enough information for maximum context.


# robust JSON encoding from fastapi
from fastapi.encoders import jsonable_encoder


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
    response = jsonable_encoder({"error_type": type(http_exception).__name__,  
                                 "error": http_exception.description,
                                 "http_status_code": http_status_code})
    return response, http_status_code


def data_validation_error_response(validation_error):
    """
    Validation exceptions raised by Pydantic:
    pydantic.error_wrappers.ValidationError

    Data validation errors encountered when the input data does not correctly
    fulfill the type requirements defined by the api. For example, when a 
    string value is provided for a field that's supposed to be a float.
    """
    http_status_code = 400      # Bad Request
    err_msg = ("The data you provided does not fully match the type requirements. "
               "Please provide valid data types as input.")    
    num_validation_issues = len(validation_error.errors())
    details = {"number_of_validation_errors": num_validation_issues,
               "validation_error_list": validation_error.errors()}
    print(details)
    response = jsonable_encoder({"error_type": type(validation_error).__name__, 
                                 "error": err_msg,
                                 "error_details": details,
                                 "http_status_code": http_status_code})
    return response, http_status_code


def database_error_response(pymongo_error):
    """
    Database exceptions raised by Pymongo:
    pymongo.errors.PyMongoError

    Errors encountered when an interaction with the database is gone wrong. 
    For example, a DuplicateKeyError, a DocumentTooLargeError, or an 
    ExecutionTimeout that results due to or during a database operation.
    """
    http_status_code = 500      # Internal Server Error
    response = jsonable_encoder({"error_type": type(pymongo_error).__name__,  
                                 "error": pymongo_error.message,
                                 "http_status_code": http_status_code})
    return response, http_status_code





# def general_json_error_response(error):
#     """
#     General catch all error handler to return all remaining error responses 
#     as JSON (instead of Flask's default HTML)
#     """
#     http_code = 500
#     print(dir(error))
#     print(error.errors())
#     if isinstance(error, HTTPException):
#         http_code = error.code
#     elif isinstance(error, DuplicateKeyError):
#         http_code = 400
#     return jsonify({"error_type": type(error).__name__,  
#                     "error": error.description}), http_code