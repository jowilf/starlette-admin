"""Admin view declarations for the Tortoise blog example."""

from models import Comment
from starlette_admin.contrib.tortoise import InlineModelView, ModelView


class AuthorView(ModelView):
    fields = ["id", "name", "email", "bio", "joined_on", "posts", "profile"]
    searchable_fields = ["name", "email", "bio"]


class AuthorProfileView(ModelView):
    pass


class TagView(ModelView):
    pass


class CommentInline(InlineModelView):
    model = Comment
    # fk_attr auto-detected: Comment has exactly one FK to Post
    fields = ["id", "author_name", "body"]
    extra = 1


class PostView(ModelView):
    fields = [
        "id",
        "title",
        "content",
        "status",
        "views",
        "published",
        "metadata",
        "created_at",
        "updated_at",
        "author",
        "tags",
    ]
    searchable_fields = ["title", "content", "status", "views", "published", "author"]
    fields_default_sort = [("id", True)]
    inlines = [CommentInline]
