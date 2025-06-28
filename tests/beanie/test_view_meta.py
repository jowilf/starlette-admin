from beanie import Document
from starlette_admin.contrib.beanie.view import ModelView
from starlette_admin.fields import StringField, TagsField


def test_fields_customisation():
    class MyModel(Document):
        tags: list[str]
        name: str

    class MyModelView(ModelView):
        fields = ["id", "name", TagsField("tags")]
        exclude_fields_from_create = ["tags"]
        exclude_fields_from_detail = ["id"]
        exclude_fields_from_edit = ["name"]

    assert MyModelView(MyModel).fields == [
        StringField(
            "id",
            label="id",
            exclude_from_create=True,
            exclude_from_edit=True,
            exclude_from_detail=True,
        ),
        StringField("name", exclude_from_edit=True, required=True),
        TagsField("tags", exclude_from_create=True),
    ]
