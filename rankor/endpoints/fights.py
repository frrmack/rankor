"""
Fight endpoints for a given RankedList: 
/rankor/rankedlists/<ranked_list_id>/fights/

Arrange a new Fight   | GET    /rankor/rankedlists/<ranked_list_id>/fights/new/
Save a Fight result   | POST   /rankor/rankedlists/<ranked_list_id>/fights/      
Delete a Fight        | DELETE /rankor/rankedlists/<ranked_list_id>/fights/<fight_id>
Get recorded Fights   | GET    /rankor/rankedlists/<ranked_list_id>/fights/
Get Fights of a Thing | GET    /rankor/rankedlists/<ranked_list_id>/fights/things/<thing_id>
------------------------------------------------------------------------------
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
from rankor.models import (Fight, 
                           RankedList)

# Pagination imports
from pagination import ListPaginator

# Exception imports
from rankor.errors import ResourceNotFoundInDatabaseError

# Api settings import
import settings

# Database interface import
from rankor import db


# The blueprint with all the RankedThing endpoints
# This will be registered to the Flask app
fight_endpoints = Blueprint('fight_endpoints', __name__)