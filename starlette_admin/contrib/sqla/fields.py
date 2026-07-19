from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from starlette.requests import Request
from starlette_admin.contrib.sqla.exceptions import NotSupportedValue
from starlette_admin.fields import FileField as BaseFileField
from starlette_admin.fields import ImageField as BaseImageField
from starlette_admin.fields import StringField
from starlette_admin.tools import iterencode
from starlette_admin.types import (
    RequestAction,  # used in _serialize_sqlalchemy_file_library
)


@dataclass(init=False)
class MultiplePKField(StringField):
    """Virtual field to represent multiple primary keys as a single field.

    This field joins the values of multiple primary key columns into a
    single string, encoding/decoding each value.
    """

    def __init__(self, pk_attrs: Sequence[str]):
        self.pk_attrs = pk_attrs
        name = ",".join(pk_attrs)
        super().__init__(
            name,
            exclude_from_list=True,
            exclude_from_detail=True,
            exclude_from_edit=True,
            exclude_from_create=True,
        )

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        """Encode the object's primary key values into a single string."""
        return iterencode(str(getattr(obj, n)) for n in self.name.split(","))


@dataclass
class FileField(BaseFileField):
    """A `FileField` that serializes values stored with `sqlalchemy_file.FileField`."""

    async def serialize_value(self, request: Request, value: Any) -> Any:
        try:
            return _serialize_sqlalchemy_file_library(
                request, value, request.state.action, self.multiple
            )
        except (
            ImportError,
            ModuleNotFoundError,
            NotSupportedValue,
        ):  # pragma: no cover
            return await super().serialize_value(request, value)


@dataclass
class ImageField(BaseImageField):
    """An `ImageField` that serializes values stored with `sqlalchemy_file.ImageField`."""

    async def serialize_value(self, request: Request, value: Any) -> Any:
        try:
            return _serialize_sqlalchemy_file_library(
                request, value, request.state.action, self.multiple
            )
        except (
            ImportError,
            ModuleNotFoundError,
            NotSupportedValue,
        ):  # pragma: no cover
            return await super().serialize_value(request, value)


def _serialize_sqlalchemy_file_library(
    request: Request, value: Any, action: RequestAction, is_multiple: bool
) -> list[dict[str, Any]] | dict[str, Any] | None:
    from sqlalchemy_file import File

    if isinstance(value, File) or (
        isinstance(value, list) and all(isinstance(f, File) for f in value)
    ):
        data = []
        for item in value if isinstance(value, list) else [value]:
            path = item["path"]
            if (
                action == RequestAction.LIST
                and getattr(item, "thumbnail", None) is not None
            ):
                # Prefer the thumbnail over the full image on the list page.
                path = item["thumbnail"]["path"]
            storage, file_id = path.split("/")
            data.append(
                {
                    "content_type": item["content_type"],
                    "filename": item["filename"],
                    "url": str(
                        request.url_for(
                            request.app.state.ROUTE_NAME + ":api:file",
                            storage=storage,
                            file_id=file_id,
                        )
                    ),
                }
            )
        return data if is_multiple else data[0]
    raise NotSupportedValue  # pragma: no cover
