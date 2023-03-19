import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy_utils import (
    EmailType,
    IPAddressType,
    URLType,
    UUIDType,
)

Base = declarative_base()


class User(Base):
    __tablename__ = "model"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUIDType(binary=False), default=uuid.uuid4)
    full_name = Column(String(100))
    website = Column(URLType)
    email = Column(EmailType)
    ip_address = Column(IPAddressType)


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True)
    title = Column(String(120))
    text = Column(Text, nullable=False)
    date = Column(DateTime)

    user_id = Column(Integer(), ForeignKey(User.id))
    user = relationship(User, backref="posts")
