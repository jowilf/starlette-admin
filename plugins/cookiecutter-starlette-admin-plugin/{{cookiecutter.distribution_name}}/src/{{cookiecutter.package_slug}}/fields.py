"""Example field: `{{ cookiecutter.class_prefix }}SliderField`.

Renders an integer as a range slider with a live value label. This field is kept dependency-free (plain CSS/JS, no vendored library) so it can serve as a minimal template for a real field. It demonstrates dataclass attributes, namespaced templates, the `additional_css_links`/`additional_js_links` + `_needs_form_assets` pattern, and a JS initializer registered through `StarletteAdmin.registerFieldInitializer`.

Delete this module, along with its templates and static counterparts, if this plugin does not ship a field.
"""

from __future__ import annotations

from dataclasses import dataclass

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette_admin.fields import BaseField
from starlette_admin.helpers import static_url

_VERSION = "1"


@dataclass
class {{ cookiecutter.class_prefix }}SliderField(BaseField):
    """An integer rendered as a range slider with a live value label."""

    min_value: int = 0
    max_value: int = 100
    step: int = 1
    suffix: str = "%"
    list_template: str = "plugins/{{ cookiecutter.plugin_slug }}/fields/list/slider.html"
    detail_template: str = "plugins/{{ cookiecutter.plugin_slug }}/fields/detail/slider.html"
    form_template: str = "plugins/{{ cookiecutter.plugin_slug }}/fields/form/slider.html"

    async def parse_form_data(self, request: Request, form_data: FormData) -> int:
        raw = form_data.get(self.id)
        return int(raw) if raw else self.min_value

    def additional_css_links(self, request: Request) -> list[str]:
        return [
            static_url(
                request,
                "plugins/{{ cookiecutter.plugin_slug }}/css/slider.css",
                v=_VERSION,
            )
        ]

    def additional_js_links(self, request: Request) -> list[str]:
        if self._needs_form_assets(request):
            return [
                static_url(
                    request,
                    "plugins/{{ cookiecutter.plugin_slug }}/js/slider.js",
                    v=_VERSION,
                )
            ]
        return []
