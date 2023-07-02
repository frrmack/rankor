# Import database interface library
from flask_pymongo import PyMongo

# Initialize the interface
RANKOR_PYMONGO_INTERFACE = PyMongo()

# Provide the database connection if asked
def get_database_connection():
    return RANKOR_PYMONGO_INTERFACE.db