import inspect
from abc import abstractmethod
from collections import OrderedDict, deque
from collections.abc import (
    Awaitable,
    Callable,
    Collection,
    Iterator,
    Mapping,
    Sequence,
)
from dataclasses import replace as dc_replace
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Optional,
    Union,
    cast,
)

if TYPE_CHECKING:
    from starlette_admin.base import BaseAdmin
    from starlette_admin.importers import ImportContext, ImportResult

from jinja2 import Environment, Template
from markupsafe import escape
from starlette.datastructures import QueryParams
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER, HTTP_400_BAD_REQUEST
from starlette.templating import Jinja2Templates
from starlette_admin.actions import ActionSelection, action, link_row_action, row_action
from starlette_admin.events import (
    AdminEvent,
    AfterActionContext,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    AfterExportContext,
    AfterImportContext,
    BeforeActionContext,
    BeforeCreateContext,
    BeforeDeleteContext,
    BeforeEditContext,
    BeforeExportContext,
    BeforeImportContext,
    EventBus,
    EventContext,
)
from starlette_admin.exceptions import ActionFailed, FormValidationError
from starlette_admin.export import (
    BaseExporter,
    ExportConfig,
    ExportContext,
    resolve_exporter,
)
from starlette_admin.fields import (
    BaseField,
    CollectionField,
    ComputedField,
    EnumField,
    FileField,
    ListField,
    RelationField,
)
from starlette_admin.filters.base import (
    BaseFilter,
    FilterDataType,
    FilterGroup,
    FilterRule,
    FilterValidationError,
)
from starlette_admin.filters.registry import FilterRegistry
from starlette_admin.flash import flash
from starlette_admin.helpers import (
    create_url as _create_url,
)
from starlette_admin.helpers import (
    detail_url as _detail_url,
)
from starlette_admin.helpers import (
    edit_url as _edit_url,
)
from starlette_admin.helpers import (
    field_error_payload,
    list_url,
    maybe_async,
    not_none,
    safe_redirect_url,
)
from starlette_admin.helpers import (
    static_url as _static_url,
)
from starlette_admin.helpers import (
    view_list_url as _view_list_url,
)
from starlette_admin.i18n import gettext, ngettext
from starlette_admin.i18n import lazy_gettext as _
from starlette_admin.importers import BaseImporter, resolve_importer
from starlette_admin.logging import get_logger
from starlette_admin.routing import route
from starlette_admin.types import (
    FilterChip,
    ListParams,
    RequestAction,
    RowActionsDisplayType,
    RowActionsPosition,
)
from starlette_admin.widgets import (
    BaseWidget,
    Col,
    ColumnWidget,
    FieldRef,
    FieldsetWidget,
    GridWidget,
    HtmlWidget,
    PanelWidget,
    RowWidget,
    TabsWidget,
    WidgetShorthand,
    normalize_widget,
    render_widget,
)

_log = get_logger(__name__)


def _form_layout_field_names(node: BaseWidget) -> Iterator[str]:
    """Yield every `FieldRef.name` referenced anywhere in a normalized
    `form_layout` subtree, at any nesting depth.
    """
    if isinstance(node, FieldRef):
        yield node.name
    elif isinstance(node, RowWidget):
        for child in node.children:
            yield from _form_layout_field_names(
                child.widget if isinstance(child, Col) else child
            )
    elif isinstance(node, (ColumnWidget, GridWidget, PanelWidget, FieldsetWidget)):
        for child in node.children:
            yield from _form_layout_field_names(child)
    elif isinstance(node, TabsWidget):
        for _label, widget in node.tabs:
            yield from _form_layout_field_names(widget)


def _resolve_children(
    children: Sequence[BaseWidget],
    accessible: dict[str, BaseField],
    obj: Any,
    errors: "Mapping[Any, Any] | None",
) -> list[BaseWidget]:
    """Resolve each child of a container node, dropping the ones that
    resolve to nothing (hidden fields, or containers left empty in turn).
    """
    return [
        resolved
        for child in children
        if (resolved := _resolve_form_layout_node(child, accessible, obj, errors))
        is not None
    ]


def _resolve_row_widget(
    node: RowWidget,
    accessible: dict[str, BaseField],
    obj: Any,
    errors: "Mapping[Any, Any] | None",
) -> BaseWidget | None:
    """Resolve a `RowWidget`, dropping the row entirely if none of its
    columns have anything visible left inside them.
    """
    children: list[BaseWidget | Col] = []
    for child in node.children:
        widget = child.widget if isinstance(child, Col) else child
        resolved = _resolve_form_layout_node(widget, accessible, obj, errors)
        if resolved is None:
            continue
        children.append(
            dc_replace(child, widget=resolved) if isinstance(child, Col) else resolved
        )
    return dc_replace(node, children=children) if children else None


def _resolve_panel_widget(
    node: PanelWidget,
    accessible: dict[str, BaseField],
    obj: Any,
    errors: "Mapping[Any, Any] | None",
) -> BaseWidget | None:
    """Resolve a `PanelWidget`, dropping it if it ends up empty.

    A panel left with exactly one visible field has that field's
    `show_label` forced to `False`: the panel title already names the
    field, so the label would just repeat it.
    """
    resolved_children = _resolve_children(node.children, accessible, obj, errors)
    if not resolved_children:
        return None
    if len(resolved_children) == 1 and isinstance(resolved_children[0], FieldRef):
        resolved_children[0] = dc_replace(resolved_children[0], show_label=False)
    return dc_replace(node, children=resolved_children)


def _resolve_tabs_widget(
    node: TabsWidget,
    accessible: dict[str, BaseField],
    obj: Any,
    errors: "Mapping[Any, Any] | None",
) -> BaseWidget | None:
    """Resolve a `TabsWidget`, dropping any tab left with nothing visible
    inside it, and the whole widget if every tab is dropped.
    """
    tabs = [
        (label, resolved)
        for label, widget in node.tabs
        if (resolved := _resolve_form_layout_node(widget, accessible, obj, errors))
        is not None
    ]
    return dc_replace(node, tabs=tabs) if tabs else None


def _resolve_form_layout_node(
    node: BaseWidget,
    accessible: dict[str, BaseField],
    obj: Any,
    errors: "Mapping[Any, Any] | None",
) -> BaseWidget | None:
    """Recursively resolve a normalized `form_layout` subtree against the
    current request.

    A `FieldRef` is bound to its `BaseField`/current value/validation
    error, or dropped if `node.name` isn't in `accessible` (hidden for this
    request/action). A row/column/grid/panel/tab left with nothing visible
    inside it is dropped in turn. Anything else (static content, a custom
    `BaseWidget` subclass) always renders, independent of field visibility.
    """
    if isinstance(node, FieldRef):
        field = accessible.get(node.name)
        if field is None:
            return None
        return dc_replace(
            node,
            _field=field,
            _value=obj.get(node.name) if obj else None,
            _error=errors.get(node.name) if errors else None,
        )
    if isinstance(node, RowWidget):
        return _resolve_row_widget(node, accessible, obj, errors)
    if isinstance(node, PanelWidget):
        return _resolve_panel_widget(node, accessible, obj, errors)
    if isinstance(node, (ColumnWidget, GridWidget, FieldsetWidget)):
        resolved_children = _resolve_children(node.children, accessible, obj, errors)
        return (
            dc_replace(node, children=resolved_children) if resolved_children else None
        )
    if isinstance(node, TabsWidget):
        return _resolve_tabs_widget(node, accessible, obj, errors)
    return node


class BaseView:
    """
    Base class for all views

    Attributes:
        menu_label: Label of the view to be displayed.
        icon: Icon to be displayed for this model in the admin. Only FontAwesome names are supported.
    """

    menu_label: str = ""
    icon: str | None = None

    # Set by BaseAdmin.add_view;
    _admin: "BaseAdmin | None" = None

    def title(self, request: Request) -> str:
        """Return the title of the view to be displayed in the browser tab"""
        return self.menu_label

    def is_active(self, request: Request) -> bool:
        """Return true if the current view is active"""
        return False

    def is_accessible(self, request: Request) -> bool:
        """
        Override this method to add permission checks.
        Return True if current user can access this view
        """
        return True


class DropDown(BaseView):
    """
    Group views inside a dropdown

    Example:
        ```python
        admin.add_view(
            DropDown(
                "Resources",
                icon="fa fa-list",
                views=[
                    ModelView(User),
                    Link(menu_label="Home Page", url="/"),
                    CustomView(menu_label="Dashboard", path="/dashboard", widget=dashboard_widget),
                ],
            )
        )
        ```
    """

    def __init__(
        self,
        menu_label: str,
        views: list[type[BaseView] | BaseView],
        icon: str | None = None,
        always_open: bool = True,
    ) -> None:
        self.menu_label = menu_label
        self.icon = icon
        self.always_open = always_open
        self.views: list[BaseView] = [
            (v if isinstance(v, BaseView) else v()) for v in views
        ]

    def is_active(self, request: Request) -> bool:
        return any(v.is_active(request) for v in self.views)

    def is_accessible(self, request: Request) -> bool:
        return any(v.is_accessible(request) for v in self.views)


class Link(BaseView):
    """
    Add arbitrary hyperlinks to the menu

    Example:
        ```python
        admin.add_view(Link(menu_label="Home Page", icon="fa fa-link", url="/"))
        ```
    """

    def __init__(
        self,
        menu_label: str = "",
        icon: str | None = None,
        url: str = "/",
        target: str | None = "_self",
    ):
        self.menu_label = menu_label
        self.icon = icon
        self.url = url
        self.target = target


class CustomView(BaseView):
    """
    Add your own views (not tied to any particular model). For example,
    a custom home page that displays some analytics data.

    For a page built entirely from built-in widgets, instantiate directly:

        ```python
        admin.add_view(
            CustomView(
                menu_label="System Status",
                icon="fa fa-heart-pulse",
                path="/status",
                widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
            )
        )
        ```

    Subclass when you need custom endpoints or full control over how the
    primary page is rendered. Additional routes are exposed via the
    [route][starlette_admin.routing.route] decorator; re-decorate `index`
    with `@route("")` to replace the default widget rendering with your own
    template:

        ```python
        class AnalyticsDashboard(CustomView):
            menu_label = "Analytics"
            path = "/analytics"

            @route("")
            async def index(self, request: Request) -> Response:
                return self.templates.TemplateResponse(
                    request=request,
                    name="analytics/dashboard.html",
                    context={"title": self.title(request)},
                )

            @route("/data", methods=["GET"])
            async def chart_data(self, request: Request) -> Response:
                rows = await fetch_revenue_by_day(request)
                return JSONResponse(rows)
        ```

    Attributes:
        path: Route path
        route_name: Route name
        add_to_menu: Display to menu or not
        widget: Single widget to render on the default page, or an async (or
            sync) callable ``(request) -> BaseWidget | None`` that returns one
            per-request.  Use the callable form when the widget tree depends on
            the request (current user role, feature flags, live data, …).
    """

    path: str = "/"
    route_name: str | None = None
    add_to_menu: bool = True
    widget: "BaseWidget | Callable[[Request], Awaitable[BaseWidget | None]] | None" = (
        None
    )

    def __init__(
        self,
        menu_label: str | None = None,
        icon: str | None = None,
        path: str | None = None,
        widget: "BaseWidget | Callable[[Request], Awaitable[BaseWidget | None]] | None" = None,
        route_name: str | None = None,
        add_to_menu: bool | None = None,
    ):
        self.menu_label = menu_label or self.menu_label
        self.icon = icon or self.icon
        self.path = path or self.path
        self.route_name = route_name or self.route_name
        self.add_to_menu = add_to_menu if add_to_menu is not None else self.add_to_menu
        self.widget = widget or self.widget
        self.templates: Jinja2Templates | None = None

    async def _resolve_widget(self, request: Request) -> "BaseWidget | None":
        """Return the widget for this request, calling it if it is a callable."""
        if self.widget is None or isinstance(self.widget, BaseWidget):
            return self.widget
        result = self.widget(request)
        if inspect.isawaitable(result):
            return await result
        return result

    @route("")
    async def index(self, request: Request) -> Response:
        """Default handler for the view's primary route: renders ``widget``
        inside the built-in layout. Override (re-decorating with
        ``@route("")``) to render your own template via
        ``self.templates.TemplateResponse`` instead."""
        assert self.templates is not None, "CustomView must be mounted before use"
        assert self._admin is not None, "CustomView must be mounted before use"
        widget = await self._resolve_widget(request)
        widget_html = (
            await render_widget(widget, request, self.templates.env)
            if widget is not None
            else ""
        )
        widget_additional_css = (
            widget.additional_css_links(request) if widget is not None else []
        )
        widget_additional_js = (
            widget.additional_js_links(request) if widget is not None else []
        )
        return self._admin._template_response(
            request=request,
            name="index.html",
            context={
                "title": self.title(request),
                "widget": widget,
                "widget_html": widget_html,
                "widget_additional_css": widget_additional_css,
                "widget_additional_js": widget_additional_js,
            },
        )

    def is_active(self, request: Request) -> bool:
        return request.scope["path"] == request.scope["root_path"] + self.path


async def build_export_form(request: Request, view: "BaseModelView") -> str:
    """Form builder for the built-in `export` batch action.

    Renders `templates/actions/export_form.html` through the admin's Jinja
    environment (a `@action` form builder has no `Environment` of its own).
    """
    assert view._admin is not None, "view must be registered with add_view()"
    env: Environment = view._admin.templates.env
    fields = view.get_fields_list(request, action=RequestAction.EXPORT)
    template = env.get_template("actions/export_form.html")
    return template.render(
        request=request,
        fields=fields,
        exporters=view.exporters,
        filename=view.key or "export",
    )


class BaseModelView(BaseView):
    """
    Base administrative view.
    Derive from this class to implement your administrative interface piece.

    Attributes:
        key: Unique key to identify the model associated to this view.
            Will be used for URL of the endpoints.
        display_name: Name of the view to be displayed
        fields: List of fields
        form_layout: Arranges `fields` on the create/edit forms using the
            same composable widgets as
            [CustomView.widget][starlette_admin.views.CustomView.widget]:
            [PanelWidget][starlette_admin.widgets.PanelWidget] for titled,
            optionally collapsible sections,
            [FieldsetWidget][starlette_admin.widgets.FieldsetWidget] for a
            native bordered `<fieldset>`/`<legend>` grouping,
            [RowWidget][starlette_admin.widgets.RowWidget]/[ColumnWidget][starlette_admin.widgets.ColumnWidget]/[GridWidget][starlette_admin.widgets.GridWidget]
            for layout, [TabsWidget][starlette_admin.widgets.TabsWidget] for
            tabbed sections, [HtmlWidget][starlette_admin.widgets.HtmlWidget]/[TextWidget][starlette_admin.widgets.TextWidget]
            for static content, or any custom `BaseWidget` subclass. A
            declared field is referenced by a
            [FieldRef][starlette_admin.widgets.FieldRef], or by the
            `WidgetShorthand` every widget's `children` accepts in its
            place (see
            [normalize_widget][starlette_admin.widgets.normalize_widget]):
            a bare name renders alone on its own row, a tuple of names
            renders those names side by side on one row, and a list of
            entries stacks them vertically. This is the same shorthand
            usable anywhere a widget tree is built, including
            `CustomView.widget`, not just `form_layout`. Leave unset to
            render all fields as one flat list, unchanged from the default
            behavior. Every field in `fields` must be referenced by exactly
            one `FieldRef`/shorthand somewhere in the tree; one left out is
            appended, in declaration order, as a trailing top-level field,
            so it can never silently disappear from the form because it was
            forgotten when `form_layout` was written.
        pk_attr: Primary key field name
        show_pk_in_forms (bool): Indicates whether the primary key should be
            included in create and edit forms. Default to False.
        exclude_fields_from_list: List of fields to exclude in List page.
        exclude_fields_from_detail: List of fields to exclude in Detail page.
        exclude_fields_from_create: List of fields to exclude from creation page.
        exclude_fields_from_edit: List of fields to exclude from editing page.
        searchable_fields: List of searchable fields.
        sortable_fields: List of sortable fields.
        fields_default_sort: Initial order (sort) to apply to the table.
            Should be a sequence of field names or a tuple of
            (field name, True/False to indicate the sort direction).
            For example:
            `["title",  ("created_at", False), ("price", True)]` will sort
             by `title` ascending, `created_at` ascending and `price` descending.
        exporters: Formats to enable on this view, as extension strings
            (resolved via the `EXPORT_FORMATS` registry), exporter instances
            (for per-instance options), or a mix of both. Defaults to
            ``["csv", "json"]``, which need no extra dependency.
        importers: Formats to enable on this view, as extension strings
            (resolved via the `IMPORT_FORMATS` registry), importer instances,
            or a mix of both. Defaults to ``["csv", "json"]``.
        exclude_fields_from_export: List of fields to exclude from exported data.
        exclude_fields_from_import: List of fields to exclude from import processing.
        column_visibility: Enable/Disable the "Show/Hide columns" dropdown on the
            List page. Visibility is toggled client-side and persisted in
            `localStorage`.
        search_highlight: Highlight the search term in matching table cells.
            Default is `True`.
        search_auto_submit: Auto-submit the search form as the user types
            (debounced). Default is `False`.
        page_size: Default number of items to display in List page pagination.
            Default value is set to `10`.
        page_size_options: Pagination choices displayed in List page.
            Default value is set to `[10, 25, 50, 100]`. Use `-1`to display All
        show_goto_page: Enable/Disable the "Go to page" input in the List
            page pagination footer. Default to `False`.
        show_detail_search: Enable/Disable the search box on the Detail page.
            Default to `False`.
        list_template: List view template. Default is `list.html`.
        detail_template: Details view template. Default is `detail.html`.
        create_template: Edit view template. Default is `create.html`.
        edit_template: Edit view template. Default is `edit.html`.
        actions: List of actions
        action_select_all_limit: Maximum number of rows a batch action may resolve
            via "select all matching" (`all=1`). `handle_action` rejects the
            request with `ActionFailed` if the current filter/search matches more
            rows than this. Default is `1000`.
        row_actions_position: Position of the row actions column. Use
            `RowActionsPosition.BEFORE_COLUMNS` (default) to place it before
            the data columns, or `RowActionsPosition.AFTER_COLUMNS` to place
            it after.
        row_click_navigate: Enable/Disable navigating to the detail page when
            clicking anywhere on a row in the List page. Default is `True`.
        additional_js_links: A list of additional JavaScript files to include.
        additional_css_links: A list of additional CSS files to include.
        inline_editable_fields: Field names that may be edited inline from
            the list page, in a popover anchored to the cell, without
            navigating to the edit page. Each name must be present in
            `fields`, must not be `exclude_from_list`/`exclude_from_edit`,
            and must not be the primary key, a `CollectionField`/`ListField`,
            a `ComputedField`, or a `FileField`/`ImageField`; violating any of
            these raises `ValueError` at startup. Defaults to `None`
            (disabled). An inline save touches only the edited field:
            `get_fields_list` narrows to that field for the whole request,
            so its validators run and the backend writes it, while every
            other field is left untouched. The cross-field `validate` hook
            still runs but receives a data dict holding only the edited
            field; hooks that index other keys must use `data.get(...)` or
            check `request.state.action == RequestAction.INLINE_EDIT`.
            Gated solely by the existing `can_edit(request)`; no separate
            permission method is introduced.


    """

    key: str | None = None
    display_name: str | None = None
    fields: Sequence[BaseField] = []
    form_layout: Sequence[WidgetShorthand] | None = None
    pk_attr: str | None = None
    show_pk_in_forms: bool = False
    exclude_fields_from_list: Sequence[str] = []
    exclude_fields_from_detail: Sequence[str] = []
    exclude_fields_from_create: Sequence[str] = []
    exclude_fields_from_edit: Sequence[str] = []
    searchable_fields: Sequence[str] | None = None
    sortable_fields: Sequence[str] | None = None
    fields_default_sort: Sequence[tuple[str, bool] | str] | None = None
    exporters: Sequence[BaseExporter | str] = ["csv", "json"]
    importers: Sequence[BaseImporter | str] = ["csv", "json"]
    exclude_fields_from_export: Sequence[str] = []
    exclude_fields_from_import: Sequence[str] = []
    column_visibility: bool = True
    search_highlight: bool = True
    search_auto_submit: bool = False
    page_size: int = 10
    page_size_options: Sequence[int] = [10, 25, 50, 100]
    action_select_all_limit: int = 1000
    show_goto_page: bool = False
    show_detail_search: bool = False
    list_template: str = "list.html"
    detail_template: str = "detail.html"
    create_template: str = "create.html"
    edit_template: str = "edit.html"
    actions: Sequence[str] | None = None
    row_actions: Sequence[str] | None = None
    additional_js_links: list[str] | None = None
    additional_css_links: list[str] | None = None
    inline_editable_fields: Sequence[str] | None = None
    row_actions_display_type: RowActionsDisplayType = RowActionsDisplayType.ICON_LIST
    row_actions_position: RowActionsPosition = RowActionsPosition.BEFORE_COLUMNS
    row_click_navigate: bool = True
    inlines: Sequence[Union[type["InlineModelView"], "InlineModelView"]] = []

    _find_foreign_view: Callable[[str], "BaseModelView"]

    def __init__(self) -> None:
        _log.debug(
            "BaseModelView initializing: key=%r class=%s",
            self.key,
            type(self).__name__,
        )
        self._resolve_export_import_types()
        self._init_fields()
        self._validate_inline_editable_fields()
        self._init_form_layout()
        self._actions: dict[str, dict[str, str]] = OrderedDict()
        self._row_actions: dict[str, dict[str, str]] = OrderedDict()
        self._actions_handlers: dict[
            str, Callable[[Request, ActionSelection], Awaitable]
        ] = OrderedDict()
        self._row_actions_handlers: dict[str, Callable[[Request, Any], Awaitable]] = (
            OrderedDict()
        )
        self.events: EventBus = EventBus()
        self._init_actions()
        self._init_inlines()
        _log.info(
            "ModelView ready: key=%r fields=%d actions=%d row_actions=%d inlines=%d",
            self.key,
            len(self._all_fields),
            len(self._actions),
            len(self._row_actions),
            len(self._inline_instances),
        )

    def _resolve_export_import_types(self) -> None:
        """Resolve `exporters`/`importers` entries (format strings or direct
        instances, e.g. a bare `TablibExporter("xlsx")`) into availability-checked
        instances via the format registries."""
        self.exporters = [resolve_exporter(e) for e in self.exporters]
        self.importers = [resolve_importer(i) for i in self.importers]

    def _init_fields(self) -> None:  # noqa: C901
        """Walk ``self.fields`` depth-first, set ``_name`` / ``_view`` on every
        field, apply exclusion overrides, and populate ``self._all_fields`` (the
        flat list of every non-container field at any nesting level).
        """
        _log.debug(
            "_init_fields: key=%r total declared fields=%d",
            self.key,
            len(self.fields),
        )
        self._all_fields: list[BaseField] = []
        all_field_names: list[str] = []
        queue: deque[BaseField] = deque(self.fields)
        while queue:
            field = queue.popleft()
            if not field._name:
                field._name = field.name
            if isinstance(field, CollectionField):
                field._view = self
                for f in field.fields:
                    f._name = f"{field._name}.{f.name}"
                queue.extend(field.fields)
            elif isinstance(field, RelationField):
                field._view = self
                _log.debug(
                    "_init_fields: RelationField %r wired to view (key=%r)",
                    field.name,
                    self.key,
                )
            elif isinstance(field, ListField) and isinstance(
                field.field, CollectionField
            ):
                queue.append(field.field)
            name: str = field._name
            if name == self.pk_attr and not self.show_pk_in_forms:
                field.exclude_from_create = True
                field.exclude_from_edit = True
                _log.debug(
                    "_init_fields: pk field %r excluded from create/edit forms (show_pk_in_forms=False)",
                    name,
                )
            if name in self.exclude_fields_from_list:
                field.exclude_from_list = True
            if name in self.exclude_fields_from_detail:
                field.exclude_from_detail = True
            if name in self.exclude_fields_from_create:
                field.exclude_from_create = True
            if name in self.exclude_fields_from_edit:
                field.exclude_from_edit = True
            if name in self.exclude_fields_from_export:
                field.exclude_from_export = True
            if name in self.exclude_fields_from_import:
                field.exclude_from_import = True
            if not isinstance(field, CollectionField):
                self._all_fields.append(field)
                all_field_names.append(name)
                field.searchable = (self.searchable_fields is None) or (
                    name in self.searchable_fields
                )
                field.orderable = (self.sortable_fields is None) or (
                    name in self.sortable_fields
                )
                field.inline_editable = name in (self.inline_editable_fields or [])
        if not self.pk_attr:
            _log.warning(
                "_init_fields: key=%r has no pk_attr set; find_by_pk / get_pk_value will not work",
                self.key,
            )
        if self.searchable_fields is None:
            self.searchable_fields = all_field_names[:]
        if self.sortable_fields is None:
            self.sortable_fields = all_field_names[:]
        if self.fields_default_sort is None and self.pk_attr:
            self.fields_default_sort = [self.pk_attr]
        _log.debug(
            "_init_fields done: key=%r resolved %d leaf field(s): %s",
            self.key,
            len(self._all_fields),
            all_field_names,
        )

    def _validate_inline_editable_fields(self) -> None:
        """Validates `inline_editable_fields` at startup (fail fast): every
        name must exist in `fields`, be visible on the list page and
        editable on the edit page, and not be a container, computed, file,
        or the primary key field. Called after `_init_fields`, so
        `exclude_from_list`/`exclude_from_edit` already reflect
        `exclude_fields_from_list`/`exclude_fields_from_edit` and the
        pk-field exclusion.
        """
        if not self.inline_editable_fields:
            return
        fields_by_name = {f.name: f for f in self.fields}
        for name in self.inline_editable_fields:
            field = fields_by_name.get(name)
            if field is None:
                raise ValueError(
                    f"{type(self).__name__}: inline_editable_fields references "
                    f"{name!r}, which is not declared in `fields`."
                )
            if name == self.pk_attr:
                raise ValueError(
                    f"{type(self).__name__}: inline_editable_fields cannot "
                    f"include the primary key field {name!r}."
                )
            if field.exclude_from_list or field.exclude_from_edit:
                raise ValueError(
                    f"{type(self).__name__}: inline_editable_fields field "
                    f"{name!r} must be visible on the list page and editable "
                    "on the edit page (exclude_from_list and "
                    "exclude_from_edit must both be False)."
                )
            if isinstance(
                field, (CollectionField, ListField, ComputedField, FileField)
            ):
                raise ValueError(
                    f"{type(self).__name__}: inline_editable_fields field "
                    f"{name!r} is a {type(field).__name__}, which is not "
                    "supported for inline edit."
                )

    def _init_form_layout(self) -> None:
        """Normalize `self.form_layout` to a list of `BaseWidget`, expanding
        field-name/tuple shorthand at any nesting depth, and validate it
        against `self.fields`: every declared field must be referenced by
        exactly one `FieldRef` in the tree. A field declared but never
        referenced is appended, in declaration order, as a trailing
        top-level `FieldRef`, so it can never silently vanish from the
        create/edit forms because it was forgotten when `form_layout` was
        written.
        """
        if not self.form_layout:
            return
        nodes = [normalize_widget(entry) for entry in self.form_layout]
        declared_names = [f.name for f in self.fields]
        declared_names_set = set(declared_names)
        seen: set[str] = set()
        for node in nodes:
            for name in _form_layout_field_names(node):
                if name not in declared_names_set:
                    raise ValueError(
                        f"{type(self).__name__}: form_layout references {name!r}, "
                        "which is not declared in `fields`."
                    )
                if name in seen:
                    raise ValueError(
                        f"{type(self).__name__}: field {name!r} is referenced more "
                        "than once in form_layout."
                    )
                seen.add(name)
        leftover = [name for name in declared_names if name not in seen]
        if leftover:
            _log.debug(
                "_init_form_layout: key=%r field(s) %s not referenced in "
                "form_layout; appending trailing FieldRef(s)",
                self.key,
                leftover,
            )
            nodes.extend(FieldRef(name) for name in leftover)
        self.form_layout = nodes

    def is_active(self, request: Request) -> bool:
        return request.path_params.get("key", None) == self.key

    def _init_actions(self) -> None:
        self._init_batch_actions()
        self._init_row_actions()
        self._validate_actions()

    def _init_batch_actions(self) -> None:
        """
        This method initializes batch and row actions, collects their handlers,
        and validates that all specified actions exist.
        """
        for _method_name, method in inspect.getmembers(
            self, predicate=inspect.ismethod
        ):
            if hasattr(method, "_action"):
                name = method._action.get("name")
                self._actions[name] = method._action
                self._actions_handlers[name] = method
                _log.debug(
                    "_init_batch_actions: discovered action %r on %s",
                    name,
                    type(self).__name__,
                )

        if self.actions is None:
            self.actions = list(self._actions_handlers.keys())
        elif "export" in self._actions_handlers and "export" not in self.actions:
            # "export" is new: existing code with a hand-picked `actions`
            # list was written before it existed and has no way to know to
            # list it. Visibility is controlled by `can_export()`, not by
            # `actions` membership, so it's appended rather than silently
            # dropped.
            self.actions = [*self.actions, "export"]

        _log.debug(
            "_init_batch_actions: key=%r active actions=%s",
            self.key,
            list(self.actions) if self.actions else [],
        )

    def _init_row_actions(self) -> None:
        for _method_name, method in inspect.getmembers(
            self, predicate=inspect.ismethod
        ):
            if hasattr(method, "_row_action"):
                name = method._row_action.get("name")
                self._row_actions[name] = method._row_action
                self._row_actions_handlers[name] = method
                _log.debug(
                    "_init_row_actions: discovered row action %r on %s",
                    name,
                    type(self).__name__,
                )

        if self.row_actions is None:
            self.row_actions = list(self._row_actions_handlers.keys())

        _log.debug(
            "_init_row_actions: key=%r active row actions=%s",
            self.key,
            list(self.row_actions) if self.row_actions else [],
        )

    def _validate_actions(self) -> None:
        for action_name in not_none(self.actions):
            if action_name not in self._actions:
                _log.error(
                    "_validate_actions: key=%r references unknown action %r; available: %s",
                    self.key,
                    action_name,
                    list(self._actions.keys()),
                )
                raise ValueError(f"Unknown action with name `{action_name}`")
            action_def = self._actions[action_name]
            if action_def.get("dedicated_button") and not action_def.get(
                "allow_empty_selection"
            ):
                raise ValueError(
                    f"Action `{action_name}`: dedicated_button=True requires "
                    "allow_empty_selection=True"
                )
        for action_name in not_none(self.row_actions):
            if action_name not in self._row_actions:
                _log.error(
                    "_validate_actions: key=%r references unknown row action %r; available: %s",
                    self.key,
                    action_name,
                    list(self._row_actions.keys()),
                )
                raise ValueError(f"Unknown row action with name `{action_name}`")

    def _init_inlines(self) -> None:
        """Instantiate inline view classes and wire them to this parent view."""
        self._inline_instances: list[InlineModelView] = [
            (
                inline
                if isinstance(inline, InlineModelView)
                else inline(parent_view=self)
            )
            for inline in self.inlines
        ]
        for inline in self._inline_instances:
            inline.parent_view = self
            _log.debug(
                "_init_inlines: wired inline key=%r to parent key=%r",
                inline.key,
                self.key,
            )
        if self._inline_instances:
            _log.info(
                "ModelView %r: %d inline(s) registered: %s",
                self.key,
                len(self._inline_instances),
                [i.key for i in self._inline_instances],
            )
        else:
            _log.debug("ModelView %r: no inlines", self.key)

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        """
        Verify if action with `name` is allowed.
        Override this method to allow or disallow actions based
        on some condition.

        Args:
            name: Action name
            request: Starlette request
        """
        if name == "delete":
            return self.can_delete(request)
        if name == "export":
            return self.can_export(request) and bool(self.exporters)
        return True

    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        """
        Verify if the row action with `name` is allowed.
        Override this method to allow or disallow row actions based
        on some condition.

        Args:
            name: Row action name
            request: Starlette request
        """
        if name == "delete":
            return self.can_delete(request)
        if name == "edit":
            return self.can_edit(request)
        if name == "view":
            return self.can_view_detail(request)
        return True

    async def is_row_action_allowed_for_obj(
        self, request: Request, name: str, obj: Any
    ) -> bool:
        """
        Verify if the row action with `name` is allowed for `obj`.
        Override this method to allow or disallow a row action per
        row, based on the row's own data, for example hiding
        `make_published` once an article's status is already
        published.

        Called once for every row, in addition to `is_row_action_allowed`.
        Defaults to `is_row_action_allowed`, ignoring `obj`.

        Args:
            name: Row action name
            request: Starlette request
            obj: The row's underlying object
        """
        return await self.is_row_action_allowed(request, name)

    @staticmethod
    async def _resolve_form(form: Any, *args: Any) -> Any:
        """Resolve a `form` value that may be a static HTML string or a
        callable that builds the HTML per request (and, for row actions,
        per `obj`)."""
        if not callable(form):
            return form
        result = form(*args)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def get_all_actions(self, request: Request) -> list[dict[str, Any]]:
        """Return a list of allowed batch actions.

        A `form` callable is invoked as `(request)`, or `(request, view)` when
        it declares a second parameter — how the built-in export action's form
        builder receives the view to list its fields and formats.
        """
        actions = []
        for action_name in not_none(self.actions):
            if await self.is_action_allowed(request, action_name):
                _action = self._actions.get(action_name, {})
                form = _action.get("form")
                if callable(form):
                    params = inspect.signature(form).parameters
                    args = (request, self) if len(params) >= 2 else (request,)
                    _action = {
                        **_action,
                        "form": await self._resolve_form(form, *args),
                    }
                actions.append(_action)
        return actions

    async def get_row_actions_for_obj(
        self, request: Request, obj: Any
    ) -> list[dict[str, Any]]:
        """Return the list of row actions allowed for this specific `obj`."""
        row_actions = []
        for row_action_name in not_none(self.row_actions):
            if await self.is_row_action_allowed(
                request, row_action_name
            ) and await self.is_row_action_allowed_for_obj(
                request, row_action_name, obj
            ):
                _row_action = self._row_actions.get(row_action_name, {})
                if (
                    request.state.action == RequestAction.LIST
                    and not _row_action.get("exclude_from_list")
                ) or (
                    request.state.action == RequestAction.DETAIL
                    and not _row_action.get("exclude_from_detail")
                ):
                    if callable(_row_action.get("form")):
                        _row_action = {
                            **_row_action,
                            "form": await self._resolve_form(
                                _row_action["form"], request, obj
                            ),
                        }
                    row_actions.append(_row_action)
        return row_actions

    async def before_action(
        self, request: Request, name: str, selection: ActionSelection
    ) -> None:
        """
        This hook is called before a batch or row action runs.

        Args:
            request: The request being processed.
            name: The action's name.
            selection: The targeted rows (a single pk for a row action). Resolving
                `selection.pks()`/`.rows()`/`.count()` runs a query, so only call
                them if the hook actually needs the target rows.
        """

    async def after_action(
        self,
        request: Request,
        name: str,
        selection: ActionSelection,
        success: bool,
        error: str | None = None,
    ) -> None:
        """
        This hook is called after a batch or row action completes, whether it
        succeeded or raised `ActionFailed`.

        Args:
            request: The request being processed.
            name: The action's name.
            selection: The targeted rows (a single pk for a row action).
            success: Whether the action completed without raising `ActionFailed`.
            error: The `ActionFailed` message when `success` is `False`, else `None`.
        """

    async def _emit_before_action(
        self, request: Request, name: str, selection: ActionSelection
    ) -> None:
        """Calls the `before_action` hook, then emits the `BEFORE_ACTION` event on `view.events`."""
        await self.before_action(request, name, selection)
        ctx = BeforeActionContext(
            event=AdminEvent.BEFORE_ACTION,
            request=request,
            view_key=not_none(self.key),
            action_name=name,
            selection=selection,
        )
        await self.events.emit(ctx)

    async def _emit_after_action(
        self,
        request: Request,
        name: str,
        selection: ActionSelection,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Calls the `after_action` hook, then emits the `AFTER_ACTION` event on `view.events`."""
        await self.after_action(request, name, selection, success, error)
        ctx = AfterActionContext(
            event=AdminEvent.AFTER_ACTION,
            request=request,
            view_key=not_none(self.key),
            action_name=name,
            selection=selection,
            success=success,
            error=error,
        )
        await self.events.emit(ctx)

    async def handle_action(
        self, request: Request, selection: ActionSelection, name: str
    ) -> None | Response:
        """
        Handle action with `name`.
        Raises:
            ActionFailed: to display meaningfully error
        """
        handler = self._actions_handlers.get(name, None)
        if handler is None:
            _log.warning(
                "handle_action: key=%r no handler registered for name=%r",
                self.key,
                name,
            )
            raise ActionFailed(_("Invalid action"))
        if not await self.is_action_allowed(request, name):
            _log.warning(
                "handle_action: key=%r name=%r denied (is_action_allowed=False)",
                self.key,
                name,
            )
            raise ActionFailed(_("Forbidden"))
        if (
            not self._actions[name].get("allow_empty_selection")
            and not await selection.count()
        ):
            _log.warning(
                "handle_action: key=%r name=%r rejected (empty selection not allowed)",
                self.key,
                name,
            )
            raise ActionFailed(_("Please select at least one item"))
        await self._emit_before_action(request, name, selection)
        _log.debug(
            "handle_action: key=%r name=%r dispatching handler",
            self.key,
            name,
        )
        try:
            handler_return = await handler(request, selection)
        except ActionFailed as exc:
            await self._emit_after_action(request, name, selection, False, exc.msg)
            raise
        _log.debug(
            "handle_action: key=%r name=%r handler returned",
            self.key,
            name,
        )
        await self._emit_after_action(request, name, selection, True)
        custom_response = self._actions[name]["custom_response"]
        if isinstance(handler_return, Response) and not custom_response:
            raise ActionFailed(
                _("Set custom_response=True on this action to return a custom response")
            )
        return handler_return

    async def handle_row_action(
        self, request: Request, pk: Any, name: str
    ) -> None | Response:
        """
        Handle row action with `name`.
        Raises:
            ActionFailed: to display meaningfully error
        """
        handler = self._row_actions_handlers.get(name, None)
        if handler is None:
            _log.warning(
                "handle_row_action: key=%r no handler registered for name=%r",
                self.key,
                name,
            )
            raise ActionFailed(_("Invalid row action"))
        if not await self.is_row_action_allowed(request, name):
            _log.warning(
                "handle_row_action: key=%r name=%r pk=%s denied (is_row_action_allowed=False)",
                self.key,
                name,
                pk,
            )
            raise ActionFailed(_("Forbidden"))
        obj = await self.find_by_pk(request, pk)
        if obj is not None and not await self.is_row_action_allowed_for_obj(
            request, name, obj
        ):
            _log.warning(
                "handle_row_action: key=%r name=%r pk=%s denied (is_row_action_allowed_for_obj=False)",
                self.key,
                name,
                pk,
            )
            raise ActionFailed(_("Forbidden"))
        selection = ActionSelection(self, request, [pk], None, None)
        await self._emit_before_action(request, name, selection)
        _log.debug(
            "handle_row_action: key=%r name=%r dispatching handler pk=%s",
            self.key,
            name,
            pk,
        )
        try:
            handler_return = await handler(request, pk)
        except ActionFailed as exc:
            await self._emit_after_action(request, name, selection, False, exc.msg)
            raise
        _log.debug(
            "handle_row_action: key=%r name=%r handler returned pk=%s",
            self.key,
            name,
            pk,
        )
        await self._emit_after_action(request, name, selection, True)
        custom_response = self._row_actions[name]["custom_response"]
        if isinstance(handler_return, Response) and not custom_response:
            raise ActionFailed(
                _("Set custom_response=True on this action to return a custom response")
            )
        return handler_return

    @action(
        name="delete",
        text=_("Delete"),
        confirmation=_("Are you sure you want to delete selected items?"),
        submit_btn_text=_("Yes, delete all"),
        submit_btn_class="action.modal_confirm_button_delete",
    )
    async def delete_action(self, request: Request, selection: ActionSelection) -> None:
        pks = await selection.pks()
        if len(pks) == 1:
            obj = await self.find_by_pk(request, pks[0])
            obj_repr = await self.repr(obj, request) if obj is not None else str(pks[0])
        affected_rows = await self.delete(request, pks)
        _log.info(
            "delete_action: key=%r pks=%s affected=%s",
            self.key,
            pks,
            affected_rows,
        )
        if len(pks) == 1:
            message = gettext('The item "%(repr)s" was successfully deleted.') % {
                "repr": obj_repr
            }
        else:
            message = ngettext(
                "1 item was successfully deleted.",
                "%(count)d items were successfully deleted.",
                affected_rows or 0,
            ) % {"count": affected_rows}
        flash(request, message, "success")

    @staticmethod
    def _export_check_max_rows(count: int, max_rows: int | None) -> None:
        if max_rows is not None and count > max_rows:
            raise ActionFailed(
                gettext(
                    "Export would return %(count)d rows, which exceeds the "
                    "configured maximum of %(max)d. Apply a filter to narrow "
                    "the result set."
                )
                % {"count": count, "max": max_rows}
            )

    async def _export_resolve_items(
        self,
        request: Request,
        selection: ActionSelection,
        scope: str,
        list_params: ListParams,
        export_config: ExportConfig,
    ) -> Sequence[Any]:
        """Resolve the rows to export for one scope, enforcing
        `export_config.max_rows` with a `count()` pre-check before fetching."""
        if scope == "page":
            skip = (
                (list_params.page - 1) * list_params.page_size
                if list_params.page_size > 0
                else 0
            )
            limit = list_params.page_size
            total = await self.count(
                request, q=list_params.q, filters=list_params.filters
            )
            export_total = max(0, total - skip)
            if limit > 0:
                export_total = min(export_total, limit)
            self._export_check_max_rows(export_total, export_config.max_rows)
            return await self.find_all(
                request=request,
                skip=skip,
                limit=limit,
                q=list_params.q,
                sorts=list_params.sorts,
                filters=list_params.filters,
            )
        if selection.is_select_all:
            total = await self.count(
                request, q=list_params.q, filters=list_params.filters
            )
            self._export_check_max_rows(total, export_config.max_rows)
            return await self.find_all(
                request=request,
                skip=0,
                limit=-1,
                q=list_params.q,
                sorts=list_params.sorts,
                filters=list_params.filters,
            )
        pks = await selection.pks()
        self._export_check_max_rows(len(pks), export_config.max_rows)
        return await self.find_by_pks(request, pks)

    @action(
        name="export",
        text=_("Export"),
        confirmation="",
        header=_("Configure your export"),
        icon_class="list.export",
        submit_btn_text=_("Export"),
        form=build_export_form,
        custom_response=True,
        allow_empty_selection=True,
        dedicated_button=True,
        modal_size="lg",
    )
    async def export_action(
        self, request: Request, selection: ActionSelection
    ) -> Response:
        request.state.action = RequestAction.EXPORT
        form = await request.form()
        scope = str(form.get("scope") or "page")
        fmt = str(form.get("format") or "")
        filename = (str(form.get("filename") or "").strip()) or (self.key or "export")
        submitted_fields = form.getlist("fields")
        export_config = getattr(request.state, "export_config", None) or ExportConfig()
        exporters = cast("list[BaseExporter]", self.exporters)

        try:
            exporter = next(
                (e for e in exporters if (e.format_key or e.extension) == fmt),
                None,
            )
            if exporter is None:
                raise ActionFailed(
                    gettext("Unknown export format %(format)s") % {"format": fmt}
                )

            all_fields = list(self.get_fields_list(request))
            if submitted_fields:
                allowed = {f.name for f in all_fields if f.name in submitted_fields}
                fields = [f for f in all_fields if f.name in allowed] or all_fields
            else:
                fields = all_fields

            list_query = QueryParams(
                (request.query_params.get("_list_query") or "").lstrip("?")
            )
            list_params = self._parse_list_params(request, list_query)
            items = await self._export_resolve_items(
                request, selection, scope, list_params, export_config
            )

            rows = [await self.serialize(item, request) for item in items]
            export_ctx = ExportContext(
                fields=fields,
                rows=rows,
                view=self,
                request=request,
                filename=filename,
                export_config=export_config,
            )
            await self._emit_before_export(request, exporter, items, export_ctx)
            response = await exporter.build_response(export_ctx)
            await self._emit_after_export(request, exporter, items, export_ctx)
            return response
        except (ActionFailed, ImportError) as exc:
            message = exc.msg if isinstance(exc, ActionFailed) else str(exc)
            flash(request, message, "error")
            fallback = _view_list_url(request, not_none(self.key))
            redirect_url = safe_redirect_url(
                request.query_params.get("_origin") or fallback, request, fallback
            )
            return RedirectResponse(redirect_url, status_code=HTTP_303_SEE_OTHER)

    @link_row_action(
        name="view",
        text=_("View"),
        icon_class="default_actions.view",
        exclude_from_detail=True,
    )
    def row_action_1_view(self, request: Request, pk: Any) -> str:
        return _detail_url(request, not_none(self.key), pk)

    @link_row_action(
        name="edit",
        text=_("Edit"),
        icon_class="default_actions.edit",
        action_btn_class="action.row_item_edit",
    )
    def row_action_2_edit(self, request: Request, pk: Any) -> str:
        return _edit_url(request, not_none(self.key), pk)

    @row_action(
        name="delete",
        text=_("Delete"),
        confirmation=_("Are you sure you want to delete this item?"),
        icon_class="default_actions.delete",
        submit_btn_text=_("Yes, delete"),
        submit_btn_class="action.modal_confirm_button_delete",
        action_btn_class="action.row_item_delete",
    )
    async def row_action_3_delete(self, request: Request, pk: Any) -> None:
        obj = await self.find_by_pk(request, pk)
        obj_repr = await self.repr(obj, request) if obj is not None else str(pk)
        await self.delete(request, [pk])
        flash(
            request,
            gettext('The item "%(repr)s" was successfully deleted.')
            % {"repr": obj_repr},
            "success",
        )

    @abstractmethod
    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        sorts: Sequence[tuple[str, str]] | None = None,
        filters: FilterGroup | None = None,
    ) -> Sequence[Any]:
        """
        Find all items
        Parameters:
            request: The request being processed
            skip: should return values start from position skip+1
            limit: number of maximum items to return
            q: Full-text search term (`ListParams.q`). `None` applies no
                text search.
            sorts: Ordered list of ``(field_name, direction)`` tuples from
                `ListParams.sorts`.  ``direction`` is ``"asc"`` or ``"desc"``.
                `None` or empty list applies no explicit ordering.
            filters: Parsed & validated filter tree (`ListParams.filters`) to
                apply on top of `q`. `None`/empty applies no filtering;
                see [BaseFilter.apply][starlette_admin.filters.BaseFilter.apply].
        """
        raise NotImplementedError()

    @abstractmethod
    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        """
        Count items
        Parameters:
            request: The request being processed
            q: Full-text search term (`ListParams.q`). `None` applies no
                text search.
            filters: Parsed & validated filter tree (`ListParams.filters`) to
                apply on top of `q`. `None`/empty applies no filtering;
                see [BaseFilter.apply][starlette_admin.filters.BaseFilter.apply].
        """
        raise NotImplementedError()

    @abstractmethod
    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        """
        Find one item
        Parameters:
            request: The request being processed
            pk: Primary key
        """
        raise NotImplementedError()

    @abstractmethod
    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        """
        Find many items
        Parameters:
            request: The request being processed
            pks: List of Primary key
        """
        raise NotImplementedError()

    async def validate_fields(
        self,
        request: Request,
        data: dict[str, Any],
        exclude: Collection[str] = (),
    ) -> None:
        """Runs every field's own validation
        ([BaseField.validate][starlette_admin.fields.BaseField.validate]:
        the `required` check plus the field's `validators` chain) against the
        parsed form data, gathering all failures before raising a single
        [FormValidationError][starlette_admin.exceptions.FormValidationError]
        keyed by field name. `data` is also passed to each field as
        `form_values`, so validators can read other fields' parsed values.

        The admin calls this on the parsed form values before file storage and
        before `create`/`edit`, so field validators always see backend-agnostic
        values (relation fields see primary keys). For cross-field or
        backend-specific logic, override
        [validate][starlette_admin.views.BaseModelView.validate] instead.

        Parameters:
            request: The request being processed.
            data: The parsed form data, keyed by field name.
            exclude: Field names to skip (e.g., a primary key nulled on import).
        """
        errors: dict[str | int, Any] = {}
        for field in self.get_fields_list(request):
            if field.read_only or field.name in exclude:
                continue
            try:
                await field.validate(request, data.get(field.name), data)
            except ValueError as exc:
                errors[field.name] = field_error_payload(exc)
        if errors:
            raise FormValidationError(errors)

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        """Override this method to validate submitted data before it's persisted,
        typically for logic that spans multiple fields. Single-field rules are
        better expressed as field `validators`.

        Backends call this hook from `create`/`edit`, after per-field validation
        has passed and after backend-specific data arrangement.

        Parameters:
            request: The request being processed.
            data: The submitted form data.

        Raises:
            FormValidationError: To surface field-level errors to the user.

        Examples:
            ```python
            from starlette_admin.contrib.sqla import ModelView
            from starlette_admin.exceptions import FormValidationError


            class PostView(ModelView):

                async def validate(self, request: Request, data: Dict[str, Any]) -> None:
                    errors: Dict[str, str] = dict()
                    if data["date"] is not None and data["date"] < data["created_at"]:
                        errors["date"] = "Publication cannot predate creation"
                    if len(errors) > 0:
                        raise FormValidationError(errors)
            ```
        """

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        """
        This hook is called before a new item is created.

        Args:
            request: The request being processed.
            data: Dictionary containing converted form data.
            obj: The object about to be created.
        """

    @abstractmethod
    async def create(self, request: Request, data: dict) -> Any:
        """
        Handles the creation of an item.

        Parameters:
            request: The request being processed.
            data: Dictionary containing converted form data.

        Returns:
            Any: The newly created item.
        """
        raise NotImplementedError()

    async def after_create(self, request: Request, obj: Any) -> None:
        """
        This hook is called after a new item is successfully created.

        Args:
            request: The request being processed.
            obj: The newly created object.
        """

    async def after_create_committed(self, request: Request, obj: Any) -> None:
        """
        This hook is called after the transaction that created the item has been
        committed. Use this hook for external side effects (e.g., sending emails, triggering webhooks) that must
        only occur after the data is durably committed. Avoid writing through
        ``request.state.session`` within this hook.

        This hook is only emitted by backends that defer the transaction commit until the end of the request
        (e.g., the SQLAlchemy backend).

        Args:
            request: The request being processed.
            obj: The newly created object.
        """

    async def before_edit(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        """
        This hook is called before an item is edited.

        Args:
            request: The request being processed.
            data: Dictionary containing converted form data.
            obj: The object about to be edited.
        """

    @abstractmethod
    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        """
        Handles the editing of an item.

        Parameters:
            request: The request being processed.
            pk: The primary key of the item.
            data: Dictionary containing converted form data.

        Returns:
            Any: The edited item.
        """
        raise NotImplementedError()

    async def after_edit(self, request: Request, obj: Any) -> None:
        """
        This hook is called after an item is successfully edited.

        Args:
            request: The request being processed.
            obj: The edited object.
        """

    async def after_edit_committed(self, request: Request, obj: Any) -> None:
        """
        This hook is called after the transaction that edited the item has been
        committed. Use this hook for external side effects (e.g., sending emails, triggering webhooks) that must
        only occur after the data is durably committed. Avoid writing through
        ``request.state.session`` within this hook.

        This hook is only emitted by backends that defer the transaction commit until the end of the request
        (e.g., the SQLAlchemy backend).

        Args:
            request: The request being processed.
            obj: The edited object.
        """

    async def before_delete(self, request: Request, obj: Any) -> None:
        """
        This hook is called before an item is deleted.

        Args:
            request: The request being processed.
            obj: The object about to be deleted.
        """

    @abstractmethod
    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        """
        Deletes multiple items in bulk.

        Parameters:
            request: The request being processed.
            pks: A list of primary keys for the items to be deleted.
        """
        raise NotImplementedError()

    async def after_delete(self, request: Request, obj: Any) -> None:
        """
        This hook is called after an item is successfully deleted.

        Args:
            request: The request being processed.
            obj: The deleted object.
        """

    async def after_delete_committed(self, request: Request, obj: Any) -> None:
        """
        This hook is called after the transaction that deleted the item has been
        committed. Use this hook for external side effects (e.g., sending emails, triggering webhooks) that must
        only occur after the data is durably committed. Avoid writing through
        ``request.state.session`` within this hook.

        This hook is only emitted by backends that defer the transaction commit until the end of the request
        (e.g., the SQLAlchemy backend).

        Args:
            request: The request being processed.
            obj: The deleted object.
        """

    async def before_export(self, request: Request, ctx: "ExportContext") -> None:
        """
        This hook is called before items are exported.

        Args:
            request: The request being processed.
            ctx: The export context, including `export_type`, `items`, `view_key`, and other relevant details.
        """

    async def after_export(self, request: Request, ctx: "ExportContext") -> None:
        """
        This hook is called after items are successfully exported.

        Args:
            request: The request being processed.
            ctx: The export context, including `export_type`, `items`, `row_count`, `view_key`, and other relevant details.
        """

    async def before_import(self, request: Request, ctx: "ImportContext") -> None:
        """
        This hook is called before an import is processed.

        Args:
            request: The request being processed.
            ctx: The import context, including `import_type`, `view_key`, and other relevant details.
        """

    async def after_import(
        self,
        request: Request,
        ctx: "ImportContext",
        result: "ImportResult",
    ) -> None:
        """
        This hook is called after an import finishes (even if individual rows
        had validation errors).

        Args:
            request: The request being processed.
            ctx: The import context, including `import_type`, `row_count`, `error_count`, `view_key`, and other relevant details.
            result: The complete import result, including per-row error details and the `dry_run` flag.
        """

    # Private event orchestration helpers. ORM-specific implementations invoke these methods.
    # These are called at the appropriate points within their `create()`, `edit()`, or `delete()` method bodies.
    async def _emit_before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        """Calls the `before_create` hook, then emits the `BEFORE_CREATE` event on `view.events`."""
        await self.before_create(request, data, obj)
        ctx = BeforeCreateContext(
            event=AdminEvent.BEFORE_CREATE,
            request=request,
            view_key=not_none(self.key),
            data=data,
            obj=obj,
        )
        await self.events.emit(ctx)

    async def _emit_after_create(self, request: Request, obj: Any) -> None:
        """Calls the `after_create` hook, then emits the `AFTER_CREATE` event on `view.events`."""
        await self.after_create(request, obj)
        ctx = AfterCreateContext(
            event=AdminEvent.AFTER_CREATE,
            request=request,
            view_key=not_none(self.key),
            obj=obj,
            pk=await self.get_pk_value(request, obj),
        )
        await self.events.emit(ctx)

    async def _emit_after_create_committed(self, request: Request, obj: Any) -> None:
        """Calls the `after_create_committed` hook, then emits the `AFTER_CREATE_COMMITTED` event on `view.events`."""
        await self.after_create_committed(request, obj)
        ctx = AfterCreateContext(
            event=AdminEvent.AFTER_CREATE_COMMITTED,
            request=request,
            view_key=not_none(self.key),
            obj=obj,
            pk=await self.get_pk_value(request, obj),
        )
        await self.events.emit(ctx)

    async def _emit_before_edit(
        self,
        request: Request,
        data: dict[str, Any],
        obj: Any,
        pk: Any = None,
        old_data: dict[str, Any] | None = None,
    ) -> None:
        """Calls the `before_edit` hook, then emits the `BEFORE_EDIT` event on `view.events`."""
        await self.before_edit(request, data, obj)
        ctx = BeforeEditContext(
            event=AdminEvent.BEFORE_EDIT,
            request=request,
            view_key=not_none(self.key),
            pk=pk,
            data=data,
            obj=obj,
            old_data=old_data or {},
        )
        self._tag_inline_edit(request, ctx)
        await self.events.emit(ctx)

    async def _emit_after_edit(
        self,
        request: Request,
        obj: Any,
        pk: Any = None,
        old_data: dict[str, Any] | None = None,
    ) -> None:
        """Calls the `after_edit` hook, then emits the `AFTER_EDIT` event on `view.events`."""
        await self.after_edit(request, obj)
        ctx = AfterEditContext(
            event=AdminEvent.AFTER_EDIT,
            request=request,
            view_key=not_none(self.key),
            pk=pk,
            obj=obj,
            old_data=old_data or {},
        )
        self._tag_inline_edit(request, ctx)
        await self.events.emit(ctx)

    async def _emit_after_edit_committed(
        self,
        request: Request,
        obj: Any,
        old_data: dict[str, Any] | None = None,
    ) -> None:
        """Calls the `after_edit_committed` hook, then emits the `AFTER_EDIT_COMMITTED` event on `view.events`."""
        await self.after_edit_committed(request, obj)
        ctx = AfterEditContext(
            event=AdminEvent.AFTER_EDIT_COMMITTED,
            request=request,
            view_key=not_none(self.key),
            pk=await self.get_pk_value(request, obj),
            obj=obj,
            old_data=old_data or {},
        )
        self._tag_inline_edit(request, ctx)
        await self.events.emit(ctx)

    @staticmethod
    def _tag_inline_edit(request: Request, ctx: "EventContext") -> None:
        """Marks `ctx.extra["inline"] = True` when the edit runs under
        `RequestAction.INLINE_EDIT` (the inline-edit endpoint), so listeners
        can distinguish an inline edit from a regular edit-page submission."""
        if getattr(request.state, "action", None) == RequestAction.INLINE_EDIT:
            ctx.extra["inline"] = True

    async def _emit_before_delete(self, request: Request, pk: Any, obj: Any) -> None:
        """Calls the `before_delete` hook, then emits the `BEFORE_DELETE` event on `view.events`."""
        await self.before_delete(request, obj)
        ctx = BeforeDeleteContext(
            event=AdminEvent.BEFORE_DELETE,
            request=request,
            view_key=not_none(self.key),
            pk=pk,
            obj=obj,
        )
        await self.events.emit(ctx)

    async def _emit_after_delete(self, request: Request, pk: Any, obj: Any) -> None:
        """Calls the `after_delete` hook, then emits the `AFTER_DELETE` event on `view.events`."""
        await self.after_delete(request, obj)
        ctx = AfterDeleteContext(
            event=AdminEvent.AFTER_DELETE,
            request=request,
            view_key=not_none(self.key),
            pk=pk,
            obj=obj,
        )
        await self.events.emit(ctx)

    async def _emit_after_delete_committed(
        self, request: Request, pk: Any, obj: Any
    ) -> None:
        """Calls the `after_delete_committed` hook, then emits the `AFTER_DELETE_COMMITTED` event on `view.events`."""
        await self.after_delete_committed(request, obj)
        ctx = AfterDeleteContext(
            event=AdminEvent.AFTER_DELETE_COMMITTED,
            request=request,
            view_key=not_none(self.key),
            pk=pk,
            obj=obj,
        )
        await self.events.emit(ctx)

    async def _emit_before_export(
        self,
        request: Request,
        export_type: BaseExporter,
        items: Sequence[Any],
        export_ctx: "ExportContext",
    ) -> None:
        """Builds the `BeforeExportContext`, calls the `before_export` hook, then emits the event."""
        ctx = BeforeExportContext(
            event=AdminEvent.BEFORE_EXPORT,
            request=request,
            view_key=not_none(self.key),
            export_type=export_type,
            items=items,
            export_ctx=export_ctx,
        )
        await self.before_export(request, export_ctx)
        await self.events.emit(ctx)

    async def _emit_after_export(
        self,
        request: Request,
        export_type: BaseExporter,
        items: Sequence[Any],
        export_ctx: "ExportContext",
    ) -> None:
        """Builds the `AfterExportContext`, calls the `after_export` hook, then emits the event."""
        ctx = AfterExportContext(
            event=AdminEvent.AFTER_EXPORT,
            request=request,
            view_key=not_none(self.key),
            export_type=export_type,
            items=items,
            row_count=len(items),
            export_ctx=export_ctx,
        )
        await self.after_export(request, export_ctx)
        await self.events.emit(ctx)

    async def _emit_before_import(
        self,
        request: Request,
        import_type: BaseImporter,
        import_ctx: "ImportContext",
    ) -> None:
        """Builds the `BeforeImportContext`, calls the `before_import` hook, then emits the event."""
        ctx = BeforeImportContext(
            event=AdminEvent.BEFORE_IMPORT,
            request=request,
            view_key=not_none(self.key),
            import_type=import_type,
            import_ctx=import_ctx,
        )
        await self.before_import(request, import_ctx)
        await self.events.emit(ctx)

    async def _emit_after_import(
        self,
        request: Request,
        import_type: BaseImporter,
        result: "ImportResult",
        import_ctx: "ImportContext",
    ) -> None:
        """Builds the `AfterImportContext`, calls the `after_import` hook with the result, then emits the event."""
        ctx = AfterImportContext(
            event=AdminEvent.AFTER_IMPORT,
            request=request,
            view_key=not_none(self.key),
            import_type=import_type,
            row_count=result.rows_total,
            error_count=len(result.errors),
            import_ctx=import_ctx,
        )
        await self.after_import(request, import_ctx, result)
        await self.events.emit(ctx)

    def can_view_detail(self, request: Request) -> bool:
        """Determines permission for viewing full details of an item. Returns `True` by default."""
        return True

    def can_create(self, request: Request) -> bool:
        """Determines permission for creating new items. Returns `True` by default."""
        return True

    def can_edit(self, request: Request) -> bool:
        """Determines permission for editing items. Returns `True` by default."""
        return True

    def can_delete(self, request: Request) -> bool:
        """Determines permission for deleting items. Returns `True` by default."""
        return True

    def can_export(self, request: Request) -> bool:
        """Determines permission for exporting data. Returns `True` by default."""
        return True

    def can_import(self, request: Request) -> bool:
        """Determines permission for importing data. Returns `True` by default."""
        return True

    def can_access_field(
        self,
        request: Request,
        field: BaseField,
        action: RequestAction | None = None,
    ) -> bool:
        """
        Returns `True` if the requesting user has access to the specified `field` for `action`.

        The default implementation returns ``False`` for fields excluded from
        `action` (e.g., ``exclude_from_list``, ``exclude_from_detail``,
        ``exclude_from_create``, ``exclude_from_edit``) and ``True`` in all other cases.
        Override this method to implement role-based, field-level access control.
        Call ``super()`` to preserve the default exclusion logic:

            def can_access_field(self, request, field, action=None) -> bool:
                if field.name == "salary":
                    return "hr" in request.state.user_roles
                return super().can_access_field(request, field, action)

        This method serves as the single source of truth for field visibility.
        It is invoked by ``get_fields_list`` (which governs every page, including
        list, detail, create, edit, export, and import), by ``_parse_filter_param``
        (where an inaccessible field results in an HTTP 400 error), and by
        ``_parse_list_params`` (where an inaccessible ``sort_by`` parameter also
        results in an HTTP 400 error).

        Parameters:
            request: The request being processed.
            field: The field to check access for.
            action: The action to check access for. Defaults to
                ``request.state.action`` when omitted.
        """
        action = action if action is not None else request.state.action
        return not (
            (
                action in (RequestAction.LIST, RequestAction.RELATION_LOOKUP)
                and field.exclude_from_list
            )
            or (action == RequestAction.EXPORT and field.exclude_from_export)
            or (action == RequestAction.DETAIL and field.exclude_from_detail)
            or (action == RequestAction.CREATE and field.exclude_from_create)
            or (action == RequestAction.IMPORT and field.exclude_from_import)
            or (
                action in (RequestAction.EDIT, RequestAction.INLINE_EDIT)
                and field.exclude_from_edit
            )
        )

    async def serialize_field_value(
        self, value: Any, field: BaseField, request: Request
    ) -> Any:
        """
        Formats the output value for each field.

        !!! important

            The returned value must be JSON serializable.

        Parameters:
            value: The attribute value of an item, as returned by `find_all` or `find_by_pk`.
            field: The Starlette Admin field associated with this attribute.
            request: The request being processed.
        """
        formatter = (field.formatter or {}).get(request.state.action)
        if formatter is not None:
            return await maybe_async(formatter(request, value))
        if value is None:
            return await field.serialize_none_value(request)
        return await field.serialize_value(request, value)

    async def serialize(
        self,
        obj: Any,
        request: Request,
        include_relationships: bool = True,
        include_select2: bool = False,
    ) -> dict[str, Any]:
        obj_serialized: dict[str, Any] = {}
        obj_meta: dict[str, Any] = {}
        for field in self.get_fields_list(request):
            if isinstance(field, RelationField) and not include_relationships:
                continue
            value = await field.parse_obj(request, obj)
            obj_serialized[field.name] = await self.serialize_field_value(
                value, field, request
            )
        if include_select2:
            obj_meta["select2"] = {
                "selection": await self.select2_selection(obj, request),
                "result": await self.select2_result(obj, request),
            }
        obj_meta["repr"] = await self.repr(obj, request)

        # Make sure the primary key is always available
        pk_attr = not_none(self.pk_attr)
        if pk_attr not in obj_serialized:
            pk_value = await self.get_serialized_pk_value(request, obj)
            obj_serialized[pk_attr] = pk_value

        pk = await self.get_pk_value(request, obj)
        obj_meta["detailUrl"] = _detail_url(request, not_none(self.key), pk)
        obj_serialized["_meta"] = obj_meta
        return obj_serialized

    async def repr(self, obj: Any, request: Request) -> str:
        """
        Returns a string representation of the given object, suitable for display in the admin interface.

        If the object defines a custom representation method, `__admin_repr__`, it is used to generate the string.
        Otherwise, the fallback is `"{display_name}({pk})"`.

        Args:
            obj: The object to represent.
            request: The request being processed.

        Example:
            For example, the following implementation for a `User` model displays
            the user's full name instead of their primary key in the admin interface:

            ```python
            class User:
                id: int
                first_name: str
                last_name: str

                def __admin_repr__(self, request: Request):
                    return f"{self.last_name} {self.first_name}"
            ```
        """
        repr_method = getattr(obj, "__admin_repr__", None)
        if repr_method is None:
            pk = await self.get_pk_value(request, obj)
            return f"{self.display_name}({pk})"
        if inspect.iscoroutinefunction(repr_method):
            return await repr_method(request)
        return repr_method(request)

    async def select2_result(self, obj: Any, request: Request) -> str:
        """
        Returns an HTML-formatted string representing the search results for a Select2 search box.

        By default, this method returns a string containing all of the object's attributes,
        excluding relation and file attributes.

        If the object defines a custom representation method, `__admin_select2_repr__`, it is used to generate the
        HTML-formatted string. If that method is not defined but `__admin_repr__` is, its (escaped) return value
        is used instead.

        !!! note

            The returned value must be valid HTML.

        !!! danger

            Escape database values to prevent Cross-Site Scripting (XSS) attacks.
            Consider using Jinja2 Template rendering with `autoescape=True`.
            For more information, refer to the OWASP documentation: [click here](https://owasp.org/www-community/attacks/xss/)

        Parameters:
            obj: The object returned by the `find_all` or `find_by_pk` method.
            request: The request being processed.

        Example:
            Here is an example implementation for a `User` model
            that includes the user's name and photo:

            ```python
            class User:
                id: int
                name: str
                photo_url: str

                def __admin_select2_repr__(self, request: Request) -> str:
                    return f'<div><img src="{escape(photo_url)}"><span>{escape(self.name)}</span></div>'
            ```
        """
        html_repr_method = getattr(obj, "__admin_select2_repr__", None)
        if html_repr_method is not None:
            if inspect.iscoroutinefunction(html_repr_method):
                return await html_repr_method(request)
            return html_repr_method(request)

        if getattr(obj, "__admin_repr__", None) is not None:
            return f"<span>{escape(await self.repr(obj, request))}</span>"

        template_str = (
            "<span>{%for col in fields %}{%if obj[col]%}<strong>{{col}}:"
            " </strong>{{obj[col]}} {%endif%}{%endfor%}</span>"
        )
        display_fields = [
            field
            for field in self.get_fields_list(request)
            if not isinstance(field, (RelationField, FileField))
            and not field.exclude_from_detail
        ]
        "Builds a serialized dictionary so the template receives the same"
        " representation shown elsewhere (e.g., formatted dates, enum labels,"
        " etc.) rather than raw database values."
        display: dict[str, Any] = {}
        for field in display_fields:
            raw_value = await field.parse_obj(request, obj)
            display[field.name] = await self.serialize_field_value(
                raw_value, field, request
            )
        return Template(template_str, autoescape=True).render(
            obj=display, fields=[f.name for f in display_fields]
        )

    async def select2_selection(self, obj: Any, request: Request) -> str:
        """
        Returns the HTML representation of an item selected by a user within a Select2 component.
        By default, this method simply calls `select2_result()`.

        !!! note

            The returned value must be valid HTML.

        !!! danger

            Escape database values to prevent Cross-Site Scripting (XSS) attacks.
            Consider using Jinja2 Template rendering with `autoescape=True`.
            For more information, refer to the OWASP documentation: [click here](https://owasp.org/www-community/attacks/xss/)

        Parameters:
            obj: The item returned by `find_all` or `find_by_pk`.
            request: The request being processed.
        """
        return await self.select2_result(obj, request)

    async def get_pk_value(self, request: Request, obj: Any) -> Any:
        return getattr(obj, not_none(self.pk_attr))

    async def get_serialized_pk_value(self, request: Request, obj: Any) -> Any:
        """
        Returns the serialized value of the primary key.

        !!! note

            The returned value must be JSON-serializable.

        Parameters:
            request: The request being processed.
            obj: The object from which to retrieve the primary key.

        Returns:
            Any: The serialized primary key value.
        """
        return await self.get_pk_value(request, obj)

    def get_fields_list(
        self,
        request: Request,
        *,
        include_nested: bool = False,
        action: RequestAction | None = None,
    ) -> Sequence[BaseField]:
        """
        Returns the fields accessible for `action` based on the request.

        Each field is passed through
        [can_access_field][starlette_admin.views.BaseModelView.can_access_field],
        which handles both the built-in ``exclude_from_*`` flags and any
        role-based overrides. To add per-role field visibility, override
        ``can_access_field`` instead of this method.

        Parameters:
            request: The request being processed.
            include_nested: If ``True``, the method iterates over ``_all_fields``
                 (the flat list of every non-container field at every nesting level,
                 built by ``_init_fields``). If ``False`` (the default), it iterates
                 over ``self.fields`` (the top-level fields only). Use
                 ``include_nested=True`` when you need to access dotted paths,
                 such as ``"config.key"``, for sort or filter validation.
            action: The action to resolve fields for. Defaults to
                ``request.state.action`` when omitted. Pass this to compute the
                field list for an action other than the one currently being
                served, without touching ``request.state.action``.

        During an inline-edit request the inline-edit endpoint sets
        ``request.state.inline_edit_field``, and the list narrows to that
        single field. Every consumer (``validate_fields``, the backend's
        data arrangement and object population, event ``old_data``) then
        reads and writes only the edited field, which is what makes
        ``edit()`` safe to call with a single-field data dict.
        """
        action = action if action is not None else request.state.action
        source = self._all_fields if include_nested else self.fields
        # Set only by the inline-edit endpoint, always as a field-name string.
        inline_edit_field = getattr(request.state, "inline_edit_field", None)
        if isinstance(inline_edit_field, str):
            source = [f for f in source if f.name == inline_edit_field]
        return [f for f in source if self.can_access_field(request, f, action=action)]

    def _field_by_name(self, request: Request, name: str) -> BaseField | None:
        """Returns the accessible field named `name`, or `None` if it does
        not exist or is not accessible for the current request action."""
        return next((f for f in self.get_fields_list(request) if f.name == name), None)

    def resolve_form_layout(
        self,
        request: Request,
        obj: Any = None,
        errors: "Mapping[Any, Any] | None" = None,
    ) -> BaseWidget | None:
        """
        Resolves `form_layout` into a ready-to-render widget tree for the
        current create/edit request.

        Every `FieldRef` leaf is bound to its `BaseField`, current value
        (from `obj`), and validation error (from `errors`); a field hidden
        for the current action or user by
        [can_access_field][starlette_admin.views.BaseModelView.can_access_field]
        is dropped, and any row/column/grid/panel/tab left with nothing
        visible inside it is dropped in turn. A `PanelWidget` left with
        exactly one visible field has that field's `show_label` forced to
        `False`, since the panel title already names it. Static content
        (`HtmlWidget`/`TextWidget`, a custom `BaseWidget` subclass, ...)
        always renders, independent of field visibility. If `form_layout`
        is not set on the view, every field from `get_fields_list` renders,
        one per line, in declaration order, so create/edit forms render
        exactly as they did before `form_layout` existed. Returns `None` if
        nothing ends up visible.

        Parameters:
            request: The request being processed.
            obj: The serialized object supplying current field values, or
                `None` for an empty create form.
            errors: Validation errors keyed by field name, or `None`.
        """
        accessible = {f.name: f for f in self.get_fields_list(request)}
        if not self.form_layout:
            if not accessible:
                return None
            root: BaseWidget = ColumnWidget(
                children=[FieldRef(name) for name in accessible]
            )
        else:
            # `_init_form_layout` normalizes every entry to a `BaseWidget` at
            # instantiation time, so `self.form_layout` here is never a raw
            # top-level `str`/`tuple` shorthand.
            root = ColumnWidget(children=cast("list[BaseWidget]", self.form_layout))
        return _resolve_form_layout_node(root, accessible, obj, errors)

    def _has_array_filter(self, request: Request) -> bool:
        registry = self.get_filter_registry()
        return any(
            f.data_type == FilterDataType.ARRAY
            for field in self.get_fields_list(request)
            for f in registry.filters_for(field)
        )

    def _additional_css_links(self, request: Request) -> Sequence[str]:
        links = self.additional_css_links or []
        for field in self.get_fields_list(request):
            for link in field.additional_css_links(request) or []:
                if link not in links:
                    links.append(link)
        for inline in getattr(self, "_inline_instances", []):
            links.extend(inline._additional_css_links(request))
        if request.state.action == RequestAction.LIST and self._has_array_filter(
            request
        ):
            select2_css = _static_url(request, "css/vendor/select2.min.css", v="4.1.0")
            if select2_css not in links:
                links.append(select2_css)
        return links

    def _additional_js_links(self, request: Request) -> Sequence[str]:
        links = self.additional_js_links or []
        for field in self.get_fields_list(request):
            for link in field.additional_js_links(request) or []:
                if link not in links:
                    links.append(link)
        for inline in getattr(self, "_inline_instances", []):
            links.extend(inline._additional_js_links(request))
        if request.state.action == RequestAction.LIST and self._has_array_filter(
            request
        ):
            select2_js = _static_url(request, "js/vendor/select2.min.js", v="4.1.0")
            if select2_js not in links:
                links.append(select2_js)
        return links

    def get_filter_registry(self) -> FilterRegistry:
        """
        Returns the [FilterRegistry][starlette_admin.filters.FilterRegistry]
        used to determine which filters are available for each field on this
        view's list page. Refer to [BaseField.filters][starlette_admin.fields.BaseField.filters]
        for per-field overrides.

        The base implementation returns an empty registry, meaning fields will not
        have filters unless an explicit `filters` override is declared. Concrete
        ORM `ModelView` implementations populate a registry with their own
        `BaseFilter` implementations (see, for example,
        `starlette_admin.contrib.sqla.ModelView.get_filter_registry`) and override
        this method to return that registry.
        """
        return FilterRegistry()

    def _default_sort(self) -> list[tuple[str, bool]]:
        """
        Returns a list of tuples, ``[(field_name, descending), ...]``, to use when the URL does not
        contain a ``sort`` parameter or when it is invalid. This list is derived
        from the full ``fields_default_sort`` list, with a fallback to the primary key
        if no other sort is specified.
        """
        defaults = self.fields_default_sort or [not_none(self.pk_attr)]
        return [(d, False) if isinstance(d, str) else d for d in defaults]

    def _parse_sorts(
        self,
        raw_sorts: list[str],
        accessible_sortable: set[str],
    ) -> list[tuple[str, Literal["asc", "desc"]]]:
        sorts: list[tuple[str, Literal["asc", "desc"]]] = []
        for raw in raw_sorts:
            if "__" not in raw:
                continue
            field_name, _, direction = raw.rpartition("__")
            direction = direction.lower()
            if field_name in accessible_sortable:
                if direction not in ("asc", "desc"):
                    direction = "asc"
                sorts.append((field_name, direction))
            elif field_name in (self.sortable_fields or []):
                raise HTTPException(
                    HTTP_400_BAD_REQUEST,
                    f"Field {field_name!r} is not accessible",
                )
        return sorts

    def _parse_list_params(
        self, request: Request, query_params: "QueryParams | None" = None
    ) -> ListParams:
        """
        Reads, validates, and sanitizes list-page query parameters (`page`, `page_size`,
        `sort`, `q`) into a [ListParams][starlette_admin.types.ListParams] object.

        Sorting is expressed as repeated ``sort=field__dir`` parameters in the URL
        (e.g., ``?sort=name__asc&sort=date__desc``). Invalid or missing values
        default to the view's configured settings, ensuring the list page never
        errors out due to a malformed URL. Instead, it renders with a sane default state.

        Args:
            request: The request being processed, used for field accessibility
                checks. Its own query params are used unless `query_params` is
                given.
            query_params: Parse params from this mapping instead of
                `request.query_params`. Used by `export_action` to read
                page/page_size/sort out of the list page's query string
                (carried via `_list_query`) rather than the action request's
                own query params.
        """
        query_params = (
            query_params if query_params is not None else request.query_params
        )

        try:
            page = max(int(query_params["page"]), 1)
        except (KeyError, ValueError):
            page = 1

        try:
            page_size = int(query_params["page_size"])
            valid = set(self.page_size_options) | {self.page_size}
            if page_size not in valid:
                raise HTTPException(
                    HTTP_400_BAD_REQUEST,
                    f"Invalid page_size {page_size!r}. Allowed values: {sorted(valid)}",
                )
        except (KeyError, ValueError):
            page_size = self.page_size

        accessible_sortable = {
            f.name
            for f in self.get_fields_list(request, include_nested=True)
            if f.orderable
        }
        sorts = self._parse_sorts(query_params.getlist("sort"), accessible_sortable)
        if not sorts:
            default_sorts: list[tuple[str, Literal["asc", "desc"]]] = [
                (field, "desc" if desc else "asc")
                for field, desc in self._default_sort()
            ]
            sorts = default_sorts

        q = query_params.get("q") or None

        filters = self._parse_filter_param(request, query_params)

        visible_cols: list[str] | None = None
        cols_raw = query_params.get("cols")
        if cols_raw:
            accessible_names = {f.name for f in self.get_fields_list(request)}
            valid_cols = [
                c.strip() for c in cols_raw.split(",") if c.strip() in accessible_names
            ]
            if valid_cols and set(valid_cols) != accessible_names:
                visible_cols = valid_cols

        return ListParams(
            page=page,
            page_size=page_size,
            sorts=sorts,
            q=q,
            filters=filters,
            visible_cols=visible_cols,
        )

    @staticmethod
    def _parse_filter_string(raw: str) -> Any:  # noqa: C901
        """Parse a filter string into a raw dict tree.

        The format (inspired by Django's field lookup syntax) mirrors what
        `filter-builder.js` serialises:
          - Leaf (no value):  ``field__op``
          - Leaf (value):     ``field__op=value``
          - Between:          ``field__op=val..val2``
          - Enum multi-val:   ``field__op=v1,v2,v3``
          - Quoted value:     ``field__op="value with spaces"``
          - Group:            ``rule1 AND rule2`` / ``(rule1 OR rule2)``

        Returns the same dict structure previously used for JSON:
        ``{"logic": …, "rules": […]}`` for groups and
        ``{"field": …, "filter": …, "value": …}`` for leaf rules,
        so ``_build_filter_node`` / ``_build_filter_rule`` need no changes.

        Raises ``ValueError`` on a structurally invalid string.
        """
        max_depth = 20
        pos = [0]
        depth = [0]

        def skip_ws() -> None:
            while pos[0] < len(raw) and raw[pos[0]] in " \t\n\r":
                pos[0] += 1

        def peek_keyword() -> str | None:
            skip_ws()
            rest = raw[pos[0] :].upper()
            for kw in ("AND", "OR"):
                if rest.startswith(kw) and (
                    len(rest) == len(kw) or rest[len(kw)] in " \t\n\r()"
                ):
                    return kw
            return None

        def read_leaf_token() -> str:
            skip_ws()
            result: list[str] = []
            in_value = False
            while pos[0] < len(raw):
                ch = raw[pos[0]]
                if ch == "=":
                    result.append(ch)
                    pos[0] += 1
                    in_value = True
                    continue
                if not in_value and ch in " \t\n\r()":
                    break
                if in_value and ch in " \t\n\r)":
                    break
                if in_value and ch == '"':
                    result.append(ch)
                    pos[0] += 1
                    while pos[0] < len(raw) and raw[pos[0]] != '"':
                        if raw[pos[0]] == "\\" and pos[0] + 1 < len(raw):
                            result.append(raw[pos[0]])
                            pos[0] += 1
                        result.append(raw[pos[0]])
                        pos[0] += 1
                    if pos[0] < len(raw):
                        result.append(raw[pos[0]])
                        pos[0] += 1
                    continue
                result.append(ch)
                pos[0] += 1
            return "".join(result)

        def unquote(v: str) -> str:
            if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
                return v[1:-1].replace('\\"', '"').replace("\\\\", "\\")
            return v

        def split_outside_quotes_once(s: str, sep: str) -> tuple[str, str | None]:
            in_q = False
            for i in range(len(s)):
                if s[i] == '"':
                    in_q = not in_q
                elif not in_q and s[i : i + len(sep)] == sep:
                    return s[:i], s[i + len(sep) :]
            return s, None

        def split_commas_outside_quotes(s: str) -> list[str]:
            parts: list[str] = []
            cur: list[str] = []
            in_q = False
            for ch in s:
                if ch == '"':
                    in_q = not in_q
                    cur.append(ch)
                elif not in_q and ch == ",":
                    parts.append("".join(cur))
                    cur = []
                else:
                    cur.append(ch)
            parts.append("".join(cur))
            return parts

        def parse_leaf(token: str) -> dict[str, Any]:
            eq_idx = token.find("=")
            key = token if eq_idx == -1 else token[:eq_idx]
            value_str: str | None = None if eq_idx == -1 else token[eq_idx + 1 :]

            sep_idx = key.rfind("__")
            if sep_idx == -1 or sep_idx == 0 or sep_idx == len(key) - 2:
                raise ValueError(f"invalid filter leaf (missing '__'): {token!r}")
            field_name = key[:sep_idx]
            op_name = key[sep_idx + 2 :]

            node: dict[str, Any] = {"field": field_name, "filter": op_name}
            if value_str is not None:
                left, right = split_outside_quotes_once(value_str, "..")
                if right is not None:
                    node["value"] = unquote(left)
                    node["value2"] = unquote(right)
                elif "," in value_str:
                    node["value"] = split_commas_outside_quotes(value_str)
                else:
                    node["value"] = unquote(value_str)
            return node

        def parse_term() -> dict[str, Any] | None:
            skip_ws()
            if pos[0] >= len(raw):
                return None
            if raw[pos[0]] == "(":
                if depth[0] >= max_depth:
                    raise ValueError(
                        f"Filter expression exceeds the maximum nesting depth of {max_depth}"
                    )
                pos[0] += 1
                depth[0] += 1
                group = parse_group()
                depth[0] -= 1
                skip_ws()
                if pos[0] < len(raw) and raw[pos[0]] == ")":
                    pos[0] += 1
                return group
            if peek_keyword():
                return None
            token = read_leaf_token()
            return parse_leaf(token) if token else None

        def parse_group() -> dict[str, Any]:
            terms: list[dict[str, Any]] = []
            logic = "and"
            saw_keyword = False
            # Consume a leading keyword so "(AND)" / "(OR)" parses correctly
            kw0 = peek_keyword()
            if kw0:
                logic = kw0.lower()
                pos[0] += len(kw0)
                saw_keyword = True
            term = parse_term()
            if term is None:
                return {"logic": logic, "rules": []}
            terms.append(term)
            while True:
                skip_ws()
                kw = peek_keyword()
                if not kw:
                    break
                saw_keyword = True
                logic = kw.lower()
                pos[0] += len(kw)
                t = parse_term()
                if t is None:
                    break
                terms.append(t)
            if len(terms) == 1 and not saw_keyword:
                return terms[0]
            return {"logic": logic, "rules": terms}

        skip_ws()
        if not raw or pos[0] >= len(raw):
            raise ValueError("empty filter string")
        result = parse_group()
        skip_ws()
        if pos[0] < len(raw):
            raise ValueError(f"unexpected characters in filter: {raw[pos[0] :]!r}")
        return result

    @staticmethod
    def _serialize_filter_string(node: Any) -> str:
        """Serialize a raw filter-tree dict back to a filter string.

        Inverse of ``_parse_filter_string``; used by ``_filter_tree_url``
        to rebuild the ``filter`` query param after removing a chip.
        """
        if isinstance(node, dict) and ("logic" in node or "rules" in node):
            logic = node.get("logic", "and").upper()
            rules = node.get("rules", [])
            parts = []
            for rule in rules:
                part = BaseModelView._serialize_filter_string(rule)
                if isinstance(rule, dict) and ("logic" in rule or "rules" in rule):
                    part = f"({part})"
                parts.append(part)
            return f" {logic} ".join(parts)
        if isinstance(node, dict):
            field = node.get("field", "")
            op = node.get("filter", "")
            base = f"{field}__{op}"
            value = node.get("value")
            value2 = node.get("value2")
            if value is None and value2 is None:
                return base
            if value2 is not None:
                v1 = BaseModelView._quote_filter_value(str(value))
                v2 = BaseModelView._quote_filter_value(str(value2))
                return f"{base}={v1}..{v2}"
            if isinstance(value, list):
                joined = ",".join(
                    BaseModelView._quote_filter_value(str(v)) for v in value
                )
                return f"{base}={joined}"
            return f"{base}={BaseModelView._quote_filter_value(str(value))}"
        return str(node)

    @staticmethod
    def _quote_filter_value(v: str) -> str:
        """Quote a filter value if it contains characters special to the format."""
        if any(c in v for c in ' ()\t\n",') or ".." in v:
            return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return v

    def _parse_filter_param(
        self, request: Request, query_params: Mapping[str, str] | None = None
    ) -> FilterGroup:
        """Deserialise, validate and parse the `filter` query param (the
        filter string the filter builder serialises; see
        [FilterGroup][starlette_admin.filters.FilterGroup]) into a `FilterGroup`
        tree of already-validated, already-parsed
        [FilterRule][starlette_admin.filters.FilterRule]s.

        Unlike the other list params, an invalid `filter` raises
        `HTTPException(400)` rather than silently falling back: silently
        dropping part of a filter would return a misleadingly different result
        set, so we'd rather tell the user their filter is malformed.

        Args:
            request: The request being processed, used for field accessibility
                checks. Its own query params are used unless `query_params` is
                given.
            query_params: Parse `filter` from this mapping instead of
                `request.query_params`. Used by `handle_action` to parse the
                list page's query string (carried via `_list_query`) rather
                than the action request's own query params.
        """
        raw = (query_params or request.query_params).get("filter")
        if not raw:
            return FilterGroup()

        try:
            data = self._parse_filter_string(raw)
        except ValueError as exc:
            raise HTTPException(
                HTTP_400_BAD_REQUEST, f"Invalid 'filter' parameter: {exc}"
            ) from exc

        fields_by_name = {
            f.name: f
            for f in self.get_fields_list(request, include_nested=True)
            if f.searchable
        }
        registry = self.get_filter_registry()
        try:
            node = self._build_filter_node(data, fields_by_name, registry)
        except (FilterValidationError, ValueError, TypeError) as exc:
            raise HTTPException(
                HTTP_400_BAD_REQUEST, f"Invalid 'filter' parameter: {exc}"
            ) from exc
        return node if isinstance(node, FilterGroup) else FilterGroup(rules=[node])

    def _build_filter_node(
        self,
        node: Any,
        fields_by_name: dict[str, BaseField],
        registry: FilterRegistry,
    ) -> FilterGroup | FilterRule:
        """Recursively turn a deserialised JSON node into a `FilterGroup` (for
        `{"logic": ..., "rules": [...]}` nodes) or a validated, parsed
        `FilterRule` (for `{"field": ..., "filter": ..., "value": ...}` leaves,
        delegated to `_build_filter_rule`).

        Raises `ValueError`/`FilterValidationError` (caught by
        `_parse_filter_param`) on any structural or semantic problem: an
        unknown field, a filter slug not available for that field, a missing
        or unparsable value, ...
        """
        if not isinstance(node, dict):
            raise ValueError("each filter node must be a JSON object")

        if "logic" in node or "rules" in node:
            logic = node.get("logic", "and")
            if logic not in ("and", "or"):
                raise ValueError(f"invalid filter logic: {logic!r}")
            rules = node.get("rules")
            if not isinstance(rules, list):
                raise ValueError("'rules' must be a JSON array")
            return FilterGroup(
                logic=logic,
                rules=[
                    self._build_filter_node(rule, fields_by_name, registry)
                    for rule in rules
                ],
            )

        return self._build_filter_rule(node, fields_by_name, registry)

    @staticmethod
    def _build_filter_rule(
        node: dict[str, Any],
        fields_by_name: dict[str, BaseField],
        registry: FilterRegistry,
    ) -> FilterRule:
        """Validate a `{"field": ..., "filter": ..., "value": ...}` leaf against
        `fields_by_name`/`registry`, parse its value(s), and return the
        resulting `FilterRule`. See `_build_filter_node` for error handling.
        """
        field_name = node.get("field")
        if not isinstance(field_name, str) or field_name not in fields_by_name:
            raise ValueError(f"unknown filter field: {field_name!r}")
        field = fields_by_name[field_name]

        filter_slug = node.get("filter")
        filter_cls = (
            registry.get_filter(field, filter_slug)
            if isinstance(filter_slug, str)
            else None
        )
        if filter_cls is None:
            raise ValueError(f"unknown filter {filter_slug!r} for field {field_name!r}")

        filter_instance: BaseFilter = filter_cls()
        value = value2 = None
        if filter_instance.data_type != FilterDataType.NONE:
            if "value" not in node:
                raise ValueError(
                    f"filter {filter_slug!r} on field {field_name!r} requires a value"
                )
            value = filter_instance.parse_value(node["value"])
            if filter_instance.has_value2:
                if "value2" not in node:
                    raise ValueError(
                        f"filter {filter_slug!r} on field {field_name!r} requires a second value"
                    )
                value2 = filter_instance.parse_value(node["value2"])

        assert isinstance(filter_slug, str)
        return FilterRule(
            field=field_name, filter=filter_slug, value=value, value2=value2
        )

    def _active_filter_chips(
        self, request: Request, list_params: ListParams
    ) -> tuple[str, list[FilterChip]]:
        """Build the active-filter pills shown by `_filter_bar.html`, one per
        top-level rule/group in the `filter` query param tree (already known,
        via `list_params.filters.is_empty()`, to be non-empty and valid).

        Walks the re-parsed raw filter string rather than `list_params.filters`:
        a pill's `remove_url` is the current filter tree re-serialized with that
        one entry dropped, preserving raw string values exactly as they arrived
        (the parsed `FilterRule.value` may be a `date`/`Decimal`/… that
        `apply()` needs but the URL format can't losslessly represent;
        see [FilterChip][starlette_admin.types.FilterChip]).

        Nested AND/OR sub-groups (buildable via the filter builder's "Add
        group" control, or by hand-building the URL) collapse into a single
        removable-as-a-whole pill rather than exposing their individual rules.
        A sub-group reads as one composite filter, which avoids the
        complexity of in-place editing of nested trees from the bar (the
        builder dropdown remains the place to edit a sub-group's rules).
        """
        if list_params.filters.is_empty():
            return "and", []
        try:
            data = self._parse_filter_string(
                not_none(request.query_params.get("filter"))
            )
        except ValueError:
            return "and", []

        if isinstance(data, dict) and ("logic" in data or "rules" in data):
            logic = data.get("logic", "and")
            rules = data.get("rules", [])
        else:
            logic, rules = "and", [data]
        if not isinstance(rules, list):
            return "and", []

        fields_by_name = {
            getattr(f, "_name", f.name): f
            for f in self.get_fields_list(request, include_nested=True)
            if f.searchable
        }
        registry = self.get_filter_registry()
        return logic, [
            FilterChip(
                label=self._describe_filter_node(
                    node, fields_by_name, registry, request
                ),
                remove_url=self._filter_tree_url(
                    request, logic, rules[:i] + rules[i + 1 :]
                ),
            )
            for i, node in enumerate(rules)
        ]

    @staticmethod
    def _describe_filter_node(
        node: Any,
        fields_by_name: dict[str, BaseField],
        registry: FilterRegistry,
        request: Request,
    ) -> str:
        """Human-readable description of a raw filter-tree node for its pill
        label: `"{field}: {filter} {value}"` for a leaf rule (only the
        `{field}: {filter}` part when the filter takes no value, eg.
        "is empty"), or, for a group, its children's descriptions joined by
        `" AND "`/`" OR "` per `logic`, with nested sub-groups wrapped in
        parentheses. This renders the *exact* boolean expression that was
        built (eg. `"Title: Contains a AND (Body: Contains b OR Tags: Is
        empty)"`) rather than a vague "N grouped filters" summary; precise
        even for a top-level group pill, which is shown unparenthesized since
        it's already the whole expression.

        A leaf's raw value(s) are resolved to their display label(s) when
        the filter carries choices, via
        [BaseFilter.get_choices][starlette_admin.filters.BaseFilter.get_choices]
        or (for a plain `EnumField` filter with no choices of its own) the
        field's own choices, mirroring the precedence `_filter_builder_fields`
        uses for the value picker itself.
        """
        if not isinstance(node, dict):
            return str(node)

        if "logic" in node or "rules" in node:
            logic = node.get("logic", "and")
            rules = node.get("rules")
            if not isinstance(rules, list) or not rules:
                return ""
            joiner = gettext(" AND ") if logic != "or" else gettext(" OR ")
            parts = []
            for rule in rules:
                desc = BaseModelView._describe_filter_node(
                    rule, fields_by_name, registry, request
                )
                parts.append(desc)
            return f"({joiner.join(parts)})"

        field = fields_by_name.get(node.get("field"))  # type: ignore[arg-type]
        field_label = field.label if field is not None else node.get("field")
        filter_cls = (
            registry.get_filter(field, node.get("filter"))  # type: ignore[arg-type]
            if field is not None
            else None
        )
        filter_label = (
            filter_cls.label if filter_cls is not None else node.get("filter")
        )
        if filter_cls is not None and filter_cls.data_type == FilterDataType.NONE:
            return f"{field_label}: {filter_label}"

        labels = BaseModelView._filter_value_labels(field, filter_cls, request)

        def display(value: Any) -> str:
            if value is None:
                return ""
            return str(labels.get(str(value), value)) if labels else str(value)

        if filter_cls is not None and filter_cls.has_value2:
            return (
                f"{field_label}: {filter_label} "
                f"{display(node.get('value'))} - {display(node.get('value2'))}"
            )
        value = node.get("value")
        value_str = (
            ", ".join(display(v) for v in value)
            if isinstance(value, list)
            else display(value)
        )
        return f"{field_label}: {filter_label} {value_str}"

    @staticmethod
    def _filter_value_labels(
        field: BaseField | None,
        filter_cls: type[BaseFilter] | None,
        request: Request,
    ) -> dict[str, Any] | None:
        """Map a filter's raw string values to their display labels, for
        `_describe_filter_node`'s value pill. `None` when neither the filter
        nor the field supplies choices, so `display()` falls back to the raw
        value unchanged.
        """
        choices = filter_cls().get_choices(request) if filter_cls is not None else None
        if not choices and isinstance(field, EnumField):
            choices = field._get_choices(request)
        return {str(v): label for v, label in choices} if choices else None

    @staticmethod
    def _filter_tree_url(request: Request, logic: str, rules: list[Any]) -> str:
        """List URL with the `filter` query param set to the filter string for
        ``{logic, rules}`` (or dropped when ``rules`` is empty), every other
        list-state param preserved. Used for filter-pill removal.
        """
        if not rules:
            return list_url(request, filter=None, page=None)
        tree = BaseModelView._serialize_filter_string({"logic": logic, "rules": rules})
        return list_url(request, filter=tree, page=None)

    def _filter_builder_fields(self, request: Request) -> list[dict[str, Any]]:
        """Per-field filter metadata for `_filter_builder.html`'s client-side
        row builder: for each field that has at least one available filter,
        its name/label and the `{name, label, data_type, has_value2, choices?}`
        of each filter, serialised to JSON (`| tojson`) so `filter-builder.js`
        can populate the filter dropdown and the right value input(s) for
        whichever field/filter the user picks, without a round-trip.

        A filter carries its own `choices` when
        [BaseFilter.get_choices][starlette_admin.filters.BaseFilter.get_choices]
        returns a non-empty result, taking precedence over the field-level
        `choices` set below for `EnumField`.
        """
        registry = self.get_filter_registry()
        result = []
        for f in self.get_fields_list(request, include_nested=True):
            if not f.searchable:
                continue
            available = registry.filters_for(f)
            if available:
                filters_data = []
                for fc in available:
                    filter_data: dict[str, Any] = {
                        "name": fc.name,
                        "label": fc.label,
                        "data_type": fc.data_type.value,
                        "has_value2": fc.has_value2,
                    }
                    choices = fc().get_choices(request)
                    if choices:
                        filter_data["choices"] = [
                            [str(v), str(label)] for v, label in choices
                        ]
                    filters_data.append(filter_data)
                field_data: dict[str, Any] = {
                    "name": f.name,
                    "label": f.label,
                    "filters": filters_data,
                }
                if isinstance(f, EnumField):
                    field_data["choices"] = [
                        [str(v), str(label)] for v, label in f._get_choices(request)
                    ]
                result.append(field_data)
        return result


class DefaultIndexView(CustomView):
    """Ready-made home page with a welcome banner and per-view panels.

    Layout (all built from widgets):

    - **Row 1**: an ``HtmlWidget`` with a welcome message.
    - **Per view**: a ``PanelWidget`` (with the view's icon if set) containing
      the total record count as text and an ``HtmlWidget`` info alert with
      "View all" and "Create new" links.

    Pass this (or a subclass) as ``index_view`` to ``BaseAdmin`` to customise
    it; the admin creates one automatically when ``index_view`` is not supplied.

    Args:
        model_views: Live reference to the admin's ``_model_views`` list.
            Views added after construction are automatically visible because
            the list is shared by reference.
        app_title: The admin application title, injected by ``BaseAdmin`` at
            construction time. Used in the auto-generated welcome heading.
        welcome_text: HTML string shown at the top of the page. When ``None``
            (the default) a heading is generated automatically.
    """

    def __init__(
        self,
        model_views: list["BaseModelView"],
        env: Environment,
        app_title: str = "Admin",
        welcome_text: "str | None" = None,
    ) -> None:
        self._model_views = model_views
        self.env = env
        self.app_title = app_title
        self.welcome_text = welcome_text
        super().__init__(
            menu_label="",
            route_name="index",
            add_to_menu=False,
            widget=self._build_widget,
        )

    async def _build_widget(self, request: Request) -> BaseWidget | None:
        accessible = [v for v in self._model_views if v.is_accessible(request)]
        if not accessible:
            return HtmlWidget(html=f"<p>{_('No data views are available.')}</p>")

        # Row 1: welcome banner
        if self.welcome_text is None:
            welcome_html = f"<h2>{_('Welcome to')} {self.app_title}</h2>"
        else:
            welcome_html = self.welcome_text
        welcome = HtmlWidget(html=welcome_html)

        # One panel per view
        panels: list[BaseWidget] = [
            await self._build_view_panel(request, view) for view in accessible
        ]

        return ColumnWidget(children=[welcome, *panels])

    async def _build_view_panel(
        self, request: Request, view: "BaseModelView"
    ) -> BaseWidget:
        list_href = _view_list_url(request, cast(str, view.key))
        create_href = _create_url(request, cast(str, view.key))

        try:
            count = await view.count(request)
            count_text = str(count)
        except Exception:
            _log.warning(
                "DefaultIndexView: count() failed for view %r",
                view.key,
                exc_info=True,
            )
            count_text = "?"

        _html = (
            f"<p><strong>{count_text}</strong> {_('total records')}</p>"
            f'<p>{_("Browse")} <a href="{escape(list_href)}">{_("all records")}</a>'
            f' {_("or add a")} <a href="{escape(create_href)}">{_("new one")}</a>.</p>'
        )

        return PanelWidget(
            title=view.menu_label,
            icon=view.icon or "",
            children=[
                HtmlWidget(html=_html),
            ],
        )


class InlineModelView(BaseModelView):
    """Inline editing of related records inside a parent model's create/edit form.

    Like Django's ``TabularInline``/``StackedInline``, an inline lets users
    create, update and delete related objects without leaving the parent page.

    Example:
        ```python
        class OrderItemInline(InlineModelView):
            model = OrderItem
            fk_attr = "order_id"
            fields = [IntegerField("id"), StringField("sku"), IntegerField("qty")]

        class OrderView(ModelView):
            model = Order
            fields = [IntegerField("id"), StringField("customer")]
            inlines = [OrderItemInline]
        ```

    Concrete ORM backends subclass this and implement `find_by_parent`, while
    inheriting the normal `BaseModelView` create/edit/delete/find_by_pk
    contract for individual rows.

    Attributes:
        fk_attr: Name of the foreign-key field on the inline model that points
            to the parent.
        extra: Number of extra empty inline rows to show on create/edit forms.
        allow_delete: Whether inline rows can be deleted from the parent form.
        inline_template: Template used to render the inline formset.
        collapsible: Whether the formset can be expanded/collapsed by the
            user.
        collapsed: Initial collapsed state. Only meaningful when
            `collapsible` is `True`.
    """

    fk_attr: str | tuple[str, ...] = ""
    extra: int = 0
    allow_delete: bool = True
    inline_template: str = "inline.html"
    collapsible: bool = True
    collapsed: bool = False
    parent_view: Optional["BaseModelView"] = None

    def __init__(self, parent_view: Optional["BaseModelView"] = None) -> None:
        self.parent_view = parent_view
        if not self.fk_attr:
            raise ValueError(
                f"{type(self).__name__} must define a foreign-key attribute "
                "via `fk_attr`"
            )
        super().__init__()

    @abstractmethod
    async def find_by_parent(self, request: Request, parent: Any) -> Sequence[Any]:
        """Return all inline rows belonging to *parent*.

        Parameters:
            request: The request being processed.
            parent: The parent model instance.

        Returns:
            Sequence of inline model instances.
        """
        raise NotImplementedError()

    def _find_foreign_view(self, key: str) -> "BaseModelView":
        """Delegate foreign-view lookup to the parent view.

        RelationField.serialize_value calls ``self._view._find_foreign_view``
        and ``self._view`` is this inline, so we need to forward the call to
        the parent which has the real admin registry.
        """
        if self.parent_view is None:
            raise RuntimeError(
                "InlineModelView._find_foreign_view called before the inline "
                "was wired to a parent view"
            )
        return self.parent_view._find_foreign_view(key)

    def _get_fk_attr(self) -> str | tuple[str, ...]:
        """Return the effective FK attr(s).

        Override in ORM-specific subclasses to support auto-detection.
        """
        return self.fk_attr

    async def build_fk_value(self, request: Request, parent: Any) -> Any:
        """Return the value to store in `fk_attr` for newly created inline rows.

        For a single `fk_attr` (string), the default returns the parent's PK.
        For a composite `fk_attr` (tuple of strings), override this method to
        return a ``dict`` mapping each child FK attribute name to its value.
        ORM-specific subclasses (e.g. ``sqla.InlineModelView``) provide this
        automatically via FK constraint introspection.
        """
        if self.parent_view is None:
            raise RuntimeError(
                "InlineModelView.build_fk_value called before the inline "
                "was wired to a parent view"
            )
        return await self.parent_view.get_pk_value(request, parent)

    def _prefix(self) -> str:
        """Form field prefix for this inline formset."""
        return f"inlines.{self.key}"

    def set_row_field_ids(self, index: int) -> str:
        """Update `id` of every field so inputs are namespaced under
        ``inlines.<key>.<index>.<field_name>``.

        Called by the inline templates before rendering each row. Collection
        fields re-propagate their nested ids. Returns an empty string so it
        can be invoked directly inside ``{{ }}`` without printing anything.
        """
        prefix = self._prefix()
        for field in self.fields:
            field.id = f"{prefix}.{index}.{field.name}"
            if isinstance(field, CollectionField):
                field._propagate_id()
        return ""
