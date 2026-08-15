from collections.abc import Sequence
from typing import Any, ClassVar

from pydantic import ValidationError
from sqlalchemy import inspect
from sqlmodel import SQLModel
from starlette.requests import Request
from starlette_admin.contrib.sqla.converters import BaseSQLAModelConverter
from starlette_admin.contrib.sqla.view import InlineModelView as SQLAInlineModelView
from starlette_admin.contrib.sqla.view import ModelView as BaseModelView
from starlette_admin.fields import BaseField, FileField, HasMany, RelationField
from starlette_admin.helpers import pydantic_error_to_form_validation_errors


def _fk_columns_by_relation(
    model: type[SQLModel], fields: Sequence[BaseField]
) -> dict[str, str]:
    """Return `{local_fk_column_key: relation_field_name}` for MANYTOONE relations."""
    mapper = inspect(model)
    result: dict[str, str] = {}
    for field in fields:
        if not isinstance(field, RelationField) or isinstance(field, HasMany):
            continue
        prop = mapper.relationships.get(field.name)
        if prop is None or prop.direction.name != "MANYTOONE":
            continue
        for local_col, _ in prop.local_remote_pairs:
            result[mapper.get_property_by_column(local_col).key] = field.name
    return result


def _fk_values_from_relations(
    model: type[SQLModel], fields: Sequence[BaseField], data: dict[str, Any]
) -> dict[str, Any]:
    """Derive FK column values from already-resolved MANYTOONE relation fields.

    A required FK column (e.g. `company_id`) is hidden from the form in favor
    of its relation field (e.g. `company`), so pydantic never sees it in the
    submitted data and rejects it as missing. Populate it here from the
    related object `_arrange_data` already resolved onto the relation field.
    """
    mapper = inspect(model)
    fk_values: dict[str, Any] = {}
    for field in fields:
        if not isinstance(field, RelationField) or isinstance(field, HasMany):
            continue
        prop = mapper.relationships.get(field.name)
        if prop is None or prop.direction.name != "MANYTOONE":
            continue
        related = data.get(field.name)
        for local_col, remote_col in prop.local_remote_pairs:
            local_key = mapper.get_property_by_column(local_col).key
            if related is None:
                fk_values[local_key] = None
            else:
                remote_key = (
                    inspect(type(related)).get_property_by_column(remote_col).key
                )
                fk_values[local_key] = getattr(related, remote_key)
    return fk_values


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
        fields = self.get_fields_list(request)
        fields_to_exclude = [
            f.name for f in fields if isinstance(f, (FileField, RelationField))
        ]
        payload = {k: v for k, v in data.items() if k not in fields_to_exclude}
        payload.update(_fk_values_from_relations(self.model, fields, data))
        self.model.model_validate(payload)

    async def handle_exception(self, request: Request, exc: Exception) -> None:
        if isinstance(exc, ValidationError):
            key_map = _fk_columns_by_relation(self.model, self.get_fields_list(request))
            raise pydantic_error_to_form_validation_errors(exc, key_map)
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
        fields = self.get_fields_list(request)
        fields_to_exclude = [
            f.name for f in fields if isinstance(f, (FileField, RelationField))
        ]
        payload = {k: v for k, v in data.items() if k not in fields_to_exclude}
        payload.update(_fk_values_from_relations(self.model, fields, data))
        self.model.model_validate(payload)

    async def handle_exception(self, request: Request, exc: Exception) -> None:
        if isinstance(exc, ValidationError):
            key_map = _fk_columns_by_relation(self.model, self.get_fields_list(request))
            raise pydantic_error_to_form_validation_errors(exc, key_map)
        return await super().handle_exception(request, exc)  # pragma: no cover
