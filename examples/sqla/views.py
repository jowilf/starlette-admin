from sqlalchemy.exc import IntegrityError

from examples.sqla.models import Post
from starlette_admin import EnumField, StringField, ExportType
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import FormValidationError

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


class TagView(ModelView):
    fields = [StringField("name", label="Tag name", help_text="Add unique tag name")]
    form_include_pk = True
    search_builder = False
    column_visibility = False
    export_types = list(ExportType)  # Add all export types

    def handle_exception(self, exc: Exception) -> None:
        """
        As `tag.name` is unique, sqlalchemy will raise IntegrityError
        when trying to save duplicate values. We can catch this error to
        display comprehensible error to users.
        """
        if isinstance(exc, IntegrityError):
            raise FormValidationError(
                errors={"name": "A tag with this name already exist"}
            )
        return super().handle_exception(exc)
