import inspect
from abc import abstractmethod
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

from jinja2 import Template
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin._types import ExportType, RequestAction
from starlette_admin.actions import action
from starlette_admin.exceptions import ActionFailed
from starlette_admin.fields import (
    BaseField,
    CollectionField,
    FileField,
    HasOne,
    RelationField,
)
from starlette_admin.helpers import extract_fields
from starlette_admin.i18n import get_locale, ngettext
from starlette_admin.i18n import lazy_gettext as _


class BaseView:
    """
    Base class for all views

    Attributes:
        label: Label of the view to be displayed.
        icon: Icon to be displayed for this model in the admin. Only FontAwesome names are supported.
    """

    label: str = ""
    icon: Optional[str] = None

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
        ```Python
        admin.add_view(
            DropDown(
                "Resources",
                icon="fa fa-list",
                views=[
                    ModelView(User),
                    Link(label="Home Page", url="/"),
                    CustomView(label="Dashboard", path="/dashboard", template_path="dashboard.html"),
                ],
            )
        )
        ```
    """

    def __init__(
        self,
        label: str,
        views: List[Union[Type[BaseView], BaseView]],
        icon: Optional[str] = None,
        always_open: bool = True,
    ) -> None:
        self.label = label
        self.icon = icon
        self.always_open = always_open
        self.views: List[BaseView] = [
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
        ```Python
        admin.add_view(Link(label="Home Page", icon="fa fa-link", url="/"))
        ```
    """

    def __init__(
        self,
        label: str = "",
        icon: Optional[str] = None,
        url: str = "/",
        target: Optional[str] = "_self",
    ):
        self.label = label
        self.icon = icon
        self.url = url
        self.target = target


class CustomView(BaseView):
    """
    Add your own views (not tied to any particular model). For example,
    a custom home page that displays some analytics data.

    Attributes:
        path: Route path
        template_path: Path to template file
        methods: HTTP methods
        name: Route name
        add_to_menu: Display to menu or not

    Example:
        ```Python
        admin.add_view(CustomView(label="Home", icon="fa fa-home", path="/home", template_path="home.html"))
        ```
    """

    def __init__(
        self,
        label: str,
        icon: Optional[str] = None,
        path: str = "/",
        template_path: str = "index.html",
        name: Optional[str] = None,
        methods: Optional[List[str]] = None,
        add_to_menu: bool = True,
    ):
        self.label = label
        self.icon = icon
        self.path = path
        self.template_path = template_path
        self.name = name
        self.methods = methods
        self.add_to_menu = add_to_menu

    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        """Default methods to render view. Override this methods to add your custom logic."""
        return templates.TemplateResponse(self.template_path, {"request": request})

    def is_active(self, request: Request) -> bool:
        return request.scope["path"] == self.path


class BaseModelView(BaseView):
    """
    Base administrative view.
    Derive from this class to implement your administrative interface piece.

    Attributes:
        identity: Unique identity to identify the model associated to this view.
            Will be used for URL of the endpoints.
        name: Name of the view to be displayed
        fields: List of fields
        pk_attr: Primary key field name
        form_include_pk: Indicate if the primary key should be excluded from create and
            edit. Default to True
        exclude_fields_from_list: List of fields to exclude in List page.
        exclude_fields_from_detail: List of fields to exclude in Detail page.
        exclude_fields_from_create: List of fields to exclude from creation page.
        exclude_fields_from_edit: List of fields to exclude from editing page.
        searchable_fields: List of searchable fields.
        sortable_fields: List of sortable fields.
        export_fields: List of fields to include in exports.
        fields_default_sort: Initial order (sort) to apply to the table.
            eg: `["title", ("price", True)]`.
        export_types: A list of available export filetypes. Available
            exports are `['csv', 'excel', 'pdf', 'print']`. Only `pdf` is
            disabled by default.
        column_visibility: Enable/Disable
            [column visibility](https://datatables.net/extensions/buttons/built-in#Column-visibility)
            extension
        search_builder: Enable/Disable [search builder](https://datatables.net/extensions/searchbuilder/)
            extension
        page_size: Default number of items to display in List page pagination.
            Default value is set to `10`.
        page_size_options: Pagination choices displayed in List page.
            Default value is set to `[10, 25, 50, 100]`. Use `-1`to display All
        responsive_table: Enable/Disable [responsive](https://datatables.net/extensions/responsive/)
            extension
        list_template: List view template. Default is `list.html`.
        detail_template: Details view template. Default is `details.html`.
        create_template: Edit view template. Default is `edit.html`.
        edit_template: Edit view template. Default is `edit.html`.
        actions: List of actions

    """

    identity: Optional[str] = None
    name: Optional[str] = None
    fields: Sequence[BaseField] = []
    pk_attr: Optional[str] = None
    form_include_pk: bool = False
    exclude_fields_from_list: Sequence[str] = []
    exclude_fields_from_detail: Sequence[str] = []
    exclude_fields_from_create: Sequence[str] = []
    exclude_fields_from_edit: Sequence[str] = []
    searchable_fields: Optional[Sequence[str]] = None
    sortable_fields: Optional[Sequence[str]] = None
    fields_default_sort: Optional[Sequence[Union[Tuple[str, bool], str]]] = None
    export_types: Sequence[ExportType] = [
        ExportType.CSV,
        ExportType.EXCEL,
        ExportType.PRINT,
    ]
    export_fields: Optional[Sequence[str]] = None
    column_visibility: bool = True
    search_builder: bool = True
    page_size: int = 10
    page_size_options: Sequence[int] = [10, 25, 50, 100]
    responsive_table: bool = False
    list_template: str = "list.html"
    detail_template: str = "detail.html"
    create_template: str = "create.html"
    edit_template: str = "edit.html"
    actions: Optional[Sequence[str]] = None

    _find_foreign_model: Callable[[str], "BaseModelView"]

    def __init__(self) -> None:  # noqa: C901
        fringe = list(self.fields)
        all_field_names = []
        while len(fringe) > 0:
            field = fringe.pop(0)
            if not hasattr(field, "_name"):
                field._name = field.name  # type: ignore
            if isinstance(field, CollectionField):
                for f in field.fields:
                    f._name = f"{field._name}.{f.name}"  # type: ignore
                fringe.extend(field.fields)
            name = field._name  # type: ignore
            if name == self.pk_attr and not self.form_include_pk:
                field.exclude_from_create = True
                field.exclude_from_edit = True
            if name in self.exclude_fields_from_list:
                field.exclude_from_list = True
            if name in self.exclude_fields_from_detail:
                field.exclude_from_detail = True
            if name in self.exclude_fields_from_create:
                field.exclude_from_create = True
            if name in self.exclude_fields_from_edit:
                field.exclude_from_edit = True
            if not isinstance(field, CollectionField):
                all_field_names.append(name)
                field.searchable = (self.searchable_fields is None) or (
                    name in self.searchable_fields
                )
                field.orderable = (self.sortable_fields is None) or (
                    name in self.sortable_fields
                )
        if self.searchable_fields is None:
            self.searchable_fields = all_field_names[:]
        if self.sortable_fields is None:
            self.sortable_fields = all_field_names[:]
        if self.export_fields is None:
            self.export_fields = all_field_names[:]
        if self.fields_default_sort is None:
            self.fields_default_sort = [self.pk_attr]  # type: ignore[list-item]

        # Actions
        self._actions: Dict[str, Dict[str, str]] = {}
        self._handlers: Dict[str, Callable[[Request, Sequence[Any]], Awaitable]] = {}
        self._init_actions()

    def is_active(self, request: Request) -> bool:
        return request.path_params.get("identity", None) == self.identity

    def _init_actions(self) -> None:
        """
        Initialize list of actions
        """
        for _method_name, method in inspect.getmembers(
            self, predicate=inspect.ismethod
        ):
            if hasattr(method, "_action"):
                name = method._action.get("name")
                self._actions[name] = method._action
                self._handlers[name] = method
        if self.actions is None:
            self.actions = list(self._handlers.keys())
        for action_name in self.actions:
            if action_name not in self._actions:
                raise ValueError(f"Unknown action with name `{action_name}`")

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
        return True

    async def get_all_actions(self, request: Request) -> List[Optional[dict]]:
        actions = []
        assert self.actions is not None
        for action_name in self.actions:
            if await self.is_action_allowed(request, action_name):
                actions.append(self._actions.get(action_name))
        return actions

    async def handle_action(self, request: Request, pks: List[Any], name: str) -> str:
        """
        Handle action with `name`.
        Raises:
            ActionFailed: to display meaningfully error
        """
        handler = self._handlers.get(name, None)
        if handler is None:
            raise ActionFailed("Invalid action")
        if not await self.is_action_allowed(request, name):
            raise ActionFailed("Forbidden")
        return await handler(request, pks)

    @action(
        name="delete",
        text=_("Delete"),
        confirmation=_("Are you sure you want to delete selected items?"),
        submit_btn_text=_("Yes, delete all"),
        submit_btn_class="btn-danger",
    )
    async def delete_action(self, request: Request, pks: List[Any]) -> str:
        affected_rows = await self.delete(request, pks)
        return ngettext(
            "Item was successfully deleted",
            "%(count)d items were successfully deleted",
            affected_rows or 0,
        ) % {"count": affected_rows}

    @abstractmethod
    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        """
        Find all items
        Parameters:
            request: The request being processed
            where: Can be dict for complex query
                ```json
                 {"and":[{"id": {"gt": 5}},{"name": {"startsWith": "ban"}}]}
                ```
                or plain text for full search
            skip: should return values start from position skip+1
            limit: number of maximum items to return
            order_by: order data clauses in form `["id asc", "name desc"]`
        """
        raise NotImplementedError()

    @abstractmethod
    async def count(
        self,
        request: Request,
        where: Union[Dict[str, Any], str, None] = None,
    ) -> int:
        """
        Count items
        Parameters:
            request: The request being processed
            where: Can be dict for complex query
                ```json
                 {"and":[{"id": {"gt": 5}},{"name": {"startsWith": "ban"}}]}
                ```
                or plain text for full search
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        """
        Bulk delete items
        Parameters:
            request: The request being processed
            pks: List of primary keys
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
    async def find_by_pks(self, request: Request, pks: List[Any]) -> Sequence[Any]:
        """
        Find many items
        Parameters:
            request: The request being processed
            pks: List of Primary key
        """
        raise NotImplementedError()

    @abstractmethod
    async def create(self, request: Request, data: Dict) -> Any:
        """
        Create item
        Parameters:
            request: The request being processed
            data: Dict values contained converted form data
        Returns:
            Any: Created Item
        """
        raise NotImplementedError()

    @abstractmethod
    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        """
        Edit item
        Parameters:
            request: The request being processed
            pk: Primary key
            data: Dict values contained converted form data
        Returns:
            Any: Edited Item
        """
        raise NotImplementedError()

    def can_view_details(self, request: Request) -> bool:
        """Permission for viewing full details of Item. Return True by default"""
        return True

    def can_create(self, request: Request) -> bool:
        """Permission for creating new Items. Return True by default"""
        return True

    def can_edit(self, request: Request) -> bool:
        """Permission for editing Items. Return True by default"""
        return True

    def can_delete(self, request: Request) -> bool:
        """Permission for deleting Items. Return True by default"""
        return True

    async def serialize_field_value(
        self, value: Any, field: BaseField, action: RequestAction, request: Request
    ) -> Any:
        """
        Format output value for each field.

        !!! important
            The returned value should be json serializable

        Parameters:
            value: attribute of item returned by `find_all` or `find_by_pk`
            field: Starlette Admin field for this attribute
            action: Specify where the data will be used. Possible values are
                `VIEW` for detail page, `EDIT` for editing page and `API`
                for listing page and select2 data.
            request: The request being processed
        """
        if value is None:
            return await field.serialize_none_value(request, action)
        return await field.serialize_value(request, value, action)

    async def serialize(
        self,
        obj: Any,
        request: Request,
        action: RequestAction,
        include_relationships: bool = True,
        include_select2: bool = False,
    ) -> Dict[str, Any]:
        obj_serialized: Dict[str, Any] = {}
        for field in self.fields:
            if isinstance(field, RelationField) and include_relationships:
                value = getattr(obj, field.name, None)
                foreign_model = self._find_foreign_model(field.identity)  # type: ignore
                assert foreign_model.pk_attr is not None
                if value is None:
                    obj_serialized[field.name] = None
                elif isinstance(field, HasOne):
                    if action == RequestAction.EDIT:
                        obj_serialized[field.name] = getattr(
                            value, foreign_model.pk_attr
                        )
                    else:
                        obj_serialized[field.name] = await foreign_model.serialize(
                            value, request, action, include_relationships=False
                        )
                else:
                    if action == RequestAction.EDIT:
                        obj_serialized[field.name] = [
                            getattr(v, foreign_model.pk_attr) for v in value
                        ]
                    else:
                        obj_serialized[field.name] = [
                            await foreign_model.serialize(
                                v, request, action, include_relationships=False
                            )
                            for v in value
                        ]
            elif not isinstance(field, RelationField):
                value = await field.parse_obj(request, obj)
                obj_serialized[field.name] = await self.serialize_field_value(
                    value, field, action, request
                )
        if include_select2:
            obj_serialized["_select2_selection"] = await self.select2_selection(
                obj, request
            )
            obj_serialized["_select2_result"] = await self.select2_result(obj, request)
        obj_serialized["_repr"] = await self.repr(obj, request)
        assert self.pk_attr is not None
        pk = getattr(obj, self.pk_attr)
        obj_serialized[self.pk_attr] = obj_serialized.get(
            self.pk_attr, str(pk)  # Make sure the primary key is always available
        )
        route_name = request.app.state.ROUTE_NAME
        obj_serialized["_detail_url"] = str(
            request.url_for(route_name + ":detail", identity=self.identity, pk=pk)
        )
        obj_serialized["_edit_url"] = str(
            request.url_for(route_name + ":edit", identity=self.identity, pk=pk)
        )
        return obj_serialized

    async def repr(self, obj: Any, request: Request) -> str:
        """Return a string representation of the given object that can be displayed in the admin interface.

        If the object has a custom representation method `__admin_repr__`, it is used to generate the string. Otherwise,
        the value of the object's primary key attribute is used.

        Args:
            obj: The object to represent.
            request: The request being processed

        Example:
            For example, the following implementation for a `User` model will display
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
        repr_method = getattr(
            obj,
            "__admin_repr__",
            lambda request: str(getattr(obj, self.pk_attr)),  # type: ignore[arg-type]
        )
        if inspect.iscoroutinefunction(repr_method):
            return await repr_method(request)
        return repr_method(request)

    async def select2_result(self, obj: Any, request: Request) -> str:
        """Returns an HTML-formatted string that represents the search results for a Select2 search box.

        By default, this method returns a string that contains all the object's attributes in a list except
        relation and file attributes.

        If the object has a custom representation method `__admin_select2_repr__`, it is used to generate the
        HTML-formatted string.

        !!! note
            The returned value should be valid HTML.

        !!! danger
            Escape your database value to avoid Cross-Site Scripting (XSS) attack.
            You can use Jinja2 Template render with `autoescape=True`.
            For more information [click here](https://owasp.org/www-community/attacks/xss/)

        Parameters:
            obj: The object returned by the `find_all` or `find_by_pk` method.
            request: The request being processed

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
        template_str = (
            "<span>{%for col in fields %}{%if obj[col]%}<strong>{{col}}:"
            " </strong>{{obj[col]}} {%endif%}{%endfor%}</span>"
        )
        fields = [
            field.name
            for field in self.fields
            if (
                not isinstance(field, (RelationField, FileField))
                and not field.exclude_from_detail
            )
        ]
        html_repr_method = getattr(
            obj,
            "__admin_select2_repr__",
            lambda request: Template(template_str, autoescape=True).render(
                obj=obj, fields=fields
            ),
        )
        if inspect.iscoroutinefunction(html_repr_method):
            return await html_repr_method(request)
        return html_repr_method(request)

    async def select2_selection(self, obj: Any, request: Request) -> str:
        """
        Returns the HTML representation of an item selected by a user in a Select2 component.
        By default, it simply calls `select2_result()`.

        !!! note
            The returned value should be valid HTML.

        !!! danger
            Escape your database value to avoid Cross-Site Scripting (XSS) attack.
            You can use Jinja2 Template render with `autoescape=True`.
            For more information [click here](https://owasp.org/www-community/attacks/xss/)

        Parameters:
            obj: item returned by `find_all` or `find_by_pk`
            request: The request being processed

        """
        return await self.select2_result(obj, request)

    def _length_menu(self) -> Any:
        return [
            self.page_size_options,
            [(_("All") if i < 0 else i) for i in self.page_size_options],
        ]

    def _search_columns_selector(self) -> List[str]:
        return ["%s:name" % name for name in self.searchable_fields]  # type: ignore

    def _export_columns_selector(self) -> List[str]:
        return ["%s:name" % name for name in self.export_fields]  # type: ignore

    def get_fields_list(
        self,
        request: Request,
        action: RequestAction = RequestAction.LIST,
    ) -> Sequence[BaseField]:
        """Return a list of field instances to display in the specified view action.
        This function excludes fields with corresponding exclude flags, which are
        determined by the `exclude_fields_from_*` attributes.

        Parameters:
             request: The request being processed.
             action: The type of action being performed on the view.
        """
        return extract_fields(self.fields, action)

    def _additional_css_links(
        self, request: Request, action: RequestAction
    ) -> Sequence[str]:
        links = []
        for field in self.fields:
            if (
                (action == RequestAction.LIST and field.exclude_from_list)
                or (action == RequestAction.DETAIL and field.exclude_from_detail)
                or (action == RequestAction.CREATE and field.exclude_from_create)
                or (action == RequestAction.EDIT and field.exclude_from_edit)
            ):
                continue
            for link in field.additional_css_links(request, action) or []:
                if link not in links:
                    links.append(link)
        return links

    def _additional_js_links(
        self, request: Request, action: RequestAction
    ) -> Sequence[str]:
        links = []
        for field in self.fields:
            if (action == RequestAction.CREATE and field.exclude_from_create) or (
                action == RequestAction.EDIT and field.exclude_from_edit
            ):
                continue
            for link in field.additional_js_links(request, action) or []:
                if link not in links:
                    links.append(link)
        return links

    async def _configs(self, request: Request) -> Dict[str, Any]:
        locale = get_locale()
        return {
            "label": self.label,
            "pageSize": self.page_size,
            "lengthMenu": self._length_menu(),
            "searchColumns": self._search_columns_selector(),
            "exportColumns": self._export_columns_selector(),
            "fieldsDefaultSort": dict(
                (it, False) if isinstance(it, str) else it
                for it in self.fields_default_sort  # type: ignore[union-attr]
            ),
            "exportTypes": self.export_types,
            "columnVisibility": self.column_visibility,
            "searchBuilder": self.search_builder,
            "responsiveTable": self.responsive_table,
            "fields": [f.dict() for f in self.get_fields_list(request)],
            "actions": await self.get_all_actions(request),
            "pk": self.pk_attr,
            "locale": locale,
            "apiUrl": request.url_for(
                f"{request.app.state.ROUTE_NAME}:api", identity=self.identity
            ),
            "actionUrl": request.url_for(
                f"{request.app.state.ROUTE_NAME}:action", identity=self.identity
            ),
            "dt_i18n_url": request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics", path=f"i18n/dt/{locale}.json"
            ),
        }
