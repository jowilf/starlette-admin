# Dosya Yönetimi

*Starlette-Admin* hali hazırda [SQLAlchemy-file](https://github.com/jowilf/sqlalchemy-file) ve Gridfs aracılığıyla `MongoEngine` `FileField` ve `ImageField` desteği sunmaktadır.

## SQLAlchemy & SQLModel

Yapmanız gereken tek şey [SQLAlchemy-file](https://github.com/jowilf/sqlalchemy-file)'dan `ImageField` veya `FileField`'ı modelinize eklemek.

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


class BookView(ModelView):
    pass

admin.add_view(BookView(Book))
```

!!! note "Not"
    Ayrıca `multiple=True` kullanarak birden fazla dosya kaydedebilirsiniz.

## MongoEngine

*Starlette-Admin* `ImageField` ve `FileField` desteğine sahiptir.

```python
from mongoengine import Document, FileField, ImageField, StringField
from starlette_admin.contrib.mongoengine import ModelView


class Book(Document):
    title = StringField(max_length=50)
    cover = ImageField(thumbnail_size=(128, 128))
    content = FileField()


class BookView(ModelView):
    pass

admin.add_view(BookView(Book))
```
