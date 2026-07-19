import mongoengine as me
from starlette_admin.contrib.mongoengine.view import ModelView
from starlette_admin.fields import UUIDField


class UUIDDocument(me.Document):
    uuid_scalar = me.UUIDField()


def test_conv_uuid_field():
    view = ModelView(UUIDDocument)
    field = next(f for f in view.fields if f.name == "uuid_scalar")
    assert isinstance(field, UUIDField)
