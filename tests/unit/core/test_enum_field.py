from pathlib import Path
from unittest.mock import MagicMock

import pytest
import starlette_admin
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette_admin import EnumField

TEMPLATES_DIR = Path(starlette_admin.__file__).parent / "templates"


@pytest.fixture(scope="module")
def templates_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )


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


def test_enum_field_template_paths() -> None:
    field = EnumField("status", choices=[("a", "A"), ("b", "B")], multiple=True)
    assert field.list_template == "fields/list/enum.html"
    assert field.detail_template == "fields/detail/enum.html"
    assert field.form_template == "fields/form/enum.html"


def test_enum_field_multiple_renders_bullet_list_in_list_view(
    templates_env: Environment,
) -> None:
    template = templates_env.get_template("fields/list/enum.html")
    field = EnumField(
        "permissions",
        choices=[("a", "Alpha"), ("b", "Beta")],
        multiple=True,
    )
    html = template.render(field=field, data=["Alpha", "Beta"], request=MagicMock())

    assert "<ul" in html
    assert "<li>Alpha</li>" in html
    assert "<li>Beta</li>" in html
    assert "['Alpha', 'Beta']" not in html
    assert '["Alpha", "Beta"]' not in html


def test_enum_field_multiple_empty_list_renders_nothing(
    templates_env: Environment,
) -> None:
    template = templates_env.get_template("fields/list/enum.html")
    field = EnumField(
        "permissions",
        choices=[("a", "Alpha")],
        multiple=True,
    )
    html = template.render(field=field, data=[], request=MagicMock())

    assert "<ul" not in html
    assert "[]" not in html


def test_enum_field_single_value_delegates_to_text_template(
    templates_env: Environment,
) -> None:
    template = templates_env.get_template("fields/list/enum.html")
    field = EnumField("status", choices=[("a", "Alpha")], multiple=False)
    html = template.render(field=field, data="Alpha", request=MagicMock())

    assert "<ul" not in html
    assert "Alpha" in html


def test_enum_field_multiple_renders_bullet_list_in_detail_view(
    templates_env: Environment,
) -> None:
    template = templates_env.get_template("fields/detail/enum.html")
    field = EnumField(
        "permissions",
        choices=[("a", "Alpha"), ("b", "Beta")],
        multiple=True,
    )
    html = template.render(field=field, data=["Alpha", "Beta"], request=MagicMock())

    assert "<ul" in html
    assert "<li>Alpha</li>" in html
    assert "<li>Beta</li>" in html
    assert "['Alpha', 'Beta']" not in html


def test_enum_field_detail_empty_list_uses_empty_partial(
    templates_env: Environment,
) -> None:
    template = templates_env.get_template("fields/detail/enum.html")
    field = EnumField(
        "permissions",
        choices=[("a", "Alpha")],
        multiple=True,
    )
    html = template.render(field=field, data=[], request=MagicMock())

    assert "<ul" not in html
    assert "[]" not in html
