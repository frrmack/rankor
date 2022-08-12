"""
RankedThing endpoint for a given RankedList: 
/rankor/rankedlists/<ranked_list_id>/ranked_things/

List RankedThings  |  GET /rankor/rankedlists/<ranked_list_id>/ranked_things/
"""

# Python inspection imports 
# (to get the name of an endpoint from within)
from sys import _getframe

# Flask imports
from flask import Blueprint, request

# Pymongo query imports
from pymongo.collection import ReturnDocument

# Python datetime import for timestamps
from datetime import datetime

# Encoder imports
from rankor.json import to_json

# Rankor model imports
from rankor.models import (Thing,
                           Score,
                           RankedList)

# Pagination imports
from pagination import Paginator

# Exception imports
from rankor.errors import ResourceNotFoundInDatabaseError

# Api settings import
import settings

# Database interface import
from rankor import db


# The blueprint with all the RankedThing endpoints
# This will be registered to the Flask app
ranked_thing_endpoints = Blueprint('ranked_thing_endpoints', __name__)