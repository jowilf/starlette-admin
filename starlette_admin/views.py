from abc import abstractmethod
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Type, Union

from jinja2 import Template
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin._types import ExportType, RequestAction
from starlette_admin.fields import (
    BaseField,
    CollectionField,
    FileField,
    HasOne,
    RelationField,
)
from starlette_admin.helpers import extract_fields


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
        return any([v.is_active(request) for v in self.views])

    def is_accessible(self, request: Request) -> bool:
        return any([v.is_accessible(request) for v in self.views])


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
        export_types: A list of available export filetypes. Available
            exports are `['csv', 'excel', 'pdf', 'print']`. All of them are activated
            by default.
        column_visibility: Control column visibility button
        search_builder: Control search builder button
        page_size: Default number of items to display in List page pagination.
            Default value is set to `10`.
        page_size_options: Pagination choices displayed in List page.
            Default value is set to `[10, 25, 50, 100]`. Use `-1`to display All
        responsive: Activate responsive design https://datatables.net/extensions/responsive/
        list_template: List view template. Default is `list.html`.
        detail_template: Details view template. Default is `details.html`.
        create_template: Edit view template. Default is `edit.html`.
        edit_template: Edit view template. Default is `edit.html`.

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
                    f._name = "{}.{}".format(field._name, f.name)  # type: ignore
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

    def is_active(self, request: Request) -> bool:
        return request.path_params.get("identity", None) == self.identity

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
            request: Starlette Request
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
            request: Starlette Request
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
            request: Starlette Request
            pks: List of primary keys
        """
        raise NotImplementedError()

    @abstractmethod
    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        """
        Find one item
        Parameters:
            request: Starlette Request
            pk: Primary key
        """
        raise NotImplementedError()

    @abstractmethod
    async def find_by_pks(self, request: Request, pks: List[Any]) -> Sequence[Any]:
        """
        Find many items
        Parameters:
            request: Starlette Request
            pks: List of Primary key
        """
        raise NotImplementedError()

    @abstractmethod
    async def create(self, request: Request, data: Dict) -> Any:
        """
        Create item
        Parameters:
            request: Starlette Request
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
            request: Starlette Request
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
            request: Starlette Request
        """
        if value is None:
            return value
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
                value = getattr(obj, field.name, None)
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
        obj_serialized["_detail_url"] = request.url_for(
            route_name + ":detail", identity=self.identity, pk=pk
        )
        obj_serialized["_edit_url"] = request.url_for(
            route_name + ":edit", identity=self.identity, pk=pk
        )
        return obj_serialized

    async def repr(self, obj: Any, request: Request) -> str:
        """
        Override this function to customize item representation in
        relationships columns
        """
        return str(getattr(obj, self.pk_attr))  # type: ignore

    async def select2_result(self, obj: Any, request: Request) -> str:
        """
        Override this function to customize the way that search results are rendered.
        !!! note
            The returned value should be html. You can use `<span>mytext</span>`
            when you want to return string value
        !!! danger
            Escape your database value to avoid Cross-Site Scripting (XSS) attack.
            You can use Jinja2 Template render with `autoescape=True`.
            For more information [click here](https://owasp.org/www-community/attacks/xss/)

        Parameters:
            obj: item returned by `find_all` or `find_by_pk`
            request: Starlette Request

        """
        template_str = (
            "<span>{%for col in fields %}{%if obj[col]%}<strong>{{col}}:"
            " </strong>{{obj[col]}} {%endif%}{%endfor%}</span>"
        )
        fields = [
            field.name
            for field in self.fields
            if not isinstance(field, (RelationField, FileField))
        ]
        return Template(template_str, autoescape=True).render(obj=obj, fields=fields)

    async def select2_selection(self, obj: Any, request: Request) -> str:
        """
        Override this function to customize the way that selections are rendered.
        !!! note
            The returned value should be html. You can use `<span>mytext</span>`
            when you want to return string value
        !!! danger
            Escape your database value to avoid Cross-Site Scripting (XSS) attack.
            You can use Jinja2 Template render with `autoescape=True`.
            For more information [click here](https://owasp.org/www-community/attacks/xss/)

        Parameters:
            obj: item returned by `find_all` or `find_by_pk`
            request: Starlette Request

        """
        return await self.select2_result(obj, request)

    def _length_menu(self) -> Any:
        return [
            self.page_size_options,
            [("All" if i < 0 else i) for i in self.page_size_options],
        ]

    def _search_columns_selector(self) -> List[str]:
        return ["%s:name" % name for name in self.searchable_fields]  # type: ignore

    def _export_columns_selector(self) -> List[str]:
        return ["%s:name" % name for name in self.export_fields]  # type: ignore

    def _extract_fields(
        self, action: RequestAction = RequestAction.LIST
    ) -> Sequence[BaseField]:
        return extract_fields(self.fields, action)

    def _additional_css_links(
        self, request: Request, action: RequestAction
    ) -> Set[str]:
        links = set()
        for field in self.fields:
            if (action == RequestAction.CREATE and field.exclude_from_create) or (
                action == RequestAction.EDIT and field.exclude_from_edit
            ):
                continue
            links.update(field.additional_css_links(request))
        return links

    def _additional_js_links(self, request: Request, action: RequestAction) -> Set[str]:
        links = set()
        for field in self.fields:
            if (action == RequestAction.CREATE and field.exclude_from_create) or (
                action == RequestAction.EDIT and field.exclude_from_edit
            ):
                continue
            links.update(field.additional_js_links(request))
        return links

    def _configs(self, request: Request) -> Dict[str, Any]:
        return {
            "label": self.label,
            "pageSize": self.page_size,
            "lengthMenu": self._length_menu(),
            "searchColumns": self._search_columns_selector(),
            "exportColumns": self._export_columns_selector(),
            "exportTypes": self.export_types,
            "columnVisibility": self.column_visibility,
            "searchBuilder": self.search_builder,
            "responsiveTable": self.responsive_table,
            "fields": [f.dict() for f in self._extract_fields()],
            "pk": self.pk_attr,
            "apiUrl": request.url_for(
                f"{request.app.state.ROUTE_NAME}:api", identity=self.identity
            ),
        }
