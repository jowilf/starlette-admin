from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy_file import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView

Base = declarative_base()


class Book(Base):
    __tablename__ = "book"

    id = Column(Integer, autoincrement=True, primary_key=True)
    title = Column(String(50), unique=True)
    cover = Column(ImageField(thumbnail_size=(128, 128)))
    content = Column(FileField)


class BookView(ModelView, model=Book):
    pass
