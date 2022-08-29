import mongoengine
from mongoengine import connect

connect("example")


class Post(mongoengine.Document):
    title = mongoengine.StringField()
    content = mongoengine.StringField()
    tags = mongoengine.ListField(mongoengine.StringField())
