from devtools import debug  # noqa
from dataclasses import dataclass
from typing import Any, Dict, Optional

from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.fields import FileField as BaseFileField
from starlette_admin.fields import ImageField as BaseImageField
from starlette_admin.fields import StringField


@dataclass
class PasswordField(StringField):
    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return "***"


@dataclass
class FileField(BaseFileField):
    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return _serialize_file_field(request, value, action)


@dataclass
class ImageField(BaseImageField):
    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return _serialize_file_field(request, value, action)


def _serialize_file_field(
    request: Request, value: Any, action: RequestAction
) -> Optional[Dict[str, str]]:
    """
    return a dict, format example:
    # data = {
    #     "filename": "imagen.jpg",
    #     "content_type": "image/jpeg",
    #     "url": "http://localhost:8000/admin/mongoengine/api/file/default/fs/64414a658ac3805e5fc46fcb",
    # }
    # url (route), route must declared for Starlette! (contrib/beanie/admin.py)
    # and receive the 3 parameters (db,col,pk)
    # to be able to download the file
    """
    if value.file_name.gfs_id:
        id = value.file_name.gfs_id
        if (
            action == RequestAction.LIST
            and getattr(value.file_name, "thumbnail_id", None) is not None
        ):
            """Use thumbnail on list page if available"""
            id = value.file_name.thumbnail_id

        return {
            "filename": getattr(value.file_name, "filename", "unamed"),
            "content_type": getattr(
                value.file_name, "content_type", "application/octet-stream"
            ),
            "url": str(
                request.url_for(
                    request.app.state.ROUTE_NAME + ":api:file",
                    db=value.file_name.db_name,
                    col=value.file_name.collection_name,
                    pk=id,
                )
            ),
        }
    return None
