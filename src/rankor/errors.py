# Rankor Exceptions and Flask error handlers

# Flask imports
from flask import jsonify

# Werkzeug imports (for updating the routing rule to raise 
# a specific Error when a trailing slash is missing)
from werkzeug.routing import RequestPath, Rule as WerkzeugDefaultRoutingRule

# Error imports
from werkzeug.exceptions import HTTPException
from pymongo.errors import DuplicateKeyError




# Custom Exceptions --------
class ResourceNotFoundInDatabaseError(HTTPException):
    code = 404
    description = ("The requested resource was not found in the database. "
                   "Please check the requested data carefully and try again.")

class NoTrailingSlashError(HTTPException):
    code = 400
    description = ("The url you sent the request to does not have a trailing "
                   "slash. All endpoint urls of this api end with a / at the end, "
                   "and they won't work without this trailing slash even if "
                   "the rest of the url is correct.")





# Routing Rule to raise an Exception for trailing slashes (instead of redirecting)
# --------

# Update the default routing Rule from Werkzeug that Flask uses, to raise an
# error about a trailing slash. The default Flask (and Werkzeug) behavior is 
# that when it sees a url without a trailing slash, it redirects to the same
# url with the trailing slash. This redirect is nice for human users on a 
# browser, but not desired in a JSON based api. Because 1) Flask returns an
# HTML response that says 'Redirecting...', which is not a response this api
# wants to return, and 2) This is an api for machines to interact with, not 
# human users, and therefore it would rather be strict in the format of requests
# it accepts (requiring the trailing slash), rather than human friendly
class SlashInsistingRoutingRule(WerkzeugDefaultRoutingRule):
    def match(self, path, method=None):
        try:
            result = super(SlashInsistingRoutingRule, self).match(path, method)
        except RequestPath:
            raise NoTrailingSlashError

        return result



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