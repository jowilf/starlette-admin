import enum
from datetime import datetime
from typing import Optional

from jinja2 import Template
from markupsafe import escape
from pydantic import EmailStr
from sqlalchemy import JSON, Column, DateTime, String, Text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel
from starlette.requests import Request


class Role(enum.StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    WRITER = "writer"


class ArticleStatus(enum.StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    full_name: str = Field(min_length=2, index=True)
    email: EmailStr = Field(sa_column=Column(String(200), unique=True, index=True))
    role: Role = Field(
        sa_column=Column(SAEnum(Role), default=Role.WRITER, nullable=False)
    )
    avatar_color: str | None = Field(
        sa_column=Column(String(10), nullable=True), default=None
    )
    bio: str | None = Field(sa_column=Column(Text, nullable=True), default=None)
    created_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True), default=None
    )

    articles: list["Article"] = Relationship(back_populates="author")

    async def __admin_repr__(self, request) -> str:
        return self.full_name

    async def __admin_select2_repr__(self, _request: Request) -> str:
        template_str = (
            '<div class="d-flex align-items-center">'
            '<span class="me-2 avatar avatar-xs"'
            "{% if obj.avatar_color %}"
            ' style="background-color: {{obj.avatar_color}};'
            ' --tblr-avatar-size: 1.5rem;"'
            "{% else %}"
            ' style="--tblr-avatar-size: 1.5rem;"'
            "{% endif %}"
            ">{{obj.full_name[:2]}}</span>"
            "{{obj.full_name}}"
            "</div>"
        )
        return Template(template_str, autoescape=True).render(obj=self)


class Category(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2, index=True)
    description: str | None = Field(sa_column=Column(Text, nullable=True), default=None)

    articles: list["Article"] = Relationship(back_populates="category")

    async def __admin_repr__(self, request) -> str:
        return self.name

    async def __admin_select2_repr__(self, _request: Request) -> str:
        return f"<span>{escape(self.name)}</span>"


class Article(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    title: str = Field(min_length=3, index=True)
    content: str = Field(sa_column=Column(Text))
    tags: list[str] = Field(sa_column=Column(JSON))
    status: ArticleStatus = Field(
        sa_column=Column(
            SAEnum(ArticleStatus), default=ArticleStatus.DRAFT, nullable=False
        )
    )
    views: int = Field(default=0)
    published_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True), default=None
    )
    created_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True), default=None
    )
    updated_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True), default=None
    )

    author_id: int | None = Field(foreign_key="author.id", default=None)
    author: Optional["Author"] = Relationship(back_populates="articles")

    category_id: int | None = Field(foreign_key="category.id", default=None)
    category: Optional["Category"] = Relationship(back_populates="articles")

    comments: list["Comment"] = Relationship(back_populates="article")

    async def __admin_repr__(self, request) -> str:
        return self.title

    async def __admin_select2_repr__(self, _request: Request) -> str:
        return f"<span>{escape(self.title)}</span>"


class Comment(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    author_name: str = Field(min_length=2)
    email: str | None = Field(
        sa_column=Column(String(200), nullable=True), default=None
    )
    body: str = Field(sa_column=Column(Text), min_length=5)
    approved: bool = Field(default=False)
    created_at: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True), default=None
    )

    article_id: int | None = Field(foreign_key="article.id", default=None)
    article: Optional["Article"] = Relationship(back_populates="comments")

    async def __admin_repr__(self, request) -> str:
        return f"{self.author_name}: {self.body[:50]}"

    async def __admin_select2_repr__(self, _request: Request) -> str:
        return f"<span>{escape(f'{self.author_name}: {self.body[:50]}')}</span>"
