import pytest
from pydantic import BaseModel, ValidationError
from starlette_admin.contrib.beanie._my_json import MyJson


def test_schema_class():
    class Model(BaseModel):
        meta: MyJson

    with pytest.raises(ValidationError):
        Model()

    assert Model.schema() == {
        "title": "Model",
        "type": "object",
        "properties": {
            "meta": {
                "title": "Meta",
                "type": "string",
                "format": "json-string",
                "examples": '{"key": 10}',
            },
        },
        "required": ["meta"],
    }


def test_json_type_fails():
    class Model(BaseModel):
        meta: MyJson

    # Expect test to fail because is not str or dict
    with pytest.raises(ValidationError):
        Model(meta=123)


def test_json_str_fails():
    class Model(BaseModel):
        meta: MyJson

    with pytest.raises(ValidationError):
        Model(meta="name:Oscar, lastname")


def test_json_str_null_success():
    class Model(BaseModel):
        meta: MyJson

    Model(meta="")


def test_json_str_to_dict_fails():
    class Model(BaseModel):
        meta: MyJson

    with pytest.raises(ValidationError):
        Model(meta='"\\"foo\\bar"')


# pass a Dict
def test_json_dict_success():
    class Model(BaseModel):
        meta: MyJson

    meta = {}
    Model(meta=meta)


def test_json_repr():
    class Model(BaseModel):
        meta: MyJson

    meta = MyJson({"name": "Oscar"})
    m = Model(meta=meta)
    assert repr(m.meta) == "MyJson(\"{'name': 'Oscar'}\")"
