"""Tortoise ORM models for a small blog application.

Demonstrates the field types the Tortoise contrib converts automatically:
scalars, enums, dates, JSON, plus foreign key, one-to-one and many-to-many
relations.
"""

from enum import StrEnum

from tortoise import Tortoise, fields
from tortoise.models import Model


class PostStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=255, unique=True)
    bio = fields.TextField(null=True)
    joined_on = fields.DateField(null=True)

    def __admin_repr__(self, request):
        return self.name


class AuthorProfile(Model):
    id = fields.IntField(primary_key=True)
    author = fields.OneToOneField("models.Author", related_name="profile")
    website = fields.CharField(max_length=255, null=True)
    twitter = fields.CharField(max_length=100, null=True)


class Tag(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50, unique=True)

    def __admin_repr__(self, request):
        return self.name


class Post(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=200)
    content = fields.TextField()
    status = fields.CharEnumField(PostStatus, default=PostStatus.DRAFT)
    views = fields.IntField(default=0)
    published = fields.BooleanField(default=False)
    metadata = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    author = fields.ForeignKeyField("models.Author", related_name="posts", null=True)
    tags = fields.ManyToManyField("models.Tag", related_name="posts")

    def __admin_repr__(self, request):
        return self.title


class Comment(Model):
    id = fields.IntField(primary_key=True)
    post = fields.ForeignKeyField("models.Post", related_name="comments")
    author_name = fields.CharField(max_length=100)
    body = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)


# Resolve relations at import time so admin views (built before the async
# Tortoise.init() runs in the app lifespan) see them.
Tortoise.init_models([__name__], "models")
