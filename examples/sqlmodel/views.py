from starlette_admin import (
    CollectionField,
    ColorField,
    EmailField,
    ExportType,
    IntegerField,
    JSONField,
    ListField,
    StringField,
    URLField,
)
from starlette_admin.contrib.sqlmodel import ModelView

from .models import Comment, Post


class MyModelView(ModelView):
    page_size = 5
    page_size_options = [5, 10, 25 - 1]
    export_types = [ExportType.EXCEL, ExportType.CSV]


class PostView(MyModelView):
    fields = [
        "id",
        "title",
        "content",
        ListField(StringField("tags")),
        "published_at",
        "publisher",
        "comments",
    ]
    exclude_fields_from_list = [Post.content]
    exclude_fields_from_create = [Post.published_at]
    exclude_fields_from_edit = ["published_at"]


class CommentView(MyModelView):
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    searchable_fields = [Comment.content, Comment.created_at]
    sortable_fields = [Comment.pk, Comment.content, Comment.created_at]


class DumpView(MyModelView):
    fields = [
        "id",
        EmailField("email"),
        URLField("url", required=True),
        ColorField("color"),
        JSONField("json_field"),
        ListField(
            CollectionField(
                "configs",
                fields=[
                    StringField("key"),
                    IntegerField("value", help_text="multiple of 5"),
                ],
            )
        ),
    ]
    exclude_fields_from_list = ("configs",)
    searchable_fields = ("email", "url")
