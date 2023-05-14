import pytest
from pydantic import BaseModel, ValidationError
from starlette_admin.contrib.beanie._telephone import Telephone


class Model(BaseModel):
    phone: Telephone


def test_schema_class():
    with pytest.raises(ValidationError):
        Model()

    assert Model.schema() == {
        "title": "Model",
        "type": "object",
        "properties": {
            "phone": {
                "title": "Phone",
                "type": "string",
                "examples": ["+541165661234"],
            },
        },
        "required": ["phone"],
    }


def test_json_encode():
    phone = Telephone(country_code=54, national_number=1149681234).json_encode()
    assert type(phone) == str
    assert phone == "+541149681234"


def test_telephone_success():
    phone = Telephone(country_code=54, national_number=1149681234)
    Model(phone=phone)


def test_telephone_str_null_success():
    Model(phone="")


def test_telephone_few_fail():
    with pytest.raises(ValidationError):
        Model(phone="+120012301")


def test_telephone_fails():
    with pytest.raises(ValidationError):
        Model(phone="541165661234a")


def test_telephone_str_success():
    Model(phone="+541165661234")
