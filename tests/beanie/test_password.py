import pytest
from pydantic import BaseModel, ValidationError
from starlette_admin.contrib.beanie._password import (
    Password,
    generate_password,
    hash_password,
    is_hash,
    verify_password,
)


def test_generate_password():
    passwd = generate_password()
    assert type(passwd) == str
    assert len(passwd) > 0


def test_hash_password():
    s = "1234567890"
    passwd = hash_password(s)
    assert type(passwd) == str
    assert len(passwd) == 200
    assert passwd.startswith("__hash__")
    assert is_hash(passwd) is True
    assert verify_password(passwd, s) is True


def test_schema_class():
    class Model(BaseModel):
        password: Password

    with pytest.raises(ValidationError):
        Model()

    assert Model.schema() == {
        "title": "Model",
        "type": "object",
        "properties": {
            "password": {
                "title": "Password",
                "type": "string",
                "format": "password",
                "examples": "x?1_P-1M.4!eM",
                "writeOnly": True,
            },
        },
        "required": ["password"],
    }


def test_password_success():
    class Model(BaseModel):
        password: Password

    Model(password="1234567890#$")


def test_hashed_password_success():
    class Model(BaseModel):
        password: Password

    m1 = Model(password=Password("1234567890#$"))
    Model(password=m1.password)
