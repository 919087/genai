# mongodb_connection.py
 
from pymongo import MongoClient
 
client = MongoClient('mongodb://localhost:27017/')
db = client['genesis']
collection = db['ragdocs']