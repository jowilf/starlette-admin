"""Class map for the {{ cookiecutter.theme_name }} theme.

Core templates render class attributes through `cls('role.name')`. This map
overrides the roles this theme restyles; any role left unmapped falls through
to the Tabler defaults in `CoreClasses`, so a partial map is always safe.

The role vocabulary lives in `starlette_admin.theme.CoreClasses`. A button
role owns the element's whole class attribute (variant, size, and spacing
included), so mapping it replaces the button's look wholesale.
"""

from __future__ import annotations

from starlette_admin.theme import ClassMap


class {{ cookiecutter.class_prefix }}Classes(ClassMap):
    """Overrides for the component roles this theme restyles."""

    classes = {
        # "form.save_button": "btn btn-success",
        # "list.create_button": "btn btn-outline-primary ms-2",
        # "filter.chip": "badge rounded-pill bg-primary-subtle",
    }
