import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Unicode,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    last_name = Column(String(100))
    first_name = Column(String(100))
    # use a regular string field, for which we can specify a list of available choices later on
    # >>> EnumField("type", choices=AVAILABLE_USER_TYPES, select2=False)
    type = Column(String(50))

    posts = relationship("Post", back_populates="publisher")


post_tags_table = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("post.id")),
    Column("tag_pk", Unicode(50), ForeignKey("tag.name")),
)


class Status(str, enum.Enum):
    PENDING = "pending"
    REJECTED = "rejected"
    APPROVED = "approved"


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    text = Column(Text, nullable=False)
    date = Column(Date, default=datetime.today)
    status = Column(Enum(Status), default=Status.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_public = Column(Boolean, default=True, nullable=False)

    publisher_id = Column(Integer, ForeignKey(User.id))
    publisher = relationship(User, back_populates="posts")

    tags = relationship("Tag", secondary=post_tags_table)


class Tag(Base):
    __tablename__ = "tag"

    name = Column(Unicode(50), unique=True, primary_key=True)


class Tree(Base):
    __tablename__ = "tree"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    # recursive relationship
    parent_id = Column(Integer, ForeignKey("tree.id"))
    parent = relationship("Tree", remote_side=[id], backref="childrens")
