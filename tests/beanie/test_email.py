import pytest
from pydantic import BaseModel, Field, ValidationError
from starlette_admin.contrib.beanie._email import Email


def test_schema_class():
    class Model(BaseModel):
        foo: Email = Field(..., title="email field")

    with pytest.raises(ValidationError):
        Model()

    assert Model.schema() == {
        "title": "Model",
        "type": "object",
        "properties": {
            "foo": {
                "title": "email field",
                "type": "string",
                "format": "string",
                "examples": "user@domain.com",
            },
        },
        "required": ["foo"],
    }


def test_email_format_fails():
    class Model(BaseModel):
        email: Email

    # Expect test to fail because email has not '@'
    with pytest.raises(ValidationError):
        Model(email="admingmail.com")


def test_email_type_fails():
    class Model(BaseModel):
        email: Email

    # Expect test to fail because email has not '@'
    with pytest.raises(ValidationError):
        Model(email=123)


def test_email_len_success():
    class Model(BaseModel):
        email: Email

    # Expect test success email empty
    Model(email="")


def test_email_repr():
    class Model(BaseModel):
        email: Email

    m = Model(email="admin@domain.com")
    assert repr(m.email) == "Email('admin@domain.com')"
