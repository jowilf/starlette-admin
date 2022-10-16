from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.contrib.sqla.exceptions import NotSupportedValue
from starlette_admin.fields import FileField as BaseFileField
from starlette_admin.fields import ImageField as BaseImageField


@dataclass
class FileField(BaseFileField):
    """This field will automatically work with sqlalchemy_file.FileField"""

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        try:
            return _serialize_sqlalchemy_file_library(
                request, value, action, self.multiple
            )
        except (
            ImportError,
            ModuleNotFoundError,
            NotSupportedValue,
        ):  # pragma: no cover
            return super().serialize_value(request, value, action)


@dataclass
class ImageField(BaseImageField):
    """This field will automatically work with sqlalchemy_file.ImageField"""

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        try:
            return _serialize_sqlalchemy_file_library(
                request, value, action, self.multiple
            )
        except (
            ImportError,
            ModuleNotFoundError,
            NotSupportedValue,
        ):  # pragma: no cover
            return super().serialize_value(request, value, action)


def _serialize_sqlalchemy_file_library(
    request: Request, value: Any, action: RequestAction, is_multiple: bool
) -> Optional[Union[List[Dict[str, Any]], Dict[str, Any]]]:
    from sqlalchemy_file import File

    if isinstance(value, File) or (
        isinstance(value, list) and all([isinstance(f, File) for f in value])
    ):
        data = []
        for item in value if isinstance(value, list) else [value]:
            path = item["path"]
            if (
                action == RequestAction.LIST
                and getattr(item, "thumbnail", None) is not None
            ):
                """Use thumbnail on list page if available"""
                path = item["thumbnail"]["path"]
            storage, file_id = path.split("/")
            data.append(
                {
                    "content_type": item["content_type"],
                    "filename": item["filename"],
                    "url": request.url_for(
                        request.app.state.ROUTE_NAME + ":api:file",
                        storage=storage,
                        file_id=file_id,
                    ),
                }
            )
        return data if is_multiple else data[0]
    raise NotSupportedValue  # pragma: no cover
