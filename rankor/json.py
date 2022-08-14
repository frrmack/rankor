"""
JSON encoding code that knows how to handle rankor's model and field data types.

Rankor's JSON encoding relies on pydantic's, this module only has a couple of
simple wrappers for convenience. The MongoModel class (upon which almost all
rankor models are built) has its own to_json and to_jsonable_dict methods, which
are also used throughout rankor's code. The functions here provide standalone
encoders that can be used on any object, including those models.
"""

# Encoder imports
import json
from pydantic.json import pydantic_encoder

# Model imports
from rankor.models import JsonableModel


def to_json(obj, **kwargs):
    """
    Encode any object into a JSON string. This includes rankor models, or any
    complex data structure based on dicts, lists, etc. that include rankor
    models or data types of rankor model fields.
    
    It uses pydantic's encoder, which uses the pydantic.json.ENCODERS_BY_TYPE
    dict to figure out how to encode non-basic types. For example, all datetime
    objects are converted to an ISO8601 string via their
    datetime.datetime.isoformat() method by default, since pydantic's
    pydantic.json.ENCODERS_BY_TYPE dict has the key-value pair 
    {datetime.datetime: isoformat} where isoformat is a function defined as
    def isoformat(o): return o.isoformat()

    When we define PyObjectId and PyObjectIdString in rankor.models.pyobjectid,
    we also update this ENCODERS_BY_TYPE, telling it how to encode BsonObjectId
    and PyObjectId (by converting them into PyObjectIdStrings). Any other rankor
    choices on how to encode different data types can be implemented by further
    updating this ENCODERS_BY_TYPE dict.

    This function also defines rankor's default json pretty-print format with
    the indent and sort_keys keywords
    """
    if isinstance(obj, JsonableModel): 
        return obj.to_json()
    else:
        return json.dumps(
            obj,
            default=pydantic_encoder,
            indent=2,
            sort_keys=True,
            **kwargs
        )


def to_jsonable_dict(obj, **kwargs):
    """
    Encodes complex classes in relevant serialization types just as to_json()
    above (such as converting datetime objects to isoformat timestamp strings,
    for example), but returns a dict representation with these json-able
    contents instead of a json string. This is handy when you need the encoding
    but want to keep a dict, for example when you need to include it in another
    dict which will be encoded to json in its entirety. 

    While re-parsing a json dumped by to_json() into a dict again is slightly
    ridiculous, pydantic.json.pydantic_encoder, json.JSONEncoder, and json.dumps
    are written in a way that this functionality is a bit difficult to ensure
    without writing a custom json encoder from scratch or using an existing
    external one (such as fastapi.encoders.jsonable_encoder). It's simpler and
    more straightforward to just do this instead. The performance difference is
    absolutely negligible for rankor's use cases. 
        
    This lacking feature (a jsonable encoder returning a dict) has actually been
    proposed for pydantic, and it's favored by Samuel Colvin (pydantic's
    author). You can read more about it here:
    https://github.com/samuelcolvin/pydantic/issues/951#issuecomment-552463606
    """
    return json.loads(to_json(obj, **kwargs))
