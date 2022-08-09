# Rankor's JSON encoding relies on pydantic's, this module only has a couple of
# simple wrappers for convenience

import json
from pydantic.json import pydantic_encoder, ENCODERS_BY_TYPE


def to_json(obj, **kwargs):
    """
    Encode any object into a JSON string. This includes rankor models, or any
    data structure based on dicts, lists, etc. that include rankor models or
    data types of rankor model fields.
    
    It uses pydantic's encoder, which uses the ENCODERS_BY_TYPE dict to figure
    out how to encode non-basic types. For example, all datetime objects are
    converted to an ISO8601 string via their datetime.datetime.isoformat()
    method, and when we define PyObjectId and PyObjectIdString in
    rankor.models.pyobjectid, we are updating this ENCODERS_BY_TYPE how to
    encode BsonObjectId and PyObjectId (by converting them into
    PyObjectIdStrings). Any other rankor choices on how to encode different data
    types can be done by further updating this ENCODERS_BY_TYPE.

    This function also defines rankor's default json pretty-print format with
    the indent and sort_keys keywords
    """
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

    While re-parsing a json dumped from a dict by to_json() is slightly
    ridiculous, pydantic.json.pydantic_encoder, json.JSONEncoder and json.dumps
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
