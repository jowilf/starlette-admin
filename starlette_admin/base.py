import ast
import json
from datetime import date, datetime, time
from json import JSONDecodeError
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Type, Union

from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from starlette.applications import Starlette
from starlette.datastructures import FormData, UploadFile
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.status import HTTP_204_NO_CONTENT, HTTP_303_SEE_OTHER, HTTP_403_FORBIDDEN
from starlette.templating import Jinja2Templates
from starlette_admin.auth import AuthMiddleware, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed
from starlette_admin.fields import (
    BaseField,
    BooleanField,
    DateField,
    DateTimeField,
    EmailField,
    FileField,
    HasMany,
    HasOne,
    JSONField,
    NumberField,
    PhoneField,
    RelationField,
    TimeField,
)
from starlette_admin.helpers import get_file_icon, is_empty_file
from starlette_admin.views import (
    BaseModelView,
    BaseView,
    CustomView,
    DefaultAdminIndexView,
    DropDown,
    Link,
)


class BaseAdmin:
    """Base class for implementing Admin interface."""

    def __init__(
        self,
        title: str = "Admin",
        base_url: str = "/admin",
        route_name: str = "admin",
        logo_url: Optional[str] = None,
        login_logo_url: Optional[str] = None,
        templates_dir: str = "templates",
        index_view: Type[CustomView] = DefaultAdminIndexView,
        auth_provider: Optional[AuthProvider] = None,
        middlewares: Optional[Sequence[Middleware]] = None,
        debug: bool = False,
    ):
        """
        Parameters:
            title: Admin title.
            base_url: Base URL for Admin interface.
            route_name: Mounted Admin name
            logo_url: URL of logo to be displayed instead of title.
            login_logo_url: If set, it will be used for login interface instead of logo_url.
            templates_dir: Templates dir for customisation
            index_view: CustomView to use for index page.
            auth_provider: Authentication Provider
            middlewares: Starlette middlewares
        """
        self.title = title
        self.base_url = base_url
        self.route_name = route_name
        self.logo_url = logo_url
        self.login_logo_url = login_logo_url
        self.templates_dir = templates_dir
        self.auth_provider = auth_provider
        self.middlewares = middlewares
        self.index_view: Type[CustomView] = index_view
        self._views: List[BaseView] = []
        self._models: List[BaseModelView] = []
        self.routes: List[Union[Route, Mount]] = []
        self.debug = debug
        self._setup_templates()
        self.init_auth()
        self.init_routes()

    def add_view(self, view: Type[BaseView]) -> None:
        """
        Add View to the Admin interface.
        """
        self._views.append(view())
        self.add_routes_for_view(view)

    def init_auth(self) -> None:
        if self.auth_provider is not None:
            self.middlewares = (
                [] if self.middlewares is None else list(self.middlewares)
            )
            self.middlewares.append(
                Middleware(AuthMiddleware, provider=self.auth_provider)
            )
            self.routes.extend(
                [
                    Route(
                        self.auth_provider.login_path,
                        self._render_login,
                        methods=["GET", "POST"],
                        name="login",
                    ),
                    Route(
                        self.auth_provider.logout_path,
                        self._render_logout,
                        methods=["GET"],
                        name="logout",
                    ),
                ]
            )

    def init_routes(self) -> None:
        statics = StaticFiles(packages=["starlette_admin"])
        self.routes.extend(
            [
                Mount("/statics", app=statics, name="statics"),
                Route(
                    self.index_view.path,
                    self._render_custom_view(self.index_view()),
                    methods=self.index_view.methods,
                    name="index",
                ),
                Route(
                    "/api/{identity}",
                    self._render_api,
                    methods=["GET", "DELETE"],
                    name="api",
                ),
                Route(
                    "/{identity}/list",
                    self._render_list,
                    methods=["GET"],
                    name="list",
                ),
                Route(
                    "/{identity}/detail/{pk}",
                    self._render_detail,
                    methods=["GET"],
                    name="detail",
                ),
                Route(
                    "/{identity}/create",
                    self._render_create,
                    methods=["GET", "POST"],
                    name="create",
                ),
                Route(
                    "/{identity}/edit/{pk}",
                    self._render_edit,
                    methods=["GET", "POST"],
                    name="edit",
                ),
            ]
        )
        if self.index_view.add_to_menu:
            self._views.append(self.index_view())

    def _setup_templates(self) -> None:
        templates = Jinja2Templates(self.templates_dir)
        templates.env.loader = ChoiceLoader(
            [
                FileSystemLoader(self.templates_dir),
                PackageLoader("starlette_admin", "templates"),
            ]
        )
        templates.env.globals["views"] = self._views
        templates.env.globals["title"] = self.title
        templates.env.globals["is_auth_enabled"] = self.auth_provider is not None
        templates.env.globals["__name__"] = self.route_name
        templates.env.globals["logo_url"] = self.logo_url
        templates.env.globals["login_logo_url"] = self.login_logo_url
        templates.env.filters["is_custom_view"] = lambda res: isinstance(
            res, CustomView
        )
        templates.env.filters["is_link"] = lambda res: isinstance(res, Link)
        templates.env.filters["is_model"] = lambda res: isinstance(res, BaseModelView)
        templates.env.filters["is_dropdown"] = lambda res: isinstance(res, DropDown)
        templates.env.filters["tojson"] = lambda data: json.dumps(data, default=str)
        templates.env.filters["file_icon"] = get_file_icon
        templates.env.filters[
            "to_model"
        ] = lambda identity: self._find_model_from_identity(identity)
        self.templates = templates

    def add_routes_for_view(self, view: Type[BaseView]) -> None:
        if issubclass(view, DropDown):
            for sub_view in view.views:
                self.add_routes_for_view(sub_view)
        elif issubclass(view, CustomView):
            self.routes.insert(
                0,
                Route(
                    view.path,
                    endpoint=self._render_custom_view(view()),
                    methods=view.methods,
                    name=view.name,
                ),
            )
        elif issubclass(view, BaseModelView):
            self._models.append(view())

    def _find_model_from_identity(self, identity: Optional[str]) -> BaseModelView:
        if identity is not None:
            for model in self._models:
                if model.identity == identity:
                    return model
        raise HTTPException(404, "Model with identity %s not found" % identity)

    def _render_custom_view(
        self, custom_view: CustomView
    ) -> Callable[[Request], Awaitable[Response]]:
        async def wrapper(request: Request) -> Response:
            if not custom_view.is_accessible(request):
                raise HTTPException(403)
            return await custom_view.render(request, self.templates)

        return wrapper

    async def _render_api(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if request.method == "GET":
            if not model.is_accessible(request):
                return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
            skip = int(request.query_params.get("skip") or "0")
            limit = int(request.query_params.get("limit") or "100")
            order_by = request.query_params.getlist("order_by")
            where = request.query_params.get("where")
            pks = request.query_params.getlist("pks")
            select2 = "select2" in request.query_params.keys()
            if len(pks) > 0:
                items = await model.find_by_pks(request, pks)
                total = len(pks)
            else:
                if where is not None:
                    try:
                        where = json.loads(where)
                    except JSONDecodeError:
                        where = str(where)
                items = await model.find_all(
                    request=request,
                    skip=skip,
                    limit=limit,
                    where=where,
                    order_by=order_by,
                )
                total = await model.count(request=request, where=where)
            return JSONResponse(
                dict(
                    items=[
                        (
                            await self.serialize(
                                item,
                                model,
                                request,
                                "API",
                                include_relationships=not select2,
                                include_select2=select2,
                            )
                        )
                        for item in items
                    ],
                    total=total,
                )
            )
        else:  # "DELETE"
            if not model.can_delete(request):
                return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
            pks = request.query_params.getlist("pks")
            await model.delete(request, pks)
            return Response(status_code=HTTP_204_NO_CONTENT)

    async def _render_login(self, request: Request) -> Response:
        if request.method == "GET":
            return self.templates.TemplateResponse(
                "login.html",
                {"request": request},
            )
        else:
            form = await request.form()
            try:
                assert self.auth_provider is not None
                return await self.auth_provider.login(
                    form.get("username"),
                    form.get("password"),
                    form.get("remember_me") == "on",
                    request,
                    RedirectResponse(
                        request.query_params.get("next")
                        or request.url_for(self.route_name + ":index"),
                        status_code=HTTP_303_SEE_OTHER,
                    ),
                )
            except FormValidationError as errors:
                return self.templates.TemplateResponse(
                    "login.html",
                    {
                        "request": request,
                        "form_errors": errors,
                    },
                )
            except LoginFailed as error:
                return self.templates.TemplateResponse(
                    "login.html",
                    {
                        "request": request,
                        "error": error.msg,
                    },
                )

    async def _render_logout(self, request: Request) -> Response:
        assert self.auth_provider is not None
        return await self.auth_provider.logout(
            request,
            RedirectResponse(
                request.url_for(self.route_name + ":index"),
                status_code=HTTP_303_SEE_OTHER,
            ),
        )

    async def _render_list(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            raise HTTPException(403)
        return self.templates.TemplateResponse(
            model.list_template,
            {"request": request, "model": model},
        )

    async def _render_detail(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request) or not model.can_view_details(request):
            raise HTTPException(403)
        pk = request.path_params.get("pk")
        value = await model.find_by_pk(request, pk)
        if value is None:
            raise HTTPException(404)
        return self.templates.TemplateResponse(
            model.detail_template,
            {
                "request": request,
                "model": model,
                "raw_value": value,
                "value": await self.serialize(value, model, request, "VIEW"),
            },
        )

    async def _render_create(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request) or not model.can_create(request):
            raise HTTPException(403)
        if request.method == "GET":
            return self.templates.TemplateResponse(
                model.create_template,
                {"request": request, "model": model},
            )
        else:
            form = await request.form()
            try:
                obj = await model.create(
                    request, await self.form_to_dict(request, form, model)
                )
            except FormValidationError as errors:
                return self.templates.TemplateResponse(
                    model.create_template,
                    {
                        "request": request,
                        "model": model,
                        "errors": errors,
                        "value": form,
                        "is_form_value": True,
                    },
                )
            pk = getattr(obj, model.pk_attr)  # type: ignore
            url = request.url_for(self.route_name + ":list", identity=model.identity)
            if form.get("_continue_editing", None) is not None:
                url = request.url_for(
                    self.route_name + ":edit", identity=model.identity, pk=pk
                )
            elif form.get("_add_another", None) is not None:
                url = request.url  # type: ignore
            return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    async def _render_edit(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request) or not model.can_edit(request):
            raise HTTPException(403)
        pk = request.path_params.get("pk")
        value = await model.find_by_pk(request, pk)
        if value is None:
            raise HTTPException(404)
        if request.method == "GET":
            return self.templates.TemplateResponse(
                model.edit_template,
                {
                    "request": request,
                    "model": model,
                    "raw_value": value,
                    "value": await self.serialize(value, model, request, "EDIT"),
                },
            )
        else:
            form = await request.form()
            try:
                obj = await model.edit(
                    request,
                    pk,
                    await self.form_to_dict(request, form, model, is_edit=True),
                )
            except FormValidationError as errors:
                return self.templates.TemplateResponse(
                    model.edit_template,
                    {
                        "request": request,
                        "model": model,
                        "errors": errors,
                        "value": form,
                        "is_form_value": True,
                    },
                )
            pk = getattr(obj, model.pk_attr)  # type: ignore
            url = request.url_for(self.route_name + ":list", identity=model.identity)
            if form.get("_continue_editing", None) is not None:
                url = request.url_for(
                    self.route_name + ":edit", identity=model.identity, pk=pk
                )
            elif form.get("_add_another", None) is not None:
                url = request.url_for(
                    self.route_name + ":create", identity=model.identity
                )
            return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    async def _render_error(
        self,
        request: Request,
        exc: Exception = HTTPException(status_code=500),
    ) -> Response:
        assert isinstance(exc, HTTPException)
        return self.templates.TemplateResponse(
            "error.html",
            {"request": request, "exc": exc},
            status_code=exc.status_code,
        )

    async def serialize(
        self,
        obj: Any,
        model: BaseModelView,
        request: Request,
        ctx: str,
        include_relationships: bool = True,
        include_select2: bool = False,
    ) -> Dict[str, Any]:
        obj_serialized: Dict[str, Any] = dict()
        for field in model.fields:
            value = getattr(obj, field.name, None)
            if isinstance(field, RelationField) and include_relationships:
                foreign_model = self._find_model_from_identity(field.identity)
                if value is not None and isinstance(field, HasOne):
                    obj_serialized[field.name] = await self.serialize(
                        value, foreign_model, request, ctx, include_relationships=False
                    )
                elif value is not None:
                    obj_serialized[field.name] = [
                        (
                            await self.serialize(
                                v,
                                foreign_model,
                                request,
                                ctx,
                                include_relationships=False,
                            )
                        )
                        for v in value
                    ]
                else:
                    obj_serialized[field.name] = value  # None
            elif not isinstance(field, RelationField):
                if value is not None and field.is_array:
                    obj_serialized[field.name] = [
                        (await model.serialize_field_value(v, field, ctx, request))
                        for v in value
                    ]
                elif value is not None:
                    obj_serialized[field.name] = await model.serialize_field_value(
                        value, field, ctx, request
                    )
                else:
                    obj_serialized[field.name] = value  # None

        if include_select2:
            obj_serialized["_select2_selection"] = await model.select2_selection(
                obj, request
            )
            obj_serialized["_select2_result"] = await model.select2_result(obj, request)
        obj_serialized["_repr"] = await model.repr(obj, request)
        return obj_serialized

    async def format_form_value(self, field: BaseField, value: Any) -> Any:
        if isinstance(field, BooleanField):
            return value == "on"
        elif isinstance(field, NumberField):
            return ast.literal_eval(value)
        elif isinstance(field, DateTimeField):
            return datetime.fromisoformat(value)
        elif isinstance(field, DateField):
            return date.fromisoformat(value)
        elif isinstance(field, TimeField):
            return time.fromisoformat(value)
        elif isinstance(field, JSONField):
            try:
                return json.loads(value)
            except JSONDecodeError:
                raise FormValidationError({field.name: "Invalid JSON value"})
        elif isinstance(value, UploadFile) and is_empty_file(value.file):
            """Detect and remove empty file"""
            return None
        return value

    async def form_to_dict(
        self,
        request: Request,
        form_data: FormData,
        model: BaseModelView,
        is_edit: bool = False,
    ) -> Dict[str, Any]:
        data = dict()
        for field in model.fields:
            if (
                (field.name == model.pk_attr and not model.form_include_pk)
                or (is_edit and field.exclude_from_edit)
                or (not is_edit and field.exclude_from_create)
            ):
                continue
            if isinstance(field, FileField) and is_edit:
                data[f"_{field.name}-delete"] = (
                    form_data.get(f"_{field.name}-delete") == "on"
                )
            if form_data.get(field.name, None) is None:
                if isinstance(field, BooleanField):
                    data[field.name] = False
                else:
                    data[field.name] = [] if isinstance(field, HasMany) else None
            elif (
                isinstance(
                    field,
                    (
                        NumberField,
                        EmailField,
                        PhoneField,
                        DateTimeField,
                        DateField,
                        TimeField,
                    ),
                )
                and form_data.get(field.name) == ""
            ):
                data[field.name] = None
            elif not isinstance(field, RelationField):
                if field.is_array:
                    data[field.name] = [
                        (await self.format_form_value(field, v))
                        for v in form_data.getlist(field.name)
                    ]
                    if isinstance(field, FileField):
                        """Remove empty files"""
                        data[field.name] = [v for v in data[field.name] if v]
                else:
                    data[field.name] = await self.format_form_value(
                        field, form_data.get(field.name)
                    )
            else:
                if (
                    isinstance(field, HasOne)
                    and form_data.get(field.name, None) is not None
                ):
                    foreign_model = self._find_model_from_identity(field.identity)
                    data[field.name] = await foreign_model.find_by_pk(
                        request, form_data.get(field.name)
                    )
                elif (
                    isinstance(field, HasMany)
                    and len(form_data.getlist(field.name)) > 0
                ):
                    foreign_model = self._find_model_from_identity(field.identity)
                    data[field.name] = await foreign_model.find_by_pks(
                        request, form_data.getlist(field.name)
                    )
        return data

    def mount_to(self, app: Starlette) -> None:
        admin_app = Starlette(
            routes=self.routes,
            middleware=self.middlewares,
            debug=self.debug,
            exception_handlers={HTTPException: self._render_error},
        )
        admin_app.state.ROUTE_NAME = self.route_name
        app.mount(
            self.base_url,
            app=admin_app,
            name=self.route_name,
        )
