from typing import Any, ClassVar

from pydantic import ValidationError
from sqlmodel import SQLModel
from starlette.requests import Request
from starlette_admin.contrib.sqla.converters import BaseSQLAModelConverter
from starlette_admin.contrib.sqla.view import InlineModelView as SQLAInlineModelView
from starlette_admin.contrib.sqla.view import ModelView as BaseModelView
from starlette_admin.fields import FileField, RelationField
from starlette_admin.helpers import pydantic_error_to_form_validation_errors


class ModelView(BaseModelView):
    def __init__(
        self,
        model: type[SQLModel],
        icon: str | None = None,
        display_name: str | None = None,
        menu_label: str | None = None,
        key: str | None = None,
        converter: BaseSQLAModelConverter | None = None,
    ):
        super().__init__(model, icon, display_name, menu_label, key, converter)

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        """Validate form data against the SQLModel, excluding file and relation fields.

        File and relation fields hold values (uploads, related objects) that the
        Pydantic model itself cannot validate, so they are stripped from `data`
        before calling `model_validate`.
        """
        fields_to_exclude = [
            f.name
            for f in self.get_fields_list(request)
            if isinstance(f, (FileField, RelationField))
        ]
        self.model.model_validate(
            {k: v for k, v in data.items() if k not in fields_to_exclude}
        )

    async def handle_exception(self, request: Request, exc: Exception) -> None:
        if isinstance(exc, ValidationError):
            raise pydantic_error_to_form_validation_errors(exc)
        return await super().handle_exception(request, exc)  # pragma: no cover


class InlineModelView(SQLAInlineModelView):
    """Inline editing of SQLModel-backed related records inside a parent form.

    Inherits FK detection and session logic from the SQLAlchemy
    `InlineModelView` and adds SQLModel Pydantic validation on top.

    Declare `model` as a class attribute (a `SQLModel` table class). `fk_attr`
    is optional and is auto-detected from the parent's SQLAlchemy relationship
    when omitted.

    Example:

        ```python
        class CommentInline(InlineModelView):
            model = Comment
            fields = ["id", "author", "body"]
            extra = 1


        class PostView(ModelView):
            inlines = [CommentInline]
        ```
    """

    model: ClassVar[type[SQLModel]]  # type: ignore[misc]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        fields_to_exclude = [
            f.name
            for f in self.get_fields_list(request)
            if isinstance(f, (FileField, RelationField))
        ]
        self.model.model_validate(
            {k: v for k, v in data.items() if k not in fields_to_exclude}
        )

    async def handle_exception(self, request: Request, exc: Exception) -> None:
        if isinstance(exc, ValidationError):
            raise pydantic_error_to_form_validation_errors(exc)
        return await super().handle_exception(request, exc)  # pragma: no cover
