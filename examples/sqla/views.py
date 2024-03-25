from datetime import date, timedelta
from typing import Any, Dict, List

from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from starlette_admin import (
    EnumField,
    ExportType,
    HasOne,
    StringField,
    action,
    row_action,
)
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import FormValidationError

from .models import Post, User

AVAILABLE_USER_TYPES = [
    ("admin", "Admin"),
    ("content-writer", "Content writer"),
    ("editor", "Editor"),
    ("regular-user", "Regular user"),
]

AVAILABLE_POST_STATUSES = [
    ("pending", "Pending"),
    ("rejected", "Rejected"),
    ("approved", "Approved"),
]


class UserView(ModelView):
    fields = [
        "id",
        "last_name",
        "first_name",
        EnumField("type", choices=AVAILABLE_USER_TYPES, select2=False),
        "posts",
    ]
    fields_default_sort = [User.last_name, ("first_name", True)]


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

    async def validate_add_tag(self, request: Request, data: Dict[str, Any]):
        errors: Dict[str, str] = {}
        if data["tag"] is None:
            errors["tag"] = "You must specify a tag"
        if len(errors) > 0:
            raise FormValidationError(errors)

    @action(
        name="add_tag",
        text="Add a tag for selected posts",
        icon_class="fas fa-tag",
        confirmation="Are you sure you want to add a tag to all of these posts?",
        form_fields=[HasOne("tag", identity="tag")],
    )
    async def add_tag(self, request: Request, pks: List[Any], data: Dict):
        await self.validate_add_tag(request, data)

        tag = data["tag"]
        posts = await self.find_by_pks(request, pks)
        for post in posts:
            post.tags.append(tag)

        request.state.session.commit()
        return f"Successfully added tag {tag.name} to selected posts"

    @row_action(
        name="approve",
        text="Approve selected posts",
        icon_class="fas fa-tag",
        confirmation="Are you sure you want to change selected posts' status?",
        form_fields=[
            EnumField("status", choices=AVAILABLE_POST_STATUSES, select2=False)
        ],
    )
    async def approve(self, request: Request, pk: Any, data: Dict):
        status = data["status"]
        post = await self.find_by_pk(request, pk)
        post.status = status
        request.state.session.commit()
        return f"Post status successfully changed to {status}"


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
