from datetime import datetime
import os

from pymongo.collection import Collection, ReturnDocument

import flask
from flask import Flask, request, url_for, jsonify
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError

from src.rankor.models import Thing
from src.rankor.pyobjectid import PyObjectId

import settings


# Configure Flask & Flask-PyMongo:
app = Flask(__name__)
app.config["MONGO_URI"] = settings.MONGO_DATABASE_URI
pymongo = PyMongo(app)

# Get a reference to the relevant db collection.
# Use a type-hint, so that your IDE knows what's happening!
