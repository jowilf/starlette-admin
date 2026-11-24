from typing import get_args
from unittest.mock import MagicMock

from starlette.requests import Request
from starlette_admin.theme import BaseTheme, IconSet, TablerBase, TablerSettings


def test_icon_set_css_links_default_is_empty():
    assert IconSet().css_links(MagicMock(spec=Request)) == []


def test_base_theme_template_globals_default_is_empty():
    class Theme(BaseTheme):
        def get_icon_set(self) -> IconSet:
            return IconSet()

    assert Theme().template_globals() == {}


def test_base_theme_resolved_package_falls_back_to_top_level_package():
    class Theme(BaseTheme):
        def get_icon_set(self) -> IconSet:
            return IconSet()

    # `package` unset: resolves to the theme class's top-level import package.
    assert Theme().resolved_package() == "tests"


def test_tabler_settings_sidebar_html_attrs():
    assert "data-bs-sidebar" not in TablerSettings().html_attrs()
    assert TablerSettings(sidebar="folded").html_attrs()["data-bs-sidebar"] == "folded"
    assert (
        TablerSettings(sidebar="folded-hover").html_attrs()["data-bs-sidebar"]
        == "folded-hover"
    )


def test_tabler_settings_base_values():
    assert set(get_args(TablerBase)) == {
        "slate",
        "gray",
        "zinc",
        "neutral",
        "stone",
        "mist",
    }
    assert TablerSettings(base="mist").html_attrs()["data-bs-theme-base"] == "mist"
