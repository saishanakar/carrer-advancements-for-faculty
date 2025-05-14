
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["qr_attendance"]
users_collection = db["users"]
attendance_collection = db["attendance"]
