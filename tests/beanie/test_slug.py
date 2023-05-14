import pytest
from pydantic import BaseModel, ValidationError
from starlette_admin.contrib.beanie._slug import Slug


class Model(BaseModel):
    name_slug: Slug


def test_schema_class():
    with pytest.raises(ValidationError):
        Model()

    assert Model.schema() == {
        "title": "Model",
        "type": "object",
        "properties": {
            "name_slug": {
                "title": "Name Slug",
                "type": "string",
                "format": "string",
                "examples": "this-is-a-slug",
            },
        },
        "required": ["name_slug"],
    }


def test_slug_type_fails():
    with pytest.raises(ValidationError):
        Model(name_slug=123)


def test_slug_repr():
    m = Model(name_slug="hello world")
    assert repr(m.name_slug) == "Slug('hello-world')"
