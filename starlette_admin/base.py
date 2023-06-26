import json
from json import JSONDecodeError
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Type, Union

from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from starlette.applications import Starlette
from starlette.datastructures import FormData
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.status import (
    HTTP_303_SEE_OTHER,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from starlette.templating import Jinja2Templates
from starlette_admin._types import RequestAction
from starlette_admin.auth import AuthMiddleware, AuthProvider
from starlette_admin.exceptions import ActionFailed, FormValidationError, LoginFailed
from starlette_admin.helpers import get_file_icon
from starlette_admin.i18n import (
    I18nConfig,
    LocaleMiddleware,
    get_locale,
    get_locale_display_name,
    gettext,
    ngettext,
)
from starlette_admin.i18n import lazy_gettext as _
from starlette_admin.views import BaseModelView, BaseView, CustomView, DropDown, Link


class BaseAdmin:
    """Base class for implementing Admin interface."""

    def __init__(
        self,
        title: str = _("Admin"),
        base_url: str = "/admin",
        route_name: str = "admin",
        logo_url: Optional[str] = None,
        login_logo_url: Optional[str] = None,
        templates_dir: str = "templates",
        statics_dir: Optional[str] = None,
        index_view: Optional[CustomView] = None,
        auth_provider: Optional[AuthProvider] = None,
        middlewares: Optional[Sequence[Middleware]] = None,
        debug: bool = False,
        i18n_config: Optional[I18nConfig] = None,
    ):
        """
        Parameters:
            title: Admin title.
            base_url: Base URL for Admin interface.
            route_name: Mounted Admin name
            logo_url: URL of logo to be displayed instead of title.
            login_logo_url: If set, it will be used for login interface instead of logo_url.
            templates_dir: Templates dir for customisation
            statics_dir: Statics dir for customisation
            index_view: CustomView to use for index page.
            auth_provider: Authentication Provider
            middlewares: Starlette middlewares
            i18n_config: i18n configuration
        """
        self.title = title
        self.base_url = base_url
        self.route_name = route_name
        self.logo_url = logo_url
        self.login_logo_url = login_logo_url
        self.templates_dir = templates_dir
        self.statics_dir = statics_dir
        self.auth_provider = auth_provider
        self.middlewares = middlewares
        self.index_view = (
            index_view
            if (index_view is not None)
            else CustomView("", add_to_menu=False)
        )
        self._views: List[BaseView] = []
        self._models: List[BaseModelView] = []
        self.routes: List[Union[Route, Mount]] = []
        self.debug = debug
        self.i18n_config = i18n_config
        self._setup_templates()
        self.init_locale()
        self.init_auth()
        self.init_routes()

    def add_view(self, view: Union[Type[BaseView], BaseView]) -> None:
        """
        Add View to the Admin interface.
        """
        view_instance = view if isinstance(view, BaseView) else view()
        self._views.append(view_instance)
        self.setup_view(view_instance)

    def custom_render_js(self, request: Request) -> Optional[str]:
        """
        Override this function to provide a link to custom js to override the
        global `render` object in javascript which is use to render fields in
        list page.

        Args:
            request: Starlette Request
        """
        return None

    def init_locale(self) -> None:
        if self.i18n_config is not None:
            try:
                import babel  # noqa
            except ImportError as err:
                raise ImportError(
                    "'babel' package is required to use i18n features."
                    "Install it with `pip install starlette-admin[i18n]`"
                ) from err
            self.middlewares = (
                [] if self.middlewares is None else list(self.middlewares)
            )
            self.middlewares.insert(
                0, Middleware(LocaleMiddleware, i18n_config=self.i18n_config)
            )

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
        statics = StaticFiles(directory=self.statics_dir, packages=["starlette_admin"])
        self.routes.extend(
            [
                Mount("/statics", app=statics, name="statics"),
                Route(
                    self.index_view.path,
                    self._render_custom_view(self.index_view),
                    methods=self.index_view.methods,
                    name="index",
                ),
                Route(
                    "/api/{identity}",
                    self._render_api,
                    methods=["GET"],
                    name="api",
                ),
                Route(
                    "/api/{identity}/action",
                    self.handle_action,
                    methods=["GET", "POST"],
                    name="action",
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
            self._views.append(self.index_view)

    def _setup_templates(self) -> None:
        templates = Jinja2Templates(self.templates_dir, extensions=["jinja2.ext.i18n"])
        templates.env.loader = ChoiceLoader(
            [
                FileSystemLoader(self.templates_dir),
                PackageLoader("starlette_admin", "templates"),
            ]
        )
        # globals
        templates.env.globals["views"] = self._views
        templates.env.globals["title"] = self.title
        templates.env.globals["is_auth_enabled"] = self.auth_provider is not None
        templates.env.globals["__name__"] = self.route_name
        templates.env.globals["logo_url"] = self.logo_url
        templates.env.globals["login_logo_url"] = self.login_logo_url
        templates.env.globals["custom_render_js"] = lambda r: self.custom_render_js(r)
        templates.env.globals["get_locale"] = get_locale
        templates.env.globals["get_locale_display_name"] = get_locale_display_name
        templates.env.globals["i18n_config"] = self.i18n_config or I18nConfig()
        # filters
        templates.env.filters["is_custom_view"] = lambda r: isinstance(r, CustomView)
        templates.env.filters["is_link"] = lambda res: isinstance(res, Link)
        templates.env.filters["is_model"] = lambda res: isinstance(res, BaseModelView)
        templates.env.filters["is_dropdown"] = lambda res: isinstance(res, DropDown)
        templates.env.filters["get_admin_user"] = (
            self.auth_provider.get_admin_user if self.auth_provider else None
        )
        templates.env.filters["tojson"] = lambda data: json.dumps(data, default=str)
        templates.env.filters["file_icon"] = get_file_icon
        templates.env.filters[
            "to_model"
        ] = lambda identity: self._find_model_from_identity(identity)
        templates.env.filters["is_iter"] = lambda v: isinstance(v, (list, tuple))
        templates.env.filters["is_str"] = lambda v: isinstance(v, str)
        templates.env.filters["is_dict"] = lambda v: isinstance(v, dict)
        templates.env.filters["ra"] = lambda a: RequestAction(a)
        # install i18n
        templates.env.install_gettext_callables(gettext, ngettext, True)  # type: ignore
        self.templates = templates

    def setup_view(self, view: BaseView) -> None:
        if isinstance(view, DropDown):
            for sub_view in view.views:
                self.setup_view(sub_view)
        elif isinstance(view, CustomView):
            self.routes.insert(
                0,
                Route(
                    view.path,
                    endpoint=self._render_custom_view(view),
                    methods=view.methods,
                    name=view.name,
                ),
            )
        elif isinstance(view, BaseModelView):
            view._find_foreign_model = lambda i: self._find_model_from_identity(i)
            self._models.append(view)

    def _find_model_from_identity(self, identity: Optional[str]) -> BaseModelView:
        if identity is not None:
            for model in self._models:
                if model.identity == identity:
                    return model
        raise HTTPException(
            HTTP_404_NOT_FOUND,
            _("Model with identity %(identity)s not found") % {"identity": identity},
        )

    def _render_custom_view(
        self, custom_view: CustomView
    ) -> Callable[[Request], Awaitable[Response]]:
        async def wrapper(request: Request) -> Response:
            if not custom_view.is_accessible(request):
                raise HTTPException(HTTP_403_FORBIDDEN)
            return await custom_view.render(request, self.templates)

        return wrapper

    async def _render_api(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        skip = int(request.query_params.get("skip") or "0")
        limit = int(request.query_params.get("limit") or "100")
        order_by = request.query_params.getlist("order_by")
        where = request.query_params.get("where")
        pks = request.query_params.getlist("pks")
        select2 = "select2" in request.query_params
        if len(pks) > 0:
            items = await model.find_by_pks(request, pks)
            total = len(items)
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
            {
                "items": [
                    (
                        await model.serialize(
                            item,
                            request,
                            RequestAction.API if select2 else RequestAction.LIST,
                            include_relationships=not select2,
                            include_select2=select2,
                        )
                    )
                    for item in items
                ],
                "total": total,
            }
        )

    async def handle_action(self, request: Request) -> Response:
        try:
            identity = request.path_params.get("identity")
            pks = request.query_params.getlist("pks")
            name = request.query_params.get("name")
            model = self._find_model_from_identity(identity)
            if not model.is_accessible(request):
                raise ActionFailed("Forbidden")
            assert name is not None
            handler_return = await model.handle_action(request, pks, name)
            if isinstance(handler_return, Response):
                return handler_return
            return JSONResponse({"msg": handler_return})
        except ActionFailed as exc:
            return JSONResponse({"msg": exc.msg}, status_code=HTTP_400_BAD_REQUEST)

    async def _render_login(self, request: Request) -> Response:
        if request.method == "GET":
            return self.templates.TemplateResponse(
                "login.html",
                {"request": request, "_is_login_path": True},
            )
        form = await request.form()
        try:
            assert self.auth_provider is not None
            return await self.auth_provider.login(
                form.get("username"),  # type: ignore
                form.get("password"),  # type: ignore
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
                {"request": request, "form_errors": errors, "_is_login_path": True},
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except LoginFailed as error:
            return self.templates.TemplateResponse(
                "login.html",
                {"request": request, "error": error.msg, "_is_login_path": True},
                status_code=HTTP_400_BAD_REQUEST,
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
            raise HTTPException(HTTP_403_FORBIDDEN)
        return self.templates.TemplateResponse(
            model.list_template,
            {
                "request": request,
                "model": model,
                "_actions": await model.get_all_actions(request),
                "__js_model__": await model._configs(request),
            },
        )

    async def _render_detail(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request) or not model.can_view_details(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        pk = request.path_params.get("pk")
        obj = await model.find_by_pk(request, pk)
        if obj is None:
            raise HTTPException(HTTP_404_NOT_FOUND)
        return self.templates.TemplateResponse(
            model.detail_template,
            {
                "request": request,
                "model": model,
                "raw_obj": obj,
                "obj": await model.serialize(obj, request, RequestAction.DETAIL),
            },
        )

    async def _render_create(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request) or not model.can_create(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        if request.method == "GET":
            return self.templates.TemplateResponse(
                model.create_template,
                {"request": request, "model": model},
            )
        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.CREATE)
        try:
            obj = await model.create(request, dict_obj)
        except FormValidationError as exc:
            return self.templates.TemplateResponse(
                model.create_template,
                {
                    "request": request,
                    "model": model,
                    "errors": exc.errors,
                    "obj": dict_obj,
                },
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            )
        pk = getattr(obj, model.pk_attr)  # type: ignore
        url = request.url_for(self.route_name + ":list", identity=model.identity)
        if form.get("_continue_editing", None) is not None:
            url = request.url_for(
                self.route_name + ":edit", identity=model.identity, pk=pk
            )
        elif form.get("_add_another", None) is not None:
            url = request.url
        return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    async def _render_edit(self, request: Request) -> Response:
        identity = request.path_params.get("identity")
        model = self._find_model_from_identity(identity)
        if not model.is_accessible(request) or not model.can_edit(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        pk = request.path_params.get("pk")
        obj = await model.find_by_pk(request, pk)
        if obj is None:
            raise HTTPException(HTTP_404_NOT_FOUND)
        if request.method == "GET":
            return self.templates.TemplateResponse(
                model.edit_template,
                {
                    "request": request,
                    "model": model,
                    "raw_obj": obj,
                    "obj": await model.serialize(obj, request, RequestAction.EDIT),
                },
            )
        form = await request.form()
        dict_obj = await self.form_to_dict(request, form, model, RequestAction.EDIT)
        try:
            obj = await model.edit(request, pk, dict_obj)
        except FormValidationError as exc:
            return self.templates.TemplateResponse(
                model.edit_template,
                {
                    "request": request,
                    "model": model,
                    "errors": exc.errors,
                    "obj": dict_obj,
                },
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            )
        pk = getattr(obj, model.pk_attr)  # type: ignore
        url = request.url_for(self.route_name + ":list", identity=model.identity)
        if form.get("_continue_editing", None) is not None:
            url = request.url_for(
                self.route_name + ":edit", identity=model.identity, pk=pk
            )
        elif form.get("_add_another", None) is not None:
            url = request.url_for(self.route_name + ":create", identity=model.identity)
        return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    async def _render_error(
        self,
        request: Request,
        exc: Exception = HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR),
    ) -> Response:
        assert isinstance(exc, HTTPException)
        return self.templates.TemplateResponse(
            "error.html",
            {"request": request, "exc": exc},
            status_code=exc.status_code,
        )

    async def form_to_dict(
        self,
        request: Request,
        form_data: FormData,
        model: BaseModelView,
        action: RequestAction,
    ) -> Dict[str, Any]:
        data = {}
        for field in model.fields:
            if (action == RequestAction.EDIT and field.exclude_from_edit) or (
                action == RequestAction.CREATE and field.exclude_from_create
            ):
                continue
            data[field.name] = await field.parse_form_data(request, form_data, action)
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
