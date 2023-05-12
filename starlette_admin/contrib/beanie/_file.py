from typing import Optional, Union

from beanie import PydanticObjectId
from fastapi import UploadFile
from pydantic import BaseModel


class FileGfs(BaseModel):
    gfs_id: PydanticObjectId
    filename: str
    db_name: Optional[str] = "fastapi_admin"
    collection_name: Optional[str] = "fs_files"
    content_type: Optional[str] = "application/octet-stream"
    multiple: Optional[bool] = False
    thumbnail_id: PydanticObjectId | None = None


class File(BaseModel):
    file_name: Union[FileGfs, UploadFile, None] = None


class Image(BaseModel):
    file_name: Union[FileGfs, UploadFile, None] = None
