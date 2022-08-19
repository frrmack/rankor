# Pydantic provides data validation and creates a schema using typing, which is
# Python's own runtime support for type hints. This is good and necessary for a
# robust api. BaseModel is the starting point for all pydantic models.
from pydantic import BaseModel

# JSON encoding
import json


class JsonableModel(BaseModel):
    """
    Model template class that handles json encoding for rankor's models to
    inherit. 

    Rankor needs to return json strings as responses, which include
    representations of its models. All models that are stored directly in the
    database as documents inherit from MongoModel, which inherits from this
    JsonableModel. A couple of simple models that live within other models' data
    and not in their own collection in the database (and therefore without
    unique ids) inherit directly from JsonableModel. 

    While to_jsonable_dict() returns a python dict with the relevant json
    encodings, to_json() returns an actual json string. The overriding of the
    BaseModel.dict() method sets the default behavior to excluding empty fields,
    which means fields that are set to None do not show up in dict or json
    representations of the model unless explicitly stated.

    The json encoding relies on pydantic's encoder. More info on pydantic's json
    encoding and model exporting:
    https://pydantic-docs.helpmanual.io/usage/exporting_models/
    """

    def dict(self, *args, exclude_none=True, **kwargs):
        """
        Overrides the BaseModel.dict() method, which returns a dict
        representation of the model, to set the exclude_none keyword to True by
        default.

        This excludes fields that are set to None from the dict representation
        unless explicitly asked for. This is the default serialization behavior
        of rankor models. For example, optional fields that are never set are
        not shown in dict or json representations of the model.

        This dict() method gets called for any representation / serialization
        process on pydantic models. For example, it's what pydantic's encoder
        calls on a BaseModel object for json encoding.
        """
        return super(JsonableModel, self).dict(
            *args, 
            exclude_none=exclude_none, 
            **kwargs
        )

    def to_json(self, *args, **kwargs):
        """
        Returns a json representation of the model.
        
        A simple wrapper around BaseModel.json() with a few keyword arguments
        already set as the default json string serialization behavior of
        RankorModel. It uses pydantic's json encoder, which looks at
        pydantic.json.ENCODERS_BY_TYPE to figure out how to encode non-standard
        types. 
        
        It excludes fields that are None from the json result by default and
        pretty-print-ifies the json with sorted keys and indents for
        readability.
        """
        return self.json(
            *args, 
            exclude=None,
            indent=2, 
            sort_keys=True, 
            **kwargs
        )


    def to_jsonable_dict(self, *args, **kwargs):
        """
        Returns a python dict representation of the model, within which
        non-basic types are converted to json-friendly basic types like str.

        Encodes complex classes in relevant serialization types just as the
        to_json() method (such as converting datetime objects to isoformat
        timestamp strings, for example), but returns a dict representation with
        these json-able contents instead of a json string. 
        
        This is handy when you need the encoding but want to keep a dict, for
        example when you need to include it in another dict which will be
        encoded to json in its entirety. It excludes fields set to None (this
        includes Optional fields that were never set).
        
        While re-parsing a json dumped from a dict by BaseModel.json is slightly
        ridiculous, pydantic.json.pydantic_encoder, pydantic.BaseModel.json, and
        pydantic.BaseModel.dict are written in a way that this functionality is
        a bit difficult to ensure without writing a custom json encoder or using
        an existing external one (such as fastapi.encoders.jsonable_encoder),
        and it's simpler and more straightforward to just do this instead. The
        performance difference is absolutely negligible for rankor's use cases. 
        
        This lacking feature (a jsonable encoder returning a dict) has actually
        been proposed for pydantic, and it's favored by Samuel Colvin
        (pydantic's author). You can read more about it here:
        https://github.com/samuelcolvin/pydantic/issues/951#issuecomment-552463606
        """
        return json.loads(self.to_json(*args, **kwargs))



