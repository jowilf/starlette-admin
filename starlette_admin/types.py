from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

from starlette.requests import Request
from starlette_admin.filters.base import FilterGroup


class RequestAction(StrEnum):
    """The kind of request being handled for a `BaseModelView`.

    Set on `request.state.action` before dispatching to a view method, so
    field/filter code can branch on which page or endpoint is rendering.

    Attributes:
        RELATION_LOOKUP: Select2 lookup request, populating a relation field's dropdown.
        LIST: List page request.
        DETAIL: Detail page request for a single object.
        CREATE: Form request for creating a new object (GET or POST).
        EDIT: Form request for editing an existing object (GET or POST).
        INLINE_EDIT: Single-field edit from the list page's inline-edit
            popover (GET renders the field's form fragment, POST saves it).
        ACTION: Bulk action request applied to a set of selected rows.
        ROW_ACTION: Action request applied to a single row.
        EXPORT: Export request (CSV, Excel, JSON, PDF).
        IMPORT: Import request (CSV, Excel, JSON, optionally bundled in a ZIP).
    """

    RELATION_LOOKUP = "RELATION_LOOKUP"
    LIST = "LIST"
    DETAIL = "DETAIL"
    CREATE = "CREATE"
    EDIT = "EDIT"
    INLINE_EDIT = "INLINE_EDIT"
    ACTION = "ACTION"
    ROW_ACTION = "ROW_ACTION"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"

    def is_form(self) -> bool:
        return self.value in [self.CREATE, self.EDIT, self.INLINE_EDIT]


Getter = Callable[[Request, Any], "Any | Awaitable[Any]"]
"""`(request, obj) -> value`, sync or async. Overrides `BaseField.parse_obj`'s
default `getattr(obj, self.name, None)` lookup."""

Formatter = Callable[[Request, Any], "Any | Awaitable[Any]"]
"""`(request, value) -> formatted_value`, sync or async. Replaces
`serialize_value` / `serialize_none_value` entirely for the value parsed by
`parse_obj`/`getter`; its return value is used as the final output."""

Parser = Callable[[Request, Any], "Any | Awaitable[Any]"]
"""`(request, raw) -> value`, sync or async. Maps a `RequestAction` to a
callable that replaces this field's default parsing for that action. `raw` is
`form_data.get(self.id)` (or `getlist` when the field is `multiple`) for
CREATE, EDIT, INLINE_EDIT, or the unprocessed cell value read from the import
file for IMPORT. See `BaseField.parse_input`."""


class RowActionsDisplayType(StrEnum):
    """How row actions are rendered in the list page's row-actions column.

    Attributes:
        ICON_LIST: One icon-only link per action, laid out side by side.
        DROPDOWN: A single "Actions" button that opens a dropdown menu.
        KEBAB: A kebab (vertical ellipsis) icon button that opens a dropdown menu.
        INLINE_LINKS: Text links separated by a middle-dot, laid out side by side.
    """

    ICON_LIST = "ICON_LIST"
    DROPDOWN = "DROPDOWN"
    KEBAB = "KEBAB"
    INLINE_LINKS = "INLINE_LINKS"


class RowActionsPosition(StrEnum):
    """Where the row-actions column sits relative to the data columns in the list table.

    Attributes:
        BEFORE_COLUMNS: Row-actions column renders first, before the data columns.
        AFTER_COLUMNS: Row-actions column renders last, after the data columns.
    """

    BEFORE_COLUMNS = "BEFORE_COLUMNS"
    AFTER_COLUMNS = "AFTER_COLUMNS"


@dataclass
class ListParams:
    """Parsed & sanitised query parameters for the list page.

    All list state lives in the URL (page, page size, sort, search, ...).
    `BaseModelView._parse_list_params` builds this from the request's query
    string, falling back to the view's defaults for missing/invalid values.

    Attributes:
        page: Current page number (1-indexed).
        page_size: Number of items per page. `-1` means "show all".
        sorts: Active sort columns as ``[(field_name, direction), ...]`` where
            direction is ``"asc"`` or ``"desc"``.  Encoded in the URL as
            repeated ``sort=field__dir`` params, e.g.
            ``?sort=name__asc&sort=date__desc``.  An empty list means the
            view's default sort applies.
        q: Full-text search term, or `None`.
        filters: Parsed & validated filter tree from the `filter` query param.
            An empty [FilterGroup][starlette_admin.filters.FilterGroup] (the
            default) applies no filtering.
        visible_cols: Names of visible columns from the `cols` query param.
            `None` means all columns are visible (param absent).
    """

    page: int = 1
    page_size: int = 25
    sorts: list[tuple[str, Literal["asc", "desc"]]] = field(default_factory=list)
    q: str | None = None
    filters: FilterGroup = field(default_factory=FilterGroup)
    visible_cols: list[str] | None = None


@dataclass
class FilterChip:
    """A single active-filter pill, as rendered by `_filter_bar.html`.

    Built by `BaseModelView._active_filter_chips` from the raw `filter` query
    param so that `remove_url` carries the *original* (string) values straight
    through to the URL. Re-serialising the parsed/validated `FilterRule`
    values would require an `apply()`-style inverse for every filter (e.g.
    `date` to ISO string) that doesn't otherwise need to exist.

    Attributes:
        label: Human-readable description of the filter, eg.
            `"Title: Contains john"`.
        remove_url: List URL with this filter (and only this filter) removed
            from the `filter` query param, every other list-state param
            (sort, page, search, ...) preserved.
    """

    label: str
    remove_url: str
