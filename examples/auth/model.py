import datetime
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text

from . import Base


class Status(str, enum.Enum):
    Draft = "d"
    Published = "p"
    Withdrawn = "w"


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    enligne = Column(Boolean, default=False)
    body = Column(Text, nullable=False)
    status = Column(Enum(Status))
    created_at = Column(DateTime, default=datetime.datetime.now)
