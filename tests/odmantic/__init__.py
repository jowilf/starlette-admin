import os

MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DATABASE: str = os.getenv("MONGO_DATABASE", "test")
