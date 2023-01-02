from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette_admin import DateTimeField
from starlette_admin._types import RequestAction
from starlette_admin.contrib.sqla.exceptions import NotSupportedValue
from starlette_admin.fields import FileField as BaseFileField
from starlette_admin.fields import ImageField as BaseImageField
from starlette_admin.i18n import get_locale

arrow = None
try:
    import arrow
except ImportError:
    pass


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


@dataclass
class ArrowField(DateTimeField):
    """
    This field is used to represent sqlalchemy_utils.types.arrow.ArrowType
    """

    def __post_init__(self) -> None:
        if not arrow:
            raise ImportError("'arrow' package is required to use 'ArrowField'")
        super().__post_init__()

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        try:
            return arrow.get(form_data.get(self.id))  # type: ignore
        except (TypeError, arrow.parser.ParserError):
            return None

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> str:
        assert isinstance(value, arrow.Arrow), f"Expected Arrow, got  {type(value)}"
        if action != RequestAction.EDIT:
            return value.humanize(locale=get_locale())
        return value.isoformat()


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
