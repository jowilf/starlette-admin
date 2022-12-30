import datetime
import enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    Time,
)

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
    date_ = Column(Date, default=datetime.datetime.now)
    time_ = Column(Time, default=datetime.time)
    created_at = Column(DateTime, default=datetime.datetime.now)
