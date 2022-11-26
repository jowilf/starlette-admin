from datetime import date, timedelta
from typing import Any, Dict

from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from starlette_admin import EnumField, ExportType, StringField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import FormValidationError

from .models import Post

AVAILABLE_USER_TYPES = [
    ("admin", "Admin"),
    ("content-writer", "Content writer"),
    ("editor", "Editor"),
    ("regular-user", "Regular user"),
]


class UserView(ModelView):
    fields = [
        "id",
        "last_name",
        "first_name",
        EnumField.from_choices("type", AVAILABLE_USER_TYPES),
        "posts",
    ]


class PostView(ModelView):
    exclude_fields_from_list = ["text"]
    exclude_fields_from_create = [Post.created_at]
    exclude_fields_from_edit = ["created_at"]

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        """By default, starlette-admin doesn't validate your data, you need
        to override this function and write your own validation, or you can
        use sqlmodel to autovalidate your data with pydantic.

        Raise FormValidationError to display error in forms"""
        errors: Dict[str, str] = {}
        _2day_from_today = date.today() + timedelta(days=2)
        if data["title"] is None or len(data["title"]) < 3:
            errors["title"] = "Ensure this value has at least 03 characters"
        if data["text"] is None or len(data["text"]) < 10:
            errors["text"] = "Ensure this value has at least 10 characters"
        if data["date"] is None or data["date"] < _2day_from_today:
            errors["date"] = "We need at least one day to verify your post"
        if data["publisher"] is None:
            errors["publisher"] = "Publisher is required"
        if data["tags"] is None or len(data["tags"]) < 1:
            errors["tags"] = "At least one tag is required"
        if len(errors) > 0:
            raise FormValidationError(errors)
        return await super().validate(request, data)


class TagView(ModelView):
    fields = [StringField("name", label="Tag name", help_text="Add unique tag name")]
    form_include_pk = True
    search_builder = False
    column_visibility = False
    export_types = list(ExportType)  # Add all export types

    def handle_exception(self, exc: Exception) -> None:
        """
        As `tag.name` is unique, sqlalchemy will raise IntegrityError
        when trying to save duplicate values. We can catch this error and
        display comprehensible error to users.
        """
        if isinstance(exc, IntegrityError):
            raise FormValidationError(
                errors={"name": "A tag with this name already exist"}
            )
        return super().handle_exception(exc)
