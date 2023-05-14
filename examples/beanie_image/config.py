import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "starlette_admin_beanie"
    mongo_col_gridfs: str = "fs_files"
    upload_dir: str = "upload/"

    class Config:
        env_file = os.path.join(os.getcwd(), ".env")
        env_file_encoding = "utf-8"


CONFIG = Settings()  # type: ignore
