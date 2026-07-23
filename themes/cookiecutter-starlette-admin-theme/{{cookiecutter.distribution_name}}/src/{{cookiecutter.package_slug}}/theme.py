"""`{{ cookiecutter.class_prefix }}Theme`: the active theme passed to `Admin(theme=...)`.

A theme owns the admin layout and styling. Its surface is intentionally small:
replacement templates at bare paths, an `IconSet`, and template globals. Exactly
one theme is active per `Admin` instance. See the theme module docstring in
starlette-admin for the full contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from starlette_admin.theme import BaseTheme, IconSet, TablerSettings

from .icons import {{ cookiecutter.class_prefix }}Icons


@dataclass(frozen=True)
class {{ cookiecutter.class_prefix }}Config:
    """Options accepted by `{{ cookiecutter.class_prefix }}Theme(**options)`.

    Add fields here for anything an end user should be able to configure. Every
    option is exposed to templates via the `theme_config` global.
    """

    example_option: str = "default value"


class {{ cookiecutter.class_prefix }}Theme(BaseTheme):
    """starlette-admin theme: {{ cookiecutter.description }}."""

    name = "{{ cookiecutter.theme_slug }}"

    # Import package holding this theme's templates/ and static/ folders.
    package = "{{ cookiecutter.package_slug }}"

    def __init__(self, **options: Any) -> None:
        self.config = {{ cookiecutter.class_prefix }}Config(**options)
        # Re-exposed so the extended @core/base.html still renders its
        # data-bs-theme attributes. Replace with your own palette if needed.
        self.settings = TablerSettings()

    def get_icon_set(self) -> IconSet:
        return {{ cookiecutter.class_prefix }}Icons()

    def template_globals(self) -> dict[str, Any]:
        # Theme globals are exposed unprefixed (unlike plugin globals).
        return {"theme_config": self.config, "theme_settings": self.settings}
