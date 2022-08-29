from mongoengine import Document, FileField, ImageField, StringField
from starlette_admin.contrib.mongoengine import ModelView


class Book(Document):
    title = StringField(max_length=50)
    cover = ImageField(thumbnail_size=(128, 128))
    content = FileField()


class BookView(ModelView, document=Book):
    pass
