"""`GeospatialPlugin`: the entry point end users list in
`Admin(plugins=[...])`. See the README for the full extension surface this
builds on (templates, static assets, `setup()` registries, hooks).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from starlette.requests import Request
from starlette_admin.plugins import BasePlugin

if TYPE_CHECKING:
    from starlette_admin.base import BaseAdmin


@dataclass(frozen=True)
class GeospatialConfig:
    """Options accepted by `GeospatialPlugin(**options)`.

    Add fields here for anything an end user should be able to configure;
    every option flows to Python via `self.config` in `setup()`, to Jinja
    via the auto-prefixed `geospatial_config`
    template global, and to JS as `data-*` attributes on field templates.
    """

    example_option: str = "default value"


class GeospatialPlugin(BasePlugin):
    """starlette-admin plugin: A starlette-admin plugin."""

    # Doubles as the templates/static namespace: everything this plugin
    # ships lives under "plugins/geospatial/".
    name = "geospatial"

    def __init__(self, **options: Any) -> None:
        self.config = GeospatialConfig(**options)

    def css_links(self, request: Request) -> list[str]:
        """Stylesheets injected into every admin page. Leave empty and rely
        on per-field `additional_css_links()` unless this plugin needs a
        page-wide asset (a theme, a global widget)."""
        return []

    def js_links(self, request: Request) -> list[str]:
        return []

    def template_globals(self) -> dict[str, Any]:
        # Registration auto-prefixes this key with the plugin name, so
        # templates read it as "geospatial_config".
        return {"config": self.config}

    def setup(self, admin: BaseAdmin) -> None:
        """Wire this plugin into existing starlette-admin registries:
        storage backends (`register_storage`), model converters
        (`register_converter` per contrib backend), filters
        (`register_filters`), import/export formats, or event subscribers
        (`admin.events.subscribe(...)`). Empty by default; delete this
        override if the plugin has nothing to register.
        """
