import os

MONGO_URL = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/") + os.environ.get(
    "MONGO_DATABASE", "testdb"
)
