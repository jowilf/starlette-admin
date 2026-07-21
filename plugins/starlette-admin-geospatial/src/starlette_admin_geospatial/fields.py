"""Example field: `GeospatialRatingField`.

Renders an integer 1-5 as a row of clickable stars. Kept dependency-free
(plain CSS/JS, no vendored library) so it doubles as the minimal template
for a real field: dataclass attributes, namespaced templates, the
`additional_css_links`/`additional_js_links` + `_needs_form_assets` pattern,
and a JS initializer registered through `StarletteAdmin.registerFieldInitializer`.

Delete this module (and its templates/static counterparts) if this plugin
does not ship a field.
"""

from __future__ import annotations

from dataclasses import dataclass

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette_admin.fields import BaseField
from starlette_admin.helpers import static_url

_VERSION = "1"


@dataclass
class GeospatialRatingField(BaseField):
    """An integer rating (1-`max_stars`) rendered as clickable stars."""

    max_stars: int = 5
    list_template: str = "plugins/geospatial/fields/list/rating.html"
    detail_template: str = "plugins/geospatial/fields/detail/rating.html"
    form_template: str = "plugins/geospatial/fields/form/rating.html"

    async def parse_form_data(self, request: Request, form_data: FormData) -> int:
        raw = form_data.get(self.id)
        return int(raw) if raw else 0

    def additional_css_links(self, request: Request) -> list[str]:
        return [
            static_url(
                request,
                "plugins/geospatial/css/rating.css",
                v=_VERSION,
            )
        ]

    def additional_js_links(self, request: Request) -> list[str]:
        if self._needs_form_assets(request):
            return [
                static_url(
                    request,
                    "plugins/geospatial/js/rating.js",
                    v=_VERSION,
                )
            ]
        return []
