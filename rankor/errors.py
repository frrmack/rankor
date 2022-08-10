"""
Exceptions raised by rankor.

Custom Exceptions for specific purposes that are not covered by Exceptions 
defined in other packages that rankor uses (such as flask, pymongo, etc.)
"""

# Exception imports from other packages
from werkzeug.exceptions import NotFound, Conflict


class ResourceNotFoundInDatabaseError(NotFound):
    code = 404
    description = ("The requested <resource> was not found in the database. "
                   "Please check the requested data carefully and try again.")
    def __init__(self, 
                 description=None, 
                 response=None, 
                 resource_type=None, 
                 resource_id=None) -> None:
        resource_repr = "resource"
        if description is None:
            if resource_type is not None:
                resource_repr = resource_type
            if resource_id is not None:
                resource_repr = f"{resource_repr} with the id {resource_id}"
            description = self.description.replace("<resource>", resource_repr)
        super(ResourceNotFoundInDatabaseError,self).__init__(description, response)


class SameNameResourceAlreadyExistsError(Conflict):
    code = 409
    description = ("A <resource> with the same name already exists in the database. "
                   "Either update that <resource> instead, or delete that before "
                   "creating this, or give this new <resource> a different name")
    def __init__(self, 
                 description=None, 
                 response=None, 
                 same_name_resource=None,
                 resource_type=None):
        self.same_name_resource = same_name_resource
        if description is None:
            resource_repr = "resource"
            if resource_type is not None:
                resource_repr = resource_type
            description = self.description.replace("<resource>", resource_repr)        
        super(SameNameResourceAlreadyExistsError, self).__init__(description, response)


class NoTrailingSlashError(NotFound):
    code = 404
    description = ("The URL you sent the request to does not have a trailing "
                   "slash. All endpoint URLs of this api end with a / at the end, "
                   "and they won't work without this trailing slash even if "
                   "the rest of the URL is correct.")
