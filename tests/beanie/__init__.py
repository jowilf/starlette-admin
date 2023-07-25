import os

MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DATABASE: str = os.getenv("MONGO_DATABASE", "test")
MONGO_COL_GRIDFS: str = os.getenv("MONGO_COL_GRIDFS", "fs_files")
