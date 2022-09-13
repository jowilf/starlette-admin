from sqlalchemy import JSON, Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    tags = Column(JSON)


Base.metadata.create_all(engine)
