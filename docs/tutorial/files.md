# Handling files

With *Starlette-Admin* you can attach files directly to your model.

## SQLAlchemy

*Starlette-Admin* supports [SQLAlchemy-file](https://github.com/jowilf/sqlalchemy-file) by default for 
files handling. All you need is to add ImageField or FileField to your model

```python
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

admin.add_view(BookView)
```
!!! note
    You can also use `multiple=True` to save multiple files.


## MongoEngine

*Starlette-Admin* support ImageField and FileField

```python
from mongoengine import Document, FileField, ImageField, StringField
from starlette_admin.contrib.mongoengine import ModelView


class Book(Document):
    title = StringField(max_length=50)
    cover = ImageField(thumbnail_size=(128, 128))
    content = FileField()


class BookView(ModelView, document=Book):
    pass

admin.add_view(BookView)

```
