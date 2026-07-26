"""Tabler Icons mapping for the {{ cookiecutter.theme_name }} theme.

Swaps the default FontAwesome (`CoreIcons`) for [Tabler Icons](https://tabler.io/icons).
Every semantic key the core templates reference is mapped here, because icon
resolution falls back to the raw key name (rendered as a broken class) when a
key is missing.
"""

from __future__ import annotations

from starlette.requests import Request
from starlette_admin.theme import IconSet

_TABLER_ICONS_CSS = (
    "https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3/dist/tabler-icons.min.css"
)


class {{ cookiecutter.class_prefix }}Icons(IconSet):
    """Maps the core icon vocabulary to Tabler Icons classes."""

    icons = {
        # List page toolbar
        "list.new": "ti ti-plus",
        "list.search": "ti ti-search",
        "list.filter": "ti ti-filter",
        "list.columns": "ti ti-columns",
        "list.import": "ti ti-file-import",
        "list.export": "ti ti-file-export",
        "list.row_actions": "ti ti-dots-vertical",
        # Default row/detail actions
        "default_actions.view": "ti ti-eye",
        "default_actions.edit": "ti ti-edit",
        "default_actions.delete": "ti ti-trash",
        # Pagination
        "pagination.prev": "ti ti-chevron-left",
        "pagination.next": "ti ti-chevron-right",
        # Column sorting
        "sort.none": "ti ti-arrows-sort",
        "sort.asc": "ti ti-sort-ascending",
        "sort.desc": "ti ti-sort-descending",
        # Auth / global nav
        "auth.logout": "ti ti-logout",
        "nav.language": "ti ti-language",
        "nav.world": "ti ti-world",
        "nav.user": "ti ti-user",
        # Flash messages
        "flash.success": "ti ti-circle-check",
        "flash.warning": "ti ti-alert-triangle",
        "flash.error": "ti ti-alert-circle",
        "flash.info": "ti ti-info-circle",
        # Generic actions
        "action.close": "ti ti-x",
        "action.copy": "ti ti-copy",
        "action.copy_done": "ti ti-check",
        # Fields
        "field.file": "ti ti-file",
        "field.boolean_true": "ti ti-circle-check",
        "field.boolean_false": "ti ti-circle-x",
        "list_field.add": "ti ti-plus",
        # Inline forms
        "inline.add_row": "ti ti-plus",
        "inline.delete_row": "ti ti-trash",
        # Inline cell editing (list page popover)
        "inline_edit.save": "ti ti-check",
        "inline_edit.cancel": "ti ti-x",
        # Collapsible panels (inline formsets, panel widget)
        "panel.collapse_toggle": "ti ti-chevron-down",
        # Filter bar / builder
        "filter.remove_chip": "ti ti-x",
        "filter_builder.add_condition": "ti ti-plus",
        "filter_builder.add_group": "ti ti-layers",
        "filter_builder.remove": "ti ti-trash",
        # Import modal
        "import.preview": "ti ti-eye",
        # Create/edit form footer
        "form.cancel": "ti ti-x",
        "form.save": "ti ti-arrow-right",
    }

    def css_links(self, request: Request) -> list[str]:
        return [_TABLER_ICONS_CSS]
