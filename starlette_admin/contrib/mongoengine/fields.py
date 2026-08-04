from dataclasses import dataclass
from typing import Any

from mongoengine import GridFSProxy
from starlette.requests import Request
from starlette_admin.fields import FileField as BaseFileField
from starlette_admin.fields import ImageField as BaseImageField
from starlette_admin.fields import StringField as BaseStringField
from starlette_admin.types import RequestAction


@dataclass
class ObjectIdField(BaseStringField):
    """A string field whose underlying value is a MongoDB ObjectId.

    Registered separately from StringField so the filter registry can bind
    ObjectId-aware filters (eq/neq/in/not_in only) instead of string filters.
    """

    copy_to_clipboard: bool | None = True


@dataclass
class FileField(BaseFileField):
    """FileField backed by a MongoEngine `GridFSProxy`.

    Serializes the stored file to a `{filename, content_type, url}` dict
    instead of the base class's default handling.
    """

    async def serialize_value(self, request: Request, value: Any) -> Any:
        return _serialize_file_field(request, value)


@dataclass
class ImageField(BaseImageField):
    """ImageField backed by a MongoEngine `GridFSProxy`.

    Serializes the same way as [FileField][starlette_admin.contrib.mongoengine.fields.FileField],
    and serves the proxy's `thumbnail_id` (when present) in the list view.
    """

    async def serialize_value(self, request: Request, value: Any) -> Any:
        return _serialize_file_field(request, value)


def _serialize_file_field(
    request: Request, value: GridFSProxy
) -> dict[str, str] | None:
    """Serialize a GridFS-backed field value into display metadata.

    In the list view, serves `thumbnail_id` instead of `grid_id` when the
    proxy has one, so [ImageField][starlette_admin.contrib.mongoengine.fields.ImageField]
    can render a smaller preview image in list rows.

    Parameters:
        request: The current request, used to resolve the action and build the
            file-serving URL.
        value: The GridFS proxy stored on the document.

    Returns:
        A dict with `filename`, `content_type`, and `url` keys, or `None` if
        no file is stored (`value.grid_id` is falsy).
    """
    if value.grid_id:
        id = value.grid_id
        if (
            request.state.action == RequestAction.LIST
            and getattr(value, "thumbnail_id", None) is not None
        ):
            id = value.thumbnail_id
        gridout = value.get()
        gridout.open()
        content_type = gridout._file.get("contentType") or "application/octet-stream"
        return {
            "filename": getattr(value, "filename", "unnamed"),
            "content_type": content_type,
            "url": str(
                request.url_for(
                    request.app.state.ROUTE_NAME + ":api:file",
                    db=value.db_alias,
                    col=value.collection_name,
                    pk=id,
                )
            ),
        }
    return None
