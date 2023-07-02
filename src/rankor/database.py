# Import database interface library
from flask_pymongo import PyMongo

# Initialize the interface
rankor_pymongo_interface = PyMongo()

# Provide the database connection if asked
def get_database_connection():
    return rankor_pymongo_interface.db