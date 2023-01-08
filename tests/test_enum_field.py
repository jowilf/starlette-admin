import enum

import pytest
from starlette_admin import EnumField


def test_invalid_enum_field():
    with pytest.raises(
        ValueError,
        match="EnumField required a list of choices, enum class or a choices_loader for dynamic choices",
    ):
        EnumField("myenum")


def test_deprecated_from_enum_method():
    class Status(str, enum.Enum):
        good = "good"
        bad = "bad"

    with pytest.warns(
        DeprecationWarning,
        match="This method is deprecated.",
    ):
        assert EnumField.from_enum("myenum", enum_type=Status) == EnumField(
            "myenum", enum=Status
        )


def test_deprecated_from_choices_method():

    with pytest.warns(
        DeprecationWarning,
        match="This method is deprecated.",
    ):
        assert EnumField.from_choices(
            "myenum", choices=[("cpp", "C++"), ("py", "Python")]
        ) == EnumField("myenum", choices=[("cpp", "C++"), ("py", "Python")])
