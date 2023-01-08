import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import AnyHttpUrl, BaseModel, EmailStr
from pydantic import Field as PydField
from pydantic.color import Color
from sqlalchemy import JSON, Column, DateTime, Enum, String, Text

from sqlmodel import Field, Relationship, SQLModel


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class User(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    full_name: str = Field(min_length=3, index=True)
    sex: Optional[str] = Field(
        sa_column=Column(Enum(Gender)), default=Gender.UNKNOWN, index=True
    )

    posts: List["Post"] = Relationship(back_populates="publisher")
    comments: List["Comment"] = Relationship(back_populates="user")


class Post(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    title: str = Field(min_length=3)
    content: str = Field(sa_column=Column(Text))
    tags: List[str] = Field(sa_column=Column(JSON), min_items=1)
    published_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), default=datetime.utcnow)
    )

    publisher_id: Optional[int] = Field(foreign_key="user.id")
    publisher: User = Relationship(back_populates="posts")

    comments: List["Comment"] = Relationship(back_populates="post")


class Comment(SQLModel, table=True):
    pk: Optional[int] = Field(primary_key=True)
    content: str = Field(sa_column=Column(Text), min_length=5)
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=True), default=datetime.utcnow)
    )

    post_id: Optional[int] = Field(foreign_key="post.id")
    post: Post = Relationship(back_populates="comments")

    user_id: Optional[int] = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="comments")


class Config(BaseModel):
    key: str = PydField(min_length=3)
    value: int = PydField(multiple_of=5)


class Dump(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    email: EmailStr = Field(index=True)
    color: Color = Field(sa_column=Column(String(10)))
    url: AnyHttpUrl
    json_field: Dict[str, Any] = Field(sa_column=Column(JSON))
    configs: List[Config] = Field(sa_column=Column(JSON))
