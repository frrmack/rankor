# Exceptions raised by Rankor
# Custom exceptions for specific purposes that are not covered by exceptions 
# defined in other packages that rankor uses (such as flask, pymongo, etc.)


# Exception imports from other packages
from werkzeug.exceptions import HTTPException


class ResourceNotFoundInDatabaseError(HTTPException):
    code = 404
    description = ("The requested <resource> was not found in the database. "
                   "Please check the requested data carefully and try again.")
    def __init__(self, 
                 description=None, 
                 response=None, 
                 resource_cls_name=None, 
                 resource_id=None) -> None:
        resource_repr = "resource"
        if resource_cls_name is not None:
            resource_repr = resource_cls_name
        if resource_id is not None:
            resource_repr = f"{resource_repr} with the id {resource_id}"
        if description is None:
            description = self.description.replace("<resource>", resource_repr)
        super().__init__(description, response)


class SameNameResourceAlreadyExistsError(HTTPException):
    code = 400
    description = ("A <resource> with the same name already exists in the database. "
                   "Either update that <resource> instead, or delete that before "
                   "creating this, or give this new <resource> a different name")
    def __init__(self, 
                 description=None, 
                 response=None, 
                 same_name_resource=None,
                 resource_cls_name=None):
        self.same_name_resource = same_name_resource
        resource_repr = "resource"
        if resource_cls_name is not None:
            resource_repr = resource_cls_name
        if description is None:
            description = self.description.replace("<resource>", resource_repr)        
        super().__init__(description, response)


class NoTrailingSlashError(HTTPException):
    code = 400
    description = ("The url you sent the request to does not have a trailing "
                   "slash. All endpoint urls of this api end with a / at the end, "
                   "and they won't work without this trailing slash even if "
                   "the rest of the url is correct.")
