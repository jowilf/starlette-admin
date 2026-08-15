from unittest.mock import MagicMock

from starlette.requests import Request
from starlette_admin.theme import BaseTheme, IconSet


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
