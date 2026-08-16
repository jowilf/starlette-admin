from unittest.mock import MagicMock

import pytest
from starlette_admin import EnumField


def test_invalid_enum_field():
    with pytest.raises(
        ValueError,
        match="EnumField required a list of choices, enum class or a choices_loader for dynamic choices",
    ):
        EnumField("myenum")


@pytest.mark.asyncio
async def test_enum_field_parse_form_data_multiple():
    field = EnumField("status", choices=[("a", "A"), ("b", "B")], multiple=True)
    form = MagicMock(**{"getlist.return_value": ["a", "b"]})
    result = await field.parse_form_data(MagicMock(), form)
    assert result == ["a", "b"]


@pytest.mark.asyncio
async def test_enum_field_get_create_default_multiple_list():
    """`get_create_default` coerces each item when `multiple=True` and the default is a list."""
    field = EnumField(
        "status",
        choices=[("a", "A"), ("b", "B")],
        multiple=True,
        default=["a", "b"],
    )
    result = await field.get_create_default(MagicMock())
    assert result == ["a", "b"]


@pytest.mark.asyncio
async def test_enum_field_get_create_default_none():
    """`get_create_default` returns `None` when no default is set."""
    field = EnumField("status", choices=[("a", "A"), ("b", "B")])
    result = await field.get_create_default(MagicMock())
    assert result is None
