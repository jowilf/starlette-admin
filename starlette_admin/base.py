import logging
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from jinja2 import (
    BaseLoader,
    ChoiceLoader,
    Environment,
    FileSystemLoader,
    PackageLoader,
    PrefixLoader,
)
from markupsafe import Markup
from starlette.applications import Starlette
from starlette.datastructures import FormData, QueryParams, UploadFile
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.status import (
    HTTP_303_SEE_OTHER,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from starlette.templating import Jinja2Templates
from starlette_admin.actions import ActionSelection
from starlette_admin.auth import BaseAuthProvider
from starlette_admin.events import AdminEventBus
from starlette_admin.exceptions import (
    ActionFailed,
    FormValidationError,
    InvalidRelationFieldError,
)
from starlette_admin.export import (
    ExportConfig,
    ExportContext,
)
from starlette_admin.fields import BaseField, CollectionField, FileField, RelationField
from starlette_admin.flash import FlashMiddleware, flash, get_flashed_messages
from starlette_admin.helpers import (
    HTTP_422,
    JSONResponse,
    _as_url_callable,
    back_url,
    create_url,
    detail_url,
    edit_url,
    export_url,
    get_file_icon,
    html_safe_json,
    import_url,
    list_url,
    not_none,
    safe_redirect_url,
    safe_url,
    sanitize_html,
    static_url,
)
from starlette_admin.i18n import (
    I18nConfig,
    LocaleMiddleware,
    TimezoneConfig,
    TimezoneMiddleware,
    get_locale,
    get_locale_display_name,
    get_timezone,
    get_timezone_display_name,
    gettext,
    ngettext,
)
from starlette_admin.i18n import lazy_gettext as _
from starlette_admin.importers import (
    BaseImporter,
    ImportConfig,
    ImportContext,
    ImportResult,
    ImportRowError,
)
from starlette_admin.logging import configure_logging, get_logger
from starlette_admin.routing import route
from starlette_admin.security.csrf import CSRFMiddleware, csrf_input
from starlette_admin.storage.base import (
    FileInfo,
    UnknownStorageError,
    get_storage,
    secure_filename,
)
from starlette_admin.theme import ThemeSettings
from starlette_admin.types import RequestAction
from starlette_admin.views import (
    BaseModelView,
    BaseView,
    CustomView,
    DefaultIndexView,
    DropDown,
    InlineModelView,
    Link,
)
from starlette_admin.widgets import render_widget

_log = get_logger(__name__)


class BaseAdmin:
    """Entry point for building an admin site.

    Instantiate it, register views with [add_view][starlette_admin.base.BaseAdmin.add_view]
    or [add_link][starlette_admin.base.BaseAdmin.add_link], then attach the
    resulting routes to your Starlette/FastAPI app with
    [mount_to][starlette_admin.base.BaseAdmin.mount_to].
    """

    def __init__(
        self,
        title: str = _("Admin"),
        base_url: str = "/admin",
        route_name: str = "admin",
        logo_url: str | Callable[[Request], str | None] | None = None,
        login_logo_url: str | Callable[[Request], str | None] | None = None,
        favicon_url: str | Callable[[Request], str | None] | None = None,
        templates_dir: str = "templates",
        additional_loaders: Sequence[BaseLoader] | None = None,
        static_dir: str | None = None,
        index_view: CustomView | None = None,
        theme: ThemeSettings | None = None,
        auth_provider: BaseAuthProvider | None = None,
        secret_key: str | None = None,
        middlewares: Sequence[Middleware] | None = None,
        i18n_config: I18nConfig | None = None,
        timezone_config: TimezoneConfig | None = TimezoneConfig(),
        import_config: ImportConfig | None = None,
        export_config: ExportConfig | None = None,
        debug: bool = False,
    ):
        """
        Parameters:
            title: Title displayed in the admin's navbar and browser tab.
            base_url: URL prefix the admin is mounted under (e.g. ``/admin``).
            route_name: Name of the mounted Starlette route, used to build
                admin URLs with ``request.url_for``.
            logo_url: URL or callable ``(request) -> str | None`` of the logo
                displayed instead of the title.
            login_logo_url: URL or callable ``(request) -> str | None`` used
                on the login page instead of ``logo_url``.
            favicon_url: URL or callable ``(request) -> str | None`` of the
                favicon.
            templates_dir: Directory checked for template overrides before
                falling back to the built-in templates.
            additional_loaders: Extra Jinja2 loaders consulted after
                ``templates_dir`` but before the built-in starlette-admin
                templates. Useful to load templates from packages or
                in-memory mappings (e.g. :class:`jinja2.PackageLoader`,
                :class:`jinja2.DictLoader`).
            static_dir: Directory checked for static file overrides before
                falling back to the built-in static files.
            index_view: Custom view rendered at the admin's root path.
                Defaults to a generated index listing all registered views.
            theme: Theme settings applied as ``data-bs-theme-*`` attributes on
                ``<html>``.
            auth_provider: Authentication provider guarding access to the
                admin. Leaving this unset makes the admin publicly accessible.
            secret_key: Secret key used to sign admin cookies (CSRF token and
                flash messages). Required for these values to survive server
                restarts. A random key is generated when omitted (dev
                convenience), but signed values are lost on restart.
            middlewares: Additional Starlette middlewares to run on the admin
                app.
            i18n_config: Enables translated UI text and locale selection when
                provided. Leaving this unset serves the admin in English only.
            timezone_config: Controls how datetimes are converted for display
                and how the timezone is selected per request.
            import_config: Security and capacity limits for the import endpoint
                (upload size, max rows per request). Defaults to
                :class:`~starlette_admin.importers.ImportConfig` with sane
                production limits when not provided.
            export_config: Capacity limits for the export endpoint (max rows per
                request). Defaults to :class:`~starlette_admin.export.ExportConfig`
                with ``max_rows=100_000`` when not provided.
            debug: Enable debug mode. When ``True``, automatically configures
                colored DEBUG-level console logging for the ``starlette_admin``
                package (equivalent to calling
                ``starlette_admin.logging.configure_logging()`` before startup).
        """
        self.debug = debug
        if debug:  # pragma: no cover
            configure_logging(level=logging.DEBUG)
        self.title = title
        self.base_url = base_url
        self.route_name = route_name
        self.logo_url = logo_url
        self.login_logo_url = login_logo_url
        self.favicon_url = favicon_url
        self.templates_dir = templates_dir
        self.additional_loaders = (
            list(additional_loaders) if additional_loaders is not None else []
        )
        self.static_dir = static_dir
        self.auth_provider = auth_provider
        self.secret_key = secret_key
        self.middlewares = list(middlewares) if middlewares is not None else []
        self.import_config = (
            import_config if import_config is not None else ImportConfig()
        )
        self.export_config = (
            export_config if export_config is not None else ExportConfig()
        )
        self._views: list[BaseView] = []
        self._model_views: list[BaseModelView] = []
        self.routes: list[Route | Mount] = []
        self._app: Starlette | None = None
        self.events: AdminEventBus = AdminEventBus()
        self.i18n_config = i18n_config
        self.timezone_config = timezone_config
        self.theme = theme or ThemeSettings()
        _log.info(
            "Admin initializing: route_name=%r base_url=%r title=%r",
            route_name,
            base_url,
            title,
        )
        _log.debug(
            "Admin: setting up Jinja2 templates (templates_dir=%r)", templates_dir
        )
        self._setup_templates()
        self.index_view = (
            index_view
            if (index_view is not None)
            else DefaultIndexView(
                self._model_views, self.templates.env, app_title=title
            )
        )
        _log.debug("Admin: templates ready")
        self._ensure_secret_key()
        self._init_locale()
        self._init_flash()
        self._init_csrf()
        self._init_auth()
        self._init_routes()
        _log.info(
            "Admin ready: route_name=%r base_url=%r routes=%d auth=%s i18n=%s tz=%s",
            self.route_name,
            self.base_url,
            len(self.routes),
            "yes" if self.auth_provider else "no",
            "yes" if self.i18n_config else "no",
            "yes" if self.timezone_config else "no",
        )

    def add_view(self, view: type[BaseView] | BaseView) -> None:
        """Register a view (or view class) on the admin.

        Accepts either an instance or a class; classes are instantiated with
        no arguments. Registering a `BaseModelView` also wires it into the
        admin's event bus so `AdminEvent`s can target it by key.

        Raises:
            RuntimeError: If called after [mount_to][starlette_admin.base.BaseAdmin.mount_to]
                has already built and mounted the admin app.
        """
        if self._app is not None:
            raise RuntimeError(
                "Cannot add_view after the admin has been mounted with mount_to()."
            )
        view_instance = view if isinstance(view, BaseView) else view()
        _log.debug(
            "add_view: registering %s (menu_label=%r)",
            type(view_instance).__name__,
            getattr(view_instance, "menu_label", None),
        )
        self._views.append(view_instance)
        self._setup_view(view_instance)
        if isinstance(view_instance, BaseModelView) and view_instance.key is not None:
            self.events._register_view(view_instance.key, view_instance.events)

    def add_link(self, link: Link) -> None:
        """Register a `Link` in the admin's navigation menu."""
        self.add_view(link)

    @property
    def app(self) -> Starlette:
        """The Starlette sub-application built by `mount_to`.

        Raises:
            RuntimeError: If accessed before `mount_to` has been called.
        """
        if self._app is None:
            raise RuntimeError(
                "admin.app is not available until mount_to() has been called."
            )
        return self._app

    def _init_locale(self) -> None:
        if self.i18n_config is not None:
            try:
                import babel  # noqa
            except ImportError as err:
                _log.error(
                    "_init_locale: 'babel' package is missing, i18n is unavailable"
                )
                raise ImportError(
                    "'babel' package is required to use i18n features."
                    "Install it with `pip install starlette-admin[i18n]`"
                ) from err
            self.middlewares.insert(
                0, Middleware(LocaleMiddleware, i18n_config=self.i18n_config)
            )
            _log.info(
                "_init_locale: LocaleMiddleware added (default_locale=%r)",
                getattr(self.i18n_config, "default_locale", None),
            )
        else:
            _log.debug("_init_locale: no i18n_config, locale middleware skipped")

        if self.timezone_config is not None:
            self.middlewares.insert(
                0, Middleware(TimezoneMiddleware, timezone_config=self.timezone_config)
            )
            _log.info(
                "_init_locale: TimezoneMiddleware added (default_timezone=%r)",
                getattr(self.timezone_config, "default_timezone", None),
            )
        else:  # pragma: no cover
            _log.debug("_init_locale: no timezone_config, timezone middleware skipped")

    def _init_auth(self) -> None:
        if self.auth_provider is not None:
            _log.info(
                "_init_auth: configuring auth provider %s",
                type(self.auth_provider).__name__,
            )
            self.middlewares.append(self.auth_provider.get_middleware())
            self.routes.extend(self.auth_provider.get_routes(self.templates))
            _log.debug("_init_auth: auth provider setup complete")
        else:
            _log.debug("_init_auth: no auth provider, admin is publicly accessible")

    def _init_csrf(self) -> None:
        """Add signed-cookie CSRFMiddleware unless already present."""
        if any(getattr(m, "cls", None) is CSRFMiddleware for m in self.middlewares):
            _log.debug("_init_csrf: CSRFMiddleware already present, skipping")
            return
        assert self.secret_key is not None
        self.middlewares.append(Middleware(CSRFMiddleware, secret_key=self.secret_key))
        _log.debug("_init_csrf: CSRFMiddleware added")

    def _ensure_secret_key(self) -> None:
        """Generate a random secret key if none was supplied.

        A secret key is required for signed admin cookies (CSRF token and flash
        messages).
        """
        if self.secret_key is None:
            import secrets
            import warnings

            self.secret_key = secrets.token_hex(32)
            warnings.warn(
                "No secret_key provided: a random one was generated. "
                "CSRF tokens and flash messages will NOT survive server restarts. "
                "Set secret_key= on Admin in production.",
                stacklevel=2,
            )
            _log.debug(
                "_ensure_secret_key: no secret_key, generated ephemeral key "
                "(signed cookies lost on restart)"
            )

    def _init_flash(self) -> None:
        """Add FlashMiddleware unless the caller has already included one."""
        if any(getattr(m, "cls", None) is FlashMiddleware for m in self.middlewares):
            _log.debug("_init_flash: FlashMiddleware already present, skipping")
            return
        assert self.secret_key is not None
        self.middlewares.append(Middleware(FlashMiddleware, secret_key=self.secret_key))
        _log.debug("_init_flash: FlashMiddleware added")

    def _template_response(
        self,
        request: Request,
        name: str,
        context: dict | None = None,
        status_code: int = 200,
    ) -> Response:
        """Render a template, automatically injecting flash messages."""
        ctx: dict = {"flashed_messages": get_flashed_messages(request)}
        if context:
            ctx.update(context)
        return self.templates.TemplateResponse(
            request=request,
            name=name,
            context=ctx,
            status_code=status_code,
        )

    async def _render_form_body(
        self,
        request: Request,
        view: BaseModelView,
        obj: Any,
        errors: Mapping[Any, Any] | None,
        config: dict[str, Any],
    ) -> None:
        """Resolve `view.form_layout` and populate `config` with the
        rendered HTML plus the resolved widget tree's additional CSS/JS
        links, for the create/edit page to include."""
        tree = view.resolve_form_layout(request, obj, errors)
        if tree is None:
            config["form_body"] = Markup("")
            config["widget_additional_css"] = []
            config["widget_additional_js"] = []
            return
        config["form_body"] = await render_widget(tree, request, self.templates.env)
        config["widget_additional_css"] = tree.additional_css_links(request)
        config["widget_additional_js"] = tree.additional_js_links(request)

    def _init_routes(self) -> None:
        _log.debug("_init_routes: registering core routes")
        static = StaticFiles(
            directory=self.static_dir, packages=[("starlette_admin", "static")]
        )
        self.routes.append(Mount("/static", app=static, name="static"))
        self.routes.extend(self._collect_core_routes())
        self._register_extra_routes(self.index_view)
        if self.index_view.add_to_menu:
            self._views.append(self.index_view)

    def _collect_core_routes(self) -> list[Route]:
        """Build the admin's core `Route`s from methods decorated with
        [route][starlette_admin.routing.route].

        This keeps the route table next to the handlers it points to,
        instead of a separately maintained list that must stay in sync.
        """
        routes = []
        for method_name in dir(type(self)):
            fn = getattr(type(self), method_name, None)
            if fn is None:
                continue
            path = getattr(fn, "_route_path", None)
            if path is None:
                continue
            routes.append(
                Route(
                    path,
                    getattr(self, method_name),
                    methods=fn._route_methods,
                    name=fn._route_name or method_name,
                )
            )
        return routes

    def _setup_templates(self) -> None:
        env = Environment(
            loader=ChoiceLoader(
                [
                    FileSystemLoader(self.templates_dir),
                    *self.additional_loaders,
                    PackageLoader("starlette_admin", "templates"),
                    PrefixLoader(
                        {
                            "@starlette-admin": PackageLoader(
                                "starlette_admin", "templates"
                            ),
                        }
                    ),
                ]
            ),
            extensions=["jinja2.ext.i18n"],
            autoescape=True,
        )
        templates = Jinja2Templates(env=env)

        # Template globals, available in every rendered template.
        templates.env.globals["views"] = self._views
        templates.env.globals["app_title"] = self.title
        templates.env.globals["is_auth_enabled"] = self.auth_provider is not None
        templates.env.globals["__name__"] = self.route_name
        templates.env.globals["static_url"] = static_url
        templates.env.globals["logo_url"] = _as_url_callable(self.logo_url)
        templates.env.globals["login_logo_url"] = _as_url_callable(self.login_logo_url)
        templates.env.globals["favicon_url"] = _as_url_callable(self.favicon_url)
        templates.env.globals["list_url"] = list_url
        templates.env.globals["detail_url"] = detail_url
        templates.env.globals["edit_url"] = edit_url
        templates.env.globals["create_url"] = create_url
        templates.env.globals["back_url"] = back_url
        templates.env.globals["export_url"] = export_url
        templates.env.globals["import_url"] = import_url
        templates.env.globals["get_locale"] = get_locale
        templates.env.globals["get_locale_display_name"] = get_locale_display_name
        templates.env.globals["i18n_config"] = self.i18n_config or I18nConfig()
        templates.env.globals["get_timezone"] = get_timezone
        templates.env.globals["get_timezone_display_name"] = get_timezone_display_name
        templates.env.globals["timezone_config"] = self.timezone_config
        templates.env.globals["theme_settings"] = self.theme
        templates.env.globals["csrf_input"] = csrf_input
        # Template filters, registered for use with the Jinja2 `|` syntax.
        templates.env.filters["is_custom_view"] = lambda r: isinstance(r, CustomView)
        templates.env.filters["is_link"] = lambda res: isinstance(res, Link)
        templates.env.filters["is_model_view"] = lambda res: isinstance(
            res, BaseModelView
        )
        templates.env.filters["is_dropdown"] = lambda res: isinstance(res, DropDown)
        templates.env.filters["tojson"] = html_safe_json
        templates.env.filters["file_icon"] = get_file_icon
        templates.env.filters["to_view"] = self._find_view_by_key
        templates.env.filters["is_iter"] = lambda v: isinstance(v, (list, tuple))
        templates.env.filters["is_str"] = lambda v: isinstance(v, str)
        templates.env.filters["is_dict"] = lambda v: isinstance(v, dict)
        templates.env.filters["ra"] = RequestAction
        templates.env.filters["safe_url"] = safe_url
        templates.env.filters["sanitize_html"] = sanitize_html
        # Install gettext/ngettext so `{% trans %}` works in templates.
        templates.env.install_gettext_callables(gettext, ngettext, True)  # type: ignore
        self.templates = templates

    def _setup_view(self, view: BaseView) -> None:
        if isinstance(view, DropDown):
            _log.debug(
                "_setup_view: DropDown %r with %d sub-view(s)",
                view.menu_label,
                len(view.views),
            )
            for sub_view in view.views:
                self._setup_view(sub_view)
        elif isinstance(view, CustomView):
            _log.debug(
                "_setup_view: CustomView %r at path=%r",
                view.menu_label,
                view.path,
            )
            self._register_extra_routes(view)
        elif isinstance(view, BaseModelView):
            _log.info(
                "_setup_view: ModelView key=%r (%s) registered",
                view.key,
                type(view).__name__,
            )
            view._find_foreign_view = self._find_view_by_key
            self._model_views.append(view)

    def _validate_relation_fields(self) -> None:
        """Ensure every RelationField (HasOne/HasMany) points to a key
        that has a matching view registered on this admin instance.

        Runs at `mount_to` time, once all `add_view` calls are expected to
        have completed, since a RelationField may reference a view that is
        added after the one that declares it.
        """
        known_keys = {view.key for view in self._model_views if view.key is not None}

        def _check(view: BaseModelView, context: str) -> None:
            for field in view._all_fields:
                if isinstance(field, RelationField) and (
                    field.key is None or field.key not in known_keys
                ):
                    _log.error(
                        "_validate_relation_fields: %s field %r references "
                        "unknown key %r, known keys: %s",
                        context,
                        field.name,
                        field.key,
                        sorted(known_keys),
                    )
                    raise InvalidRelationFieldError(
                        f"{context}: RelationField {field.name!r} references "
                        f"key {field.key!r}, which has no matching "
                        f"view registered. Known keys: "
                        f"{sorted(known_keys)}"
                    )
            for inline in getattr(view, "_inline_instances", []):
                _check(inline, f"{context} -> inline {type(inline).__name__!r}")

        for view in self._model_views:
            _check(view, f"{type(view).__name__!r} (key={view.key!r})")

    def _find_view_by_key(self, key: str | None) -> BaseModelView:
        if key is not None:
            for view in self._model_views:
                if view.key == key:
                    return view
        raise HTTPException(
            HTTP_404_NOT_FOUND,
            _("Model with key %(key)s not found") % {"key": key},
        )

    def _register_extra_routes(self, custom_view: CustomView) -> None:
        """Scan *custom_view* for methods decorated with ``@route`` and
        register them as Starlette ``Route`` objects.

        The primary route (``@route("")`` on ``CustomView.index``) is
        discovered here alongside any extra routes, so there is a single
        registration path for all ``CustomView`` endpoints.
        """
        for method_name in dir(custom_view):
            fn = getattr(type(custom_view), method_name, None)
            if fn is None or not hasattr(fn, "_route_path"):
                continue
            is_primary = fn._route_path == ""
            full_path = (custom_view.path.rstrip("/") + fn._route_path) or "/"
            bound = getattr(custom_view, method_name)
            if fn._route_name is not None:
                route_name = fn._route_name
            elif is_primary and custom_view.route_name is not None:
                route_name = custom_view.route_name
            else:
                route_name = fn.__name__
            methods = fn._route_methods

            endpoint = self._wrap_extra_route(custom_view, bound, self.templates)

            self.routes.insert(
                0,
                Route(
                    full_path,
                    endpoint=endpoint,
                    methods=methods,
                    name=route_name,
                ),
            )

    def _wrap_extra_route(
        self,
        custom_view: CustomView,
        handler: Callable,
        templates: Jinja2Templates,
    ) -> Callable[[Request], Awaitable[Response]]:
        """Wrap an extra-route handler with an access check."""
        custom_view.templates = templates

        async def wrapper(request: Request) -> Response:
            if not custom_view.is_accessible(request):
                raise HTTPException(HTTP_403_FORBIDDEN)
            return await handler(request)

        wrapper._login_not_required = getattr(  # type: ignore[attr-defined]
            handler, "_login_not_required", False
        )
        return wrapper

    @route("/_api/{key}/relation-lookup", methods=["GET"], name="relation-lookup")
    async def _render_relation_lookup(self, request: Request) -> Response:
        """JSON endpoint backing the select2 widgets used by `RelationField`s
        in forms (`fields/form/relation.html`/`static/js/form.js`).

        Either resolves a set of `pks` (initial selection) or runs a
        full-text search (`q`) with pagination (`skip`/`limit`). Results are
        always sorted by primary key.
        """
        key = request.path_params.get("key")
        view = self._find_view_by_key(key)
        if not view.is_accessible(request):
            return JSONResponse(None, status_code=HTTP_403_FORBIDDEN)
        request.state.action = RequestAction.RELATION_LOOKUP
        pks = request.query_params.getlist("pks")
        if pks:
            items = await view.find_by_pks(request, pks)
            total = len(items)
        else:
            skip = max(0, int(request.query_params.get("skip") or "0"))
            limit = min(100, max(0, int(request.query_params.get("limit") or "20")))
            q = request.query_params.get("q") or None
            items = await view.find_all(
                request=request,
                skip=skip,
                limit=limit,
                q=q,
                sorts=[(not_none(view.pk_attr), "asc")],
            )
            total = await view.count(request=request, q=q)
        serialized_items = [
            (
                await view.serialize(
                    item,
                    request,
                    include_relationships=False,
                    include_select2=True,
                )
            )
            for item in items
        ]
        return JSONResponse({"items": serialized_items, "total": total})

    @route("/_api/{key}/inline-edit", methods=["GET", "POST"], name="inline-edit")
    async def _handle_inline_edit(self, request: Request) -> Response:
        """Backs the list-page inline-edit popover
        (`static/js/list.js` `initInlineEdit`, `templates/inline-edit/popover.html`).

        Runs under `RequestAction.INLINE_EDIT`, which `is_form()` treats as a
        form request, so field serialization/parsing and asset gating behave
        exactly as on the edit page. GET renders the field's `form_template`
        fragment, populated with the row's current value, for the client to
        inject into the popover body. POST parses, validates, and persists
        only the submitted field: `request.state.inline_edit_field` narrows
        `get_fields_list` to the edited field, so the unchanged `view.edit()`
        pipeline (validation, backend data arrangement and population, event
        `old_data`) reads and writes that single field. A failed save
        re-renders the fragment with the submitted value and its errors,
        mirroring how the edit page re-renders its form; on success the
        client fetches the `inline-edit-row` endpoint to swap the row.
        """
        request.state.action = RequestAction.INLINE_EDIT
        key = request.path_params.get("key")
        view = self._find_view_by_key(key)
        if not view.is_accessible(request) or not view.can_edit(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        pk = request.query_params.get("pk")
        field_name = request.query_params.get("field")
        # 403, not 400: an unknown/disallowed field name should not reveal
        # which fields exist.
        if not field_name or field_name not in (view.inline_editable_fields or []):
            raise HTTPException(HTTP_403_FORBIDDEN)
        # From here on every get_fields_list call sees only the edited field.
        request.state.inline_edit_field = field_name
        field = view._field_by_name(request, field_name)
        if field is None:
            raise HTTPException(HTTP_403_FORBIDDEN)
        obj = await view.find_by_pk(request, pk)
        if obj is None:
            raise HTTPException(HTTP_404_NOT_FOUND)

        if request.method == "GET":
            serialized = await view.serialize(obj, request)
            return self._render_inline_edit_field(
                request, view, field, serialized.get(field_name)
            )

        form = await request.form()
        value = await field.parse_form_data(request, form)
        data = {field.name: value}
        try:
            await view.validate_fields(request, data)
            obj = await view.edit(request, pk, data)
        except FormValidationError as exc:
            # Same policy as the edit page: re-render the form fragment with
            # the submitted value and the validation errors, status 422.
            return self._render_inline_edit_field(
                request, view, field, value, errors=exc.errors, status_code=HTTP_422
            )
        except HTTPException:
            raise
        except Exception:
            # The fragment, not the HTML error page: the client renders the
            # response inside the open popover, keeping the typed value.
            _log.exception(
                "inline-edit: key=%r pk=%r field=%r failed", key, pk, field_name
            )
            return self._render_inline_edit_field(
                request,
                view,
                field,
                value,
                errors={field.name: gettext("Something went wrong!")},
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            )

        obj_repr = await view.repr(obj, request)
        return JSONResponse(
            {
                "pk": await view.get_serialized_pk_value(request, obj),
                "field": field.name,
                "msg": gettext(
                    'The field "%(label)s" of "%(repr)s" was updated successfully.'
                )
                % {"label": field.label, "repr": obj_repr},
            }
        )

    def _render_inline_edit_field(
        self,
        request: Request,
        view: BaseModelView,
        field: BaseField,
        data: Any,
        errors: Mapping[Any, Any] | None = None,
        status_code: int = 200,
    ) -> Response:
        """Renders the inline-edit popover fragment (`inline-edit/field.html`):
        the field's `form_template` populated with `data`, plus any messages
        keyed to other fields (cross-field `validate` hooks), each prefixed
        with that field's label. Serves the popover GET and the 422/500
        re-render after a failed save.
        """
        errors = errors or {}
        # `get_fields_list` is narrowed to the edited field here, so labels
        # for cross-field messages must come from the full field list.
        labels = {f.name: f.label for f in view._all_fields}
        other_errors = [
            (labels.get(name, str(name)), str(message))
            for name, message in errors.items()
            if name != field.name
        ]
        html = self.templates.env.get_template("inline-edit/field.html").render(
            {
                "field": field,
                "data": data,
                "error": errors.get(field.name),
                "other_errors": other_errors,
                "input_group_prepend": None,
                "input_group_append": None,
                "input_group_flat": None,
            },
            request=request,
        )
        return HTMLResponse(html, status_code=status_code)

    @route("/_api/{key}/inline-edit/row", methods=["GET"], name="inline-edit-row")
    async def _render_inline_edit_row(self, request: Request) -> Response:
        """Renders a single list-table `<tr>` for `pk`.

        Runs under `RequestAction.LIST` and renders `_list_row.html`, the
        same template the list page's row loop uses, honoring the list-state
        query params (`cols`, ...) so the markup matches the surrounding
        table. Called by the inline-edit client to swap the edited row in
        place after a successful save, and callable on its own to refresh a
        row after an out-of-band change.
        """
        request.state.action = RequestAction.LIST
        key = request.path_params.get("key")
        view = self._find_view_by_key(key)
        if not view.is_accessible(request):
            raise HTTPException(HTTP_403_FORBIDDEN)
        pk = request.query_params.get("pk")
        obj = await view.find_by_pk(request, pk)
        if obj is None:
            raise HTTPException(HTTP_404_NOT_FOUND)
        list_params = view._parse_list_params(request)
        row = await view.serialize(obj, request)
        row_actions = {
            row[not_none(view.pk_attr)]: await view.get_row_actions_for_obj(
                request, obj
            )
        }
        html = self.templates.env.get_template("_list_row.html").render(
            {
                "view": view,
                "fields": self._list_display_fields(request, view, list_params),
                "row": row,
                "row_actions": row_actions,
            },
            request=request,
        )
        return HTMLResponse(html)

    @staticmethod
    def _list_display_fields(
        request: Request, view: BaseModelView, list_params: Any
    ) -> list[BaseField]:
        """Fields rendered as list-table columns, honoring the ``cols``
        query param. Shared by the list page and the `inline-edit-row`
        endpoint so a swapped-in row shows the same columns as the table."""
        all_fields = view.get_fields_list(request)
        if list_params.visible_cols is None:
            return list(all_fields)
        visible_set = set(list_params.visible_cols)
        return [f for f in all_fields if f.name in visible_set]

    @route(
        "/_files/{storage}/{path:path}",
        methods=["GET"],  # Read-only: other verbs must not reach the storage backend.
        name="file",
    )
    async def _serve_file(self, request: Request) -> Response:
        """Serve a stored file through its storage backend (route
        ``/_files/{storage}/{path}``). This is how `LocalStorage` files are
        exposed without a `StaticFiles` mount. Going through the admin app
        means the auth middleware (when configured) also covers uploads.
        """
        try:
            storage = get_storage(request.path_params["storage"])
            return await storage.serve(request, request.path_params["path"])
        except (UnknownStorageError, NotImplementedError) as err:
            raise HTTPException(HTTP_404_NOT_FOUND) from err

    def _export_failure_redirect_url(
        self, request: Request, view: BaseModelView
    ) -> str:
        """Build the list-page URL to bounce back to on export failure.

        Carries over every query param the export request was made with
        (``q``, ``filter``, ``sort``, ...) except ``format``, so the user
        lands back on the exact filtered/sorted view they tried to export
        rather than a blank list.
        """
        base = str(request.url_for(self.route_name + ":list", key=view.key))
        params = [
            (k, v) for k, v in request.query_params.multi_items() if k != "format"
        ]
        qs = urlencode(params)
        return base + ("?" + qs if qs else "")

    @route("/_api/{key}/export", methods=["GET"], name="export")
    async def _render_export(self, request: Request) -> Response:
        """Export the currently filtered/sorted list of records.

        Accepts the same list-state query parameters as the list page
        (``q``, ``filter``, ``sort``) and streams back the chosen format.
        When visible file fields are present, the response is a ZIP archive
        containing the data file plus all referenced files under ``assets/``.

        The ``scope`` query param controls how many rows are exported:
        ``"all"`` (default) exports every row matching the current
        filter/search, ignoring pagination. ``"page"`` restricts the export
        to the single page identified by the ``page``/``page_size`` params,
        mirroring what's currently on screen.
        """
        request.state.action = RequestAction.EXPORT
        key = request.path_params.get("key")
        scope = request.query_params.get("scope", "all")
        _log.debug("export request: key=%s scope=%s", key, scope)
        view = self._find_view_by_key(key)
        if not view.is_accessible(request) or not view.can_export(request):
            _log.warning("export denied: key=%s (permission check failed)", key)
            raise HTTPException(HTTP_403_FORBIDDEN)
        fmt = request.query_params.get("format")
        _log.debug("export format requested: %s", fmt)
        exporter = next(
            (e for e in view.exporters if (e.format_key or e.extension) == fmt), None
        )
        list_url_for_view = self._export_failure_redirect_url(request, view)
        if exporter is None:
            _log.warning(
                "export rejected: unknown/disabled format %r for key=%s",
                fmt,
                key,
            )
            flash(
                request,
                gettext("Unknown export format %(format)s") % {"format": fmt},
                "error",
            )
            return RedirectResponse(list_url_for_view, status_code=HTTP_303_SEE_OTHER)
        list_params = view._parse_list_params(request)
        _log.info(
            "export starting: view=%s format=%s q=%r sorts=%r",
            key,
            fmt,
            list_params.q,
            list_params.sorts,
        )
        if scope == "page":
            skip = (
                (list_params.page - 1) * list_params.page_size
                if list_params.page_size > 0
                else 0
            )
            limit = list_params.page_size
        else:
            skip = 0
            limit = -1
        if self.export_config.max_rows is not None:
            total = await view.count(
                request=request, q=list_params.q, filters=list_params.filters
            )
            # The number of rows this export will actually produce: the full
            # match count for scope "all", the remainder of the current page
            # otherwise. A non-positive limit means "no page size cap" (e.g.
            # a page_size of -1 for "show all"), so only a positive limit
            # shrinks the count.
            export_total = max(0, total - skip)
            if limit > 0:
                export_total = min(export_total, limit)
            if export_total > self.export_config.max_rows:
                _log.warning(
                    "export rejected: %d rows > max_rows=%d for key=%s",
                    export_total,
                    self.export_config.max_rows,
                    key,
                )
                flash(
                    request,
                    gettext(
                        "Export would return %(count)d rows, which exceeds the "
                        "configured maximum of %(max)d. Apply a filter to narrow "
                        "the result set."
                    )
                    % {"count": export_total, "max": self.export_config.max_rows},
                    "error",
                )
                return RedirectResponse(
                    list_url_for_view, status_code=HTTP_303_SEE_OTHER
                )
        request.state.export_type = exporter
        items = await view.find_all(
            request=request,
            skip=skip,
            limit=limit,
            q=list_params.q,
            sorts=list_params.sorts,
            filters=list_params.filters,
        )
        _log.debug("export query returned %d item(s)", len(items))
        rows = [await view.serialize(item, request) for item in items]
        export_fields = list(view.get_fields_list(request))
        _log.debug(
            "export fields resolved: %d field(s) (%s)",
            len(export_fields),
            [f.name for f in export_fields],
        )
        export_ctx = ExportContext(
            fields=export_fields,
            rows=rows,
            view=view,
            request=request,
            filename=view.key or "export",
            export_config=self.export_config,
        )
        await view._emit_before_export(request, exporter, items, export_ctx)
        _log.debug("export building response: format=%s rows=%d", fmt, len(rows))
        response = await exporter.build_response(export_ctx)
        await view._emit_after_export(request, exporter, items, export_ctx)
        _log.info("export complete: view=%s format=%s rows=%d", key, fmt, len(rows))
        return response

    async def _execute_import(
        self,
        importer: "BaseImporter",
        ctx: "ImportContext",
        fields: list[BaseField],
        field_by_header: dict[str, BaseField],
        skip_pk: bool,
        request: Request,
        view: "BaseModelView",
        dry_run: bool,
    ) -> "ImportResult":
        result = ImportResult(dry_run=dry_run)
        row_num = 0
        async for row in importer.parse(ctx):
            row_num += 1
            result.rows_total += 1
            _log.debug("import row %d: parsing", row_num)
            try:
                data = await self._parse_import_row(
                    row, fields, field_by_header, skip_pk, view.pk_attr, ctx
                )
                # A None pk (skipped or absent column) means the backend
                # auto-generates it, so it must not trip the required check.
                skip_validation = (
                    (view.pk_attr,)
                    if view.pk_attr and (skip_pk or data.get(view.pk_attr) is None)
                    else ()
                )
                await view.validate_fields(request, data, exclude=skip_validation)
                if dry_run:
                    result.rows_skipped += 1
                    _log.debug("import row %d: skipped (dry_run)", row_num)
                else:
                    await view.create(request, data)
                    result.rows_created += 1
                    _log.debug("import row %d: created", row_num)
            except FormValidationError as exc:
                for raw_field_name, msg in exc.errors.items():
                    field_name: str | None = (
                        None if isinstance(raw_field_name, int) else raw_field_name
                    )
                    result.errors.append(
                        ImportRowError(row=row_num, field=field_name, message=str(msg))
                    )
                    _log.warning(
                        "import row %d validation error, field=%r: %s",
                        row_num,
                        field_name,
                        msg,
                    )
            except Exception as exc:
                _log.error(
                    "import row %d unexpected error (%s): %s",
                    row_num,
                    type(exc).__name__,
                    exc,
                    exc_info=True,
                )
                result.errors.append(
                    ImportRowError(
                        row=row_num,
                        field=None,
                        message=gettext(
                            "An unexpected error occurred while processing this row."
                        ),
                    )
                )
        return result

    async def _parse_import_row(
        self,
        row: dict[str, Any],
        fields: list[BaseField],
        field_by_header: dict[str, BaseField],
        skip_pk: bool,
        pk_attr: str | None,
        ctx: "ImportContext",
    ) -> dict[str, Any]:
        data: dict[str, Any] = {}
        unknown_headers: list[str] = []
        for header, value in row.items():
            matched_field: BaseField | None = field_by_header.get(header)
            if matched_field is None:
                unknown_headers.append(header)
                continue
            data[matched_field.name] = await matched_field.parse_import_value(
                value, ctx
            )
        if unknown_headers:
            _log.debug("import row: ignored unknown headers: %s", unknown_headers)
        for field in fields:
            if field.name not in data:
                data[field.name] = None
        if skip_pk and pk_attr and pk_attr in data:
            data[pk_attr] = None  # Allow backend to auto-generate PK
            _log.debug("import row: dropped pk column '%s'", pk_attr)
        return data

    async def _check_import_row_cap(
        self,
        importer: "BaseImporter",
        ctx: "ImportContext",
        key: str | None,
    ) -> JSONResponse | None:
        """Reject the upload when it holds more rows than ``max_rows`` allows.

        The cap must fire before any record is created, so the file is counted
        in a separate parse that stops as soon as the cap is crossed. Parsing
        twice stays cheap because the upload is already bounded by
        ``max_upload_size``. Returns the error response to send, or ``None``
        when the import may proceed.
        """
        if self.import_config.max_rows is None:
            return None
        row_count = 0
        try:
            async for _ in importer.parse(ctx):
                row_count += 1
                if row_count > self.import_config.max_rows:
                    break
        except Exception as exc:
            _log.warning(
                "import failed while counting rows for key=%s: %s",
                key,
                exc,
                exc_info=True,
            )
            return JSONResponse(
                {
                    "error": gettext(
                        "An error occurred while importing the file. Please check the file format and try again."
                    )
                },
                status_code=HTTP_400_BAD_REQUEST,
            )
        if row_count > self.import_config.max_rows:
            _log.warning(
                "import rejected: file exceeds max_rows=%d for key=%s",
                self.import_config.max_rows,
                key,
            )
            return JSONResponse(
                {
                    "error": gettext(
                        "Import file exceeds the configured maximum of "
                        "%(max)d rows. Split the file into smaller batches "
                        "and try again."
                    )
                    % {"max": self.import_config.max_rows}
                },
                status_code=HTTP_400_BAD_REQUEST,
            )
        return None

    @route("/_api/{key}/import", methods=["POST"], name="import")
    async def _render_import(self, request: Request) -> Response:
        """Import records from an uploaded CSV/Excel/JSON file.

        Returns a JSON summary with row counts and per-row validation errors.
        Pass ``?dry_run=1`` to validate without persisting anything.
        Pass ``?skip_pk=1`` to drop the primary key column so the backend auto-generates it.
        """
        request.state.action = RequestAction.IMPORT
        key = request.path_params.get("key")
        _log.debug("import request: key=%s", key)
        view = self._find_view_by_key(key)
        if not view.is_accessible(request) or not view.can_import(request):
            _log.warning("import denied: key=%s (permission check failed)", key)
            raise HTTPException(HTTP_403_FORBIDDEN)
        form = await request.form()
        fmt = form.get("format")
        _log.debug("import format requested: %s", fmt)
        importer = next(
            (i for i in view.importers if (i.format_key or i.extension) == fmt), None
        )
        if importer is None:
            _log.warning(
                "import rejected: unknown/disabled format %r for key=%s",
                fmt,
                key,
            )
            return JSONResponse(
                {"error": gettext("Unknown import format %(fmt)s") % {"fmt": fmt}},
                status_code=HTTP_400_BAD_REQUEST,
            )
        request.state.import_type = importer
        upload = form.get("file")
        if upload is None or not isinstance(upload, UploadFile):
            _log.warning("import rejected: no file in request for key=%s", key)
            return JSONResponse(
                {"error": gettext("No file uploaded")},
                status_code=HTTP_400_BAD_REQUEST,
            )
        if upload.size is None or upload.size > self.import_config.max_upload_size:
            _log.warning(
                "import rejected: upload too large or size unknown (%s bytes; limit %d) for key=%s",
                upload.size,
                self.import_config.max_upload_size,
                key,
            )
            return JSONResponse(
                {
                    "error": gettext(
                        "Upload too large (%(size)s bytes; maximum %(max)s bytes)."
                    )
                    % {
                        "size": f"{upload.size:,}"
                        if upload.size is not None
                        else "unknown",
                        "max": f"{self.import_config.max_upload_size:,}",
                    }
                },
                status_code=HTTP_400_BAD_REQUEST,
            )
        content = await upload.read()
        _log.debug(
            "import file received: filename=%r size=%d bytes",
            upload.filename,
            len(content),
        )
        fields = list(view.get_fields_list(request))
        field_by_header: dict[str, BaseField] = {}
        for field in fields:
            field_by_header[field.label or field.name] = field
            field_by_header[field.name] = field
        dry_run = request.query_params.get("dry_run") in ("1", "true", "yes")
        skip_pk = request.query_params.get("skip_pk") in ("1", "true", "yes")
        _log.info(
            "import starting: view=%s format=%s fields=%d dry_run=%s skip_pk=%s",
            key,
            fmt,
            len(fields),
            dry_run,
            skip_pk,
        )
        import_ctx = ImportContext(
            fields=fields,
            content=content,
            view=view,
            request=request,
            dry_run=dry_run,
        )
        row_cap_error = await self._check_import_row_cap(importer, import_ctx, key)
        if row_cap_error is not None:
            return row_cap_error
        await view._emit_before_import(request, importer, import_ctx)
        try:
            result = await self._execute_import(
                importer,
                import_ctx,
                fields,
                field_by_header,
                skip_pk,
                request,
                view,
                dry_run,
            )
        except Exception as exc:
            _log.warning(
                "import failed with unexpected error for key=%s: %s",
                key,
                exc,
                exc_info=True,
            )
            return JSONResponse(
                {
                    "error": gettext(
                        "An error occurred while importing the file. Please check the file format and try again."
                    )
                },
                status_code=HTTP_400_BAD_REQUEST,
            )
        await view._emit_after_import(request, importer, result, import_ctx)
        if result.has_errors:
            _log.warning(
                "import finished with errors: view=%s total=%d created=%d skipped=%d errors=%d",
                key,
                result.rows_total,
                result.rows_created,
                result.rows_skipped,
                len(result.errors),
            )
        else:
            _log.info(
                "import complete: view=%s total=%d created=%d skipped=%d",
                key,
                result.rows_total,
                result.rows_created,
                result.rows_skipped,
            )
        return JSONResponse(
            {
                "rows_total": result.rows_total,
                "rows_created": result.rows_created,
                "rows_updated": result.rows_updated,
                "rows_skipped": result.rows_skipped,
                "has_errors": result.has_errors,
                "errors": [
                    {"row": e.row, "field": e.field, "message": e.message}
                    for e in result.errors
                ],
                "dry_run": result.dry_run,
            }
        )

    @route("/_api/{key}/action", methods=["POST"], name="action")
    async def handle_action(self, request: Request) -> Response:
        request.state.action = RequestAction.ACTION
        try:
            key = request.path_params.get("key")
            pks = request.query_params.getlist("pks")
            name = not_none(request.query_params.get("name"))
            is_select_all = request.query_params.get("all") == "1"
            _log.debug(
                "action request: key=%s name=%r pks=%s all=%s",
                key,
                name,
                pks,
                is_select_all,
            )
            view = self._find_view_by_key(key)
            if not view.is_accessible(request):
                _log.warning(
                    "action denied: key=%s name=%r (permission check failed)",
                    key,
                    name,
                )
                raise ActionFailed(_("Forbidden"))
            list_query = QueryParams(
                (request.query_params.get("_list_query") or "").lstrip("?")
            )
            try:
                filters = view._parse_filter_param(request, list_query)
            except HTTPException as exc:
                raise ActionFailed(str(exc.detail)) from exc
            q = list_query.get("q") or None
            selection = ActionSelection(
                view, request, None if is_select_all else pks, filters, q
            )
            handler_return = await view.handle_action(request, selection, name)
            _log.info(
                "action complete: key=%s name=%r all=%s pks=%s",
                key,
                name,
                is_select_all,
                pks,
            )
            if isinstance(handler_return, Response):
                return handler_return
            fallback = str(request.url_for(self.route_name + ":list", key=key))
            redirect_url = safe_redirect_url(
                request.query_params.get("_origin") or fallback, request, fallback
            )
            return JSONResponse({"redirect": redirect_url})
        except ActionFailed as exc:
            _log.warning(
                "action failed: key=%s name=%r: %s",
                request.path_params.get("key"),
                request.query_params.get("name"),
                exc.msg,
            )
            return JSONResponse({"msg": exc.msg}, status_code=HTTP_400_BAD_REQUEST)

    @route("/_api/{key}/row-action", methods=["POST"], name="row-action")
    async def handle_row_action(self, request: Request) -> Response:
        request.state.action = RequestAction.ROW_ACTION
        try:
            key = request.path_params.get("key")
            pk = request.query_params.get("pk")
            name = request.query_params.get("name")
            if not name:  # pragma: no cover
                raise ActionFailed(_("Missing 'name' parameter"))
            _log.debug(
                "row-action request: key=%s name=%r pk=%s",
                key,
                name,
                pk,
            )
            view = self._find_view_by_key(key)
            if not view.is_accessible(request):
                _log.warning(
                    "row-action denied: key=%s name=%r pk=%s (permission check failed)",
                    key,
                    name,
                    pk,
                )
                raise ActionFailed(_("Forbidden"))
            handler_return = await view.handle_row_action(request, pk, name)
            _log.info("row-action complete: key=%s name=%r pk=%s", key, name, pk)
            if isinstance(handler_return, Response):
                return handler_return
            fallback = str(request.url_for(self.route_name + ":list", key=key))
            origin = request.query_params.get("_origin")
            if name == "delete" and origin:
                # A "delete" row action can be triggered from the item's own
                # detail page, which no longer exists once deleted. Detect
                # that case and unwrap the detail page's own `_origin` (the
                # filtered list it was reached from) instead of dropping
                # back to a bare, unfiltered list.
                parsed_origin = urlparse(origin)
                detail_path = urlparse(
                    str(request.url_for(self.route_name + ":detail", key=key))
                ).path
                if parsed_origin.path == detail_path:
                    nested_origin = parse_qs(parsed_origin.query).get("_origin")
                    origin = nested_origin[0] if nested_origin else None
            redirect_url = safe_redirect_url(origin or fallback, request, fallback)
            return JSONResponse({"redirect": redirect_url})
        except ActionFailed as exc:
            _log.warning(
                "row-action failed: key=%s name=%r pk=%s: %s",
                request.path_params.get("key"),
                request.query_params.get("name"),
                request.query_params.get("pk"),
                exc.msg,
            )
            return JSONResponse({"msg": exc.msg}, status_code=HTTP_400_BAD_REQUEST)

    @route("/{key}/list", methods=["GET"], name="list")
    async def _render_list(self, request: Request) -> Response:
        request.state.action = RequestAction.LIST
        key = request.path_params.get("key")
        _log.debug("list request: key=%s", key)
        view = self._find_view_by_key(key)
        if not view.is_accessible(request):
            _log.warning("list denied: key=%s (permission check failed)", key)
            raise HTTPException(HTTP_403_FORBIDDEN)
        list_params = view._parse_list_params(request)
        _log.debug(
            "list params: key=%s page=%s page_size=%s q=%r sorts=%r",
            key,
            list_params.page,
            list_params.page_size,
            list_params.q,
            list_params.sorts,
        )
        skip = (
            (list_params.page - 1) * list_params.page_size
            if list_params.page_size > 0
            else 0
        )
        items = await view.find_all(
            request=request,
            skip=skip,
            limit=list_params.page_size,
            q=list_params.q,
            sorts=list_params.sorts,
            filters=list_params.filters,
        )
        total = await view.count(
            request=request, q=list_params.q, filters=list_params.filters
        )
        rows = []
        row_actions: dict[Any, list[dict[str, Any]]] = {}
        for item in items:
            row = await view.serialize(item, request)
            rows.append(row)
            row_actions[
                row[not_none(view.pk_attr)]
            ] = await view.get_row_actions_for_obj(request, item)
        page_size = (
            list_params.page_size if list_params.page_size > 0 else max(total, 1)
        )
        total_pages = max(-(-total // page_size), 1)
        range_start = 0 if total == 0 else (list_params.page - 1) * page_size + 1
        range_end = min(list_params.page * page_size, total)
        all_fields = view.get_fields_list(request)
        display_fields = self._list_display_fields(request, view, list_params)
        _log.info(
            "list rendered: key=%s page=%d/%d rows=%d total=%d q=%r filters=%r",
            key,
            list_params.page,
            total_pages,
            len(rows),
            total,
            list_params.q,
            list_params.filters,
        )
        filter_logic, filter_chips = view._active_filter_chips(request, list_params)
        return self._template_response(
            request=request,
            name=view.list_template,
            context={
                "view": view,
                "title": view.title(request),
                "_actions": await view.get_all_actions(request),
                "row_actions": row_actions,
                "fields": display_fields,
                "all_fields": all_fields,
                "list_params": list_params,
                "filter_logic": filter_logic,
                "filter_chips": filter_chips,
                "filter_builder_fields": view._filter_builder_fields(request),
                "raw_filter": request.query_params.get("filter"),
                "rows": rows,
                "total": total,
                "total_pages": total_pages,
                "range_start": range_start,
                "range_end": range_end,
            },
        )

    @route("/{key}/detail", methods=["GET"], name="detail")
    async def _render_detail(self, request: Request) -> Response:
        request.state.action = RequestAction.DETAIL
        key = request.path_params.get("key")
        pk = request.query_params.get("pk")
        _log.debug("detail request: key=%s pk=%s", key, pk)
        view = self._find_view_by_key(key)
        if not view.is_accessible(request) or not view.can_view_detail(request):
            _log.warning(
                "detail denied: key=%s pk=%s (permission check failed)",
                key,
                pk,
            )
            raise HTTPException(HTTP_403_FORBIDDEN)
        obj = await view.find_by_pk(request, pk)
        if obj is None:
            _log.warning("detail not found: key=%s pk=%s", key, pk)
            raise HTTPException(HTTP_404_NOT_FOUND)
        _log.info("detail rendered: key=%s pk=%s", key, pk)
        return self._template_response(
            request=request,
            name=view.detail_template,
            context={
                "title": view.title(request),
                "view": view,
                "raw_obj": obj,
                "_actions": await view.get_row_actions_for_obj(request, obj),
                "obj": await view.serialize(obj, request),
                "inlines": await self._detail_inlines_context(request, view, obj),
            },
        )

    async def _detail_inlines_context(
        self,
        request: Request,
        view: "BaseModelView",
        parent: Any,
    ) -> list[dict[str, Any]]:
        """Build the template context for inline tables on the detail page.

        Unlike the create/edit context, this fetches only existing rows. No
        extra empty rows are added, since the detail page is read-only.
        """
        result = []
        for inline in view._inline_instances:
            existing = await inline.find_by_parent(request, parent)
            rows = [
                {
                    "pk": await inline.get_pk_value(request, item),
                    "obj": await inline.serialize(item, request),
                }
                for item in existing
            ]
            result.append({"inline": inline, "rows": rows})
        return result

    @route("/{key}/create", methods=["GET", "POST"], name="create")
    async def _render_create(self, request: Request) -> Response:
        request.state.action = RequestAction.CREATE
        key = request.path_params.get("key")
        _log.debug("create request: key=%s method=%s", key, request.method)
        view = self._find_view_by_key(key)
        config = {"title": view.title(request), "view": view}
        if not view.is_accessible(request) or not view.can_create(request):
            _log.warning("create denied: key=%s (permission check failed)", key)
            raise HTTPException(HTTP_403_FORBIDDEN)
        if request.method == "GET":
            _log.debug("create GET: key=%s serving empty form", key)
            config["obj"] = await self._create_default_obj(request, view)
            config["inlines"] = await self._inlines_context(request, view)
            await self._render_form_body(request, view, config["obj"], None, config)
            return self._template_response(
                request=request,
                name=view.create_template,
                context=config,
            )
        form = await request.form()
        _log.debug("create POST: key=%s parsing form data", key)
        dict_obj = await self._parse_form_data(request, form, view)
        _log.debug("create POST: key=%s form values=%s", key, dict_obj)
        inline_data, inline_errors = await self._parse_inline_forms(request, view, form)
        if inline_errors:
            _log.warning(
                "create inline validation errors: key=%s inlines=%s",
                key,
                list(inline_errors.get("inlines", {}).keys()),
            )
            config.update(
                {
                    "errors": inline_errors,
                    "obj": dict_obj,
                    "inlines": await self._inlines_context(
                        request, view, inline_data=inline_data
                    ),
                }
            )
            await self._render_form_body(request, view, dict_obj, inline_errors, config)
            return self._template_response(
                request=request,
                name=view.create_template,
                context=config,
                status_code=HTTP_422,
            )
        try:
            await view.validate_fields(request, dict_obj)
            await self._process_file_fields(request, view, dict_obj)
            obj = await view.create(request, dict_obj)
            await self._save_inlines(request, view, obj, inline_data)
        except FormValidationError as exc:
            all_errors = dict(exc.errors)
            _log.warning(
                "create validation failed: key=%s errors=%s",
                key,
                list(all_errors.keys()),
            )
            config.update(
                {
                    "errors": all_errors,
                    "obj": dict_obj,
                    "inlines": await self._inlines_context(
                        request, view, inline_data=inline_data
                    ),
                }
            )
            await self._render_form_body(request, view, dict_obj, all_errors, config)
            return self._template_response(
                request=request,
                name=view.create_template,
                context=config,
                status_code=HTTP_422,
            )
        pk = await view.get_pk_value(request, obj)
        _log.info("create success: key=%s pk=%s", key, pk)
        obj_repr = await view.repr(obj, request)
        flash(
            request,
            gettext('The item "%(repr)s" was added successfully.') % {"repr": obj_repr},
            "success",
        )
        fallback = str(request.url_for(self.route_name + ":list", key=view.key))
        origin = request.query_params.get("_origin")
        url: Any = safe_redirect_url(origin, request, fallback) if origin else fallback
        if form.get("_continue_editing", None) is not None:
            url = request.url_for(
                self.route_name + ":edit", key=view.key
            ).include_query_params(pk=str(pk))
            if origin:
                url = url.include_query_params(_origin=origin)
        elif form.get("_add_another", None) is not None:
            url = request.url
        return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    @route("/{key}/edit", methods=["GET", "POST"], name="edit")
    async def _render_edit(self, request: Request) -> Response:
        request.state.action = RequestAction.EDIT
        key = request.path_params.get("key")
        pk = request.query_params.get("pk")
        _log.debug("edit request: key=%s pk=%s method=%s", key, pk, request.method)
        view = self._find_view_by_key(key)
        if not view.is_accessible(request) or not view.can_edit(request):
            _log.warning("edit denied: key=%s pk=%s (permission check failed)", key, pk)
            raise HTTPException(HTTP_403_FORBIDDEN)
        obj = await view.find_by_pk(request, pk)
        if obj is None:
            _log.warning("edit not found: key=%s pk=%s", key, pk)
            raise HTTPException(HTTP_404_NOT_FOUND)
        config = {
            "title": view.title(request),
            "view": view,
            "raw_obj": obj,
            "obj": await view.serialize(obj, request),
        }
        if request.method == "GET":
            _log.debug("edit GET: key=%s pk=%s serving form", key, pk)
            config["inlines"] = await self._inlines_context(request, view, parent=obj)
            await self._render_form_body(request, view, config["obj"], None, config)
            return self._template_response(
                request=request,
                name=view.edit_template,
                context=config,
            )
        form = await request.form()
        _log.debug("edit POST: key=%s pk=%s parsing form data", key, pk)
        dict_obj = await self._parse_form_data(request, form, view)
        _log.debug("edit POST: key=%s pk=%s form values=%s", key, pk, dict_obj)
        inline_data, inline_errors = await self._parse_inline_forms(request, view, form)
        if inline_errors:
            _log.warning(
                "edit inline validation errors: key=%s pk=%s inlines=%s",
                key,
                pk,
                list(inline_errors.get("inlines", {}).keys()),
            )
            config.update(
                {
                    "errors": inline_errors,
                    "obj": dict_obj,
                    "inlines": await self._inlines_context(
                        request, view, parent=obj, inline_data=inline_data
                    ),
                }
            )
            await self._render_form_body(request, view, dict_obj, inline_errors, config)
            return self._template_response(
                request=request,
                name=view.edit_template,
                context=config,
                status_code=HTTP_422,
            )
        try:
            await view.validate_fields(request, dict_obj)
            await self._process_file_fields(request, view, dict_obj, obj=obj)
            obj = await view.edit(request, pk, dict_obj)
            await self._save_inlines(request, view, obj, inline_data)
        except FormValidationError as exc:
            all_errors = dict(exc.errors)
            _log.warning(
                "edit validation failed: key=%s pk=%s errors=%s",
                key,
                pk,
                list(all_errors.keys()),
            )
            config.update(
                {
                    "errors": all_errors,
                    "obj": dict_obj,
                    "inlines": await self._inlines_context(
                        request, view, parent=obj, inline_data=inline_data
                    ),
                }
            )
            await self._render_form_body(request, view, dict_obj, all_errors, config)
            return self._template_response(
                request=request,
                name=view.edit_template,
                context=config,
                status_code=HTTP_422,
            )
        pk = await view.get_pk_value(request, obj)
        _log.info("edit success: key=%s pk=%s", key, pk)
        obj_repr = await view.repr(obj, request)
        flash(
            request,
            gettext('The item "%(repr)s" was changed successfully.')
            % {"repr": obj_repr},
            "success",
        )
        fallback = str(request.url_for(self.route_name + ":list", key=view.key))
        origin = request.query_params.get("_origin")
        url: Any = safe_redirect_url(origin, request, fallback) if origin else fallback
        if form.get("_continue_editing", None) is not None:
            url = request.url_for(
                self.route_name + ":edit", key=view.key
            ).include_query_params(pk=str(pk))
            if origin:
                url = url.include_query_params(_origin=origin)
        elif form.get("_add_another", None) is not None:
            url = request.url_for(self.route_name + ":create", key=view.key)
            if origin:
                url = url.include_query_params(_origin=origin)
        return RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)

    async def _render_error(
        self,
        request: Request,
        exc: Exception = HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR),
    ) -> Response:
        assert isinstance(exc, HTTPException)
        return self._template_response(
            request=request,
            name="error.html",
            context={"exc": exc},
            status_code=exc.status_code,
        )

    async def _parse_form_data(
        self,
        request: Request,
        form_data: FormData,
        view: BaseModelView,
    ) -> dict[str, Any]:
        data = {}
        for field in view.get_fields_list(request):
            if field.read_only:
                continue
            data[field.name] = await field.parse_form_data(request, form_data)
        return data

    async def _create_default_obj(
        self,
        request: Request,
        view: BaseModelView,
    ) -> dict[str, Any]:
        """Build a dict of initial form values from each field's ``default``.

        Each default runs through ``serialize_field_value`` so the create form
        receives the same value shape as the edit form. Relation fields are
        exempt: their defaults are already primary key values, which is what
        the form expects, while their serializer expects related objects.
        """
        obj: dict[str, Any] = {}
        for field in view.get_fields_list(request):
            value = await field.get_create_default(request)
            if isinstance(field, RelationField):
                obj[field.name] = value
            else:
                obj[field.name] = await view.serialize_field_value(
                    value, field, request
                )
        return obj

    def _inline_indices(self, form_data: FormData, prefix: str) -> list[int]:
        """Collect the numeric row indices present in the form for an inline."""
        indices: set[int] = set()
        for name in form_data:
            if not name.startswith(f"{prefix}."):
                continue
            rest = name[len(prefix) + 1 :]
            idx = rest.split(".", maxsplit=1)[0]
            if idx.isdigit():
                indices.add(int(idx))
        return sorted(indices)

    def _inline_row_is_empty(
        self,
        inline: "InlineModelView",
        form_data: FormData,
        index: int,
    ) -> bool:
        """Return True when a new inline row has no meaningful user input."""
        prefix = f"{inline._prefix()}.{index}."
        for field in inline.fields:
            name = f"{prefix}{field.name}"
            if form_data.get(name):
                return False
            if any(form_data.getlist(name)):
                return False
        return True

    async def _parse_inline_row_fields(
        self,
        request: Request,
        inline: "InlineModelView",
        form_data: FormData,
        row_prefix: str,
        validate: bool = True,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Parse the field values submitted for a single inline row, running
        each field's validation unless *validate* is `False` (rows flagged for
        deletion are not validated).

        Returns a tuple of ``(data, field_err)``.
        """
        data: dict[str, Any] = {}
        field_err: dict[str, Any] = {}
        for field in inline.get_fields_list(request):
            if field.read_only:
                continue
            original_id = field.id
            try:
                field.id = f"{row_prefix}{field.name}"
                if isinstance(field, CollectionField):
                    field._propagate_id()
                data[field.name] = await field.parse_form_data(request, form_data)
                if validate:
                    await field.validate(request, data[field.name])
            except Exception as exc:
                field_err[field.name] = str(exc)
            finally:
                field.id = original_id
                if isinstance(field, CollectionField):
                    field._propagate_id()
        return data, field_err

    async def _parse_inline_formset(
        self,
        request: Request,
        inline: "InlineModelView",
        form_data: FormData,
    ) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
        """Parse every row submitted for a single inline formset.

        Returns a tuple of ``(rows, row_errors)``.
        """
        prefix = inline._prefix()
        rows: list[dict[str, Any]] = []
        row_errors: dict[int, dict[str, Any]] = {}
        for idx in self._inline_indices(form_data, prefix):
            row_prefix = f"{prefix}.{idx}."
            pk = form_data.get(f"{row_prefix}pk") or None
            delete = form_data.get(f"{row_prefix}DELETE") in ("1", "on", "true")
            if (
                pk is None
                and not delete
                and self._inline_row_is_empty(inline, form_data, idx)
            ):
                continue
            data, field_err = await self._parse_inline_row_fields(
                request, inline, form_data, row_prefix, validate=not delete
            )
            rows.append(
                {
                    "index": idx,
                    "pk": pk,
                    "data": data,
                    "delete": delete,
                    "errors": field_err,
                }
            )
            if field_err:
                row_errors[idx] = field_err
        return rows, row_errors

    async def _parse_inline_forms(
        self,
        request: Request,
        view: BaseModelView,
        form_data: FormData,
    ) -> tuple[dict[str, list[dict[str, Any]]], dict[str | int, Any]]:
        """Parse every inline formset for *view*.

        Returns a tuple of ``(inline_data, errors)`` where ``inline_data`` is a
        mapping from inline key to a list of row dicts
        ``{"index", "pk", "data", "delete", "errors"}``. ``errors`` has the
        same shape used by [FormValidationError][starlette_admin.exceptions.FormValidationError]
        so that per-field inline validation failures can be rendered by the
        inline templates.
        """
        inline_data: dict[str, list[dict[str, Any]]] = {}
        errors: dict[str | int, Any] = {}
        for inline in view._inline_instances:
            key = not_none(inline.key)
            rows, row_errors = await self._parse_inline_formset(
                request, inline, form_data
            )
            inline_data[key] = rows
            if row_errors:
                errors.setdefault("inlines", {}).setdefault(key, {}).update(row_errors)
        return inline_data, errors

    async def _save_inline_row(
        self,
        request: Request,
        inline: "InlineModelView",
        row: dict[str, Any],
        parent: Any,
    ) -> tuple[str, Any]:
        """Persist a single inline row.

        Returns ``(op, obj)`` where *op* is ``"delete"``, ``"edit"``, or
        ``"create"`` and *obj* is the saved model instance (``None`` for
        deletes).
        """
        if row.get("delete"):
            if row.get("pk"):
                _log.debug("inline delete: key=%r pk=%r", inline.key, row["pk"])
                await inline.delete(request, [row["pk"]])
            return "delete", None
        if row.get("pk"):
            _log.debug("inline edit: key=%r pk=%r", inline.key, row["pk"])
            existing = await inline.find_by_pk(request, row["pk"])
            await self._process_file_fields(request, inline, row["data"], obj=existing)
            obj = await inline.edit(request, row["pk"], row["data"])
            return "edit", obj
        _log.debug("inline create: key=%r", inline.key)
        data = dict(row["data"])
        await self._process_file_fields(request, inline, data)
        fk_value = await inline.build_fk_value(request, parent)
        eff_fk = inline._get_fk_attr()
        if isinstance(eff_fk, tuple):
            data.update(fk_value)
        else:
            data[eff_fk] = fk_value
        obj = await inline.create(request, data)
        return "create", obj

    async def _save_inlines(
        self,
        request: Request,
        view: BaseModelView,
        parent: Any,
        inline_data: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Persist inline formset data after the parent object has been saved.

        Each row is either deleted, edited, or created. New rows get their
        ``fk_attr`` populated from
        [InlineModelView.build_fk_value][starlette_admin.views.InlineModelView.build_fk_value].

        If an inline row fails validation, its errors are attached to the row
        and a [FormValidationError][starlette_admin.exceptions.FormValidationError]
        is raised after attempting the remaining rows. On full success, a flash
        message is emitted per created or edited inline item.
        """
        errors: dict[str | int, Any] = {}
        successes: list[tuple[Any, str, Any]] = []
        _log.debug(
            "save inlines: %d inline(s) for view key=%s",
            len(view._inline_instances),
            view.key,
        )
        for inline in view._inline_instances:
            key = not_none(inline.key)
            for row in inline_data.get(key, []):
                try:
                    op, obj = await self._save_inline_row(request, inline, row, parent)
                    if op in ("create", "edit"):
                        successes.append((inline, op, obj))
                except FormValidationError as exc:
                    _log.warning(
                        "inline save error: key=%r row_index=%d fields=%s",
                        inline.key,
                        row["index"],
                        list(exc.errors.keys()),
                    )
                    row["errors"].update(exc.errors)
                    errors.setdefault("inlines", {}).setdefault(inline.key, {})[
                        row["index"]
                    ] = row["errors"]
        if errors:
            _log.warning(
                "save inlines: validation failed, view=%s affected_inlines=%s",
                view.key,
                list(errors.get("inlines", {}).keys()),
            )
            raise FormValidationError(errors)
        for inline, op, obj in successes:
            obj_repr = await inline.repr(obj, request)
            if op == "create":
                flash(
                    request,
                    gettext('The item "%(repr)s" was added successfully.')
                    % {"repr": obj_repr},
                    "success",
                )
            else:
                flash(
                    request,
                    gettext('The item "%(repr)s" was changed successfully.')
                    % {"repr": obj_repr},
                    "success",
                )

    async def _inline_rows_context(
        self,
        request: Request,
        inline: "InlineModelView",
        parent: Any = None,
        submitted_rows: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Build the template context for an inline's rows.

        On GET, renders existing rows from the database plus ``extra`` empty
        rows. On a validation-error re-render, renders exactly the rows that
        were submitted so the user sees their input again.
        """
        if submitted_rows is not None:
            return [
                {
                    "index": row["index"],
                    "pk": row.get("pk"),
                    "obj": row["data"],
                    "errors": row.get("errors", {}),
                    "delete": row.get("delete", False),
                    "is_extra": row.get("pk") is None,
                }
                for row in submitted_rows
            ]
        rows: list[dict[str, Any]] = []
        existing: Sequence[Any] = []
        if parent is not None:
            existing = await inline.find_by_parent(request, parent)
        for i, item in enumerate(existing):
            rows.append(
                {
                    "index": i,
                    "pk": await inline.get_pk_value(request, item),
                    "obj": await inline.serialize(item, request),
                    "errors": {},
                    "delete": False,
                    "is_extra": False,
                }
            )
        next_index = len(rows)
        for i in range(inline.extra):
            rows.append(
                {
                    "index": next_index + i,
                    "pk": None,
                    "obj": None,
                    "errors": {},
                    "delete": False,
                    "is_extra": True,
                }
            )
        return rows

    async def _inlines_context(
        self,
        request: Request,
        view: BaseModelView,
        parent: Any = None,
        inline_data: dict[str, list[dict[str, Any]]] | None = None,
    ) -> list[dict[str, Any]]:
        """Build the template context for every inline on a create/edit page."""
        return [
            {
                "inline": inline,
                "rows": await self._inline_rows_context(
                    request,
                    inline,
                    parent=parent,
                    submitted_rows=inline_data.get(not_none(inline.key))
                    if inline_data is not None
                    else None,
                ),
            }
            for inline in view._inline_instances
        ]

    async def _process_file_fields(
        self,
        request: Request,
        view: BaseModelView,
        data: dict[str, Any],
        obj: Any = None,
    ) -> None:
        """Handle the storage lifecycle of every `FileField`/`ImageField` with
        an attached storage, replacing the raw ``(upload(s), should_be_deleted)``
        tuple in `data` with the JSON metadata the backend should persist:

        - new upload → the upload is saved and the resulting `FileInfo` dict is stored;
        - "delete" checked → `None` (or `[]`) is stored;
        - neither → the current value is carried over unchanged.

        Uploads have already been validated by
        [validate_fields][starlette_admin.views.BaseModelView.validate_fields],
        which the create/edit routes run first, so a rejected form never leaves
        files behind. Fields without a storage keep their tuple value;
        processing them remains the backend's responsibility (the pre-storage
        behavior).
        """
        file_fields = [
            field
            for field in view.get_fields_list(request, include_nested=True)
            if isinstance(field, FileField)
            and field.storage is not None
            and not field.read_only
        ]
        if not file_fields:
            return
        _log.debug(
            "file fields: processing %d field(s) for key=%s",
            len(file_fields),
            view.key,
        )
        for field in file_fields:
            value, should_be_deleted = data[field.name]
            uploads = (
                list(value)
                if field.multiple
                else ([value] if value is not None else [])
            )
            old_value = await field.parse_obj(request, obj) if obj is not None else None
            if uploads:
                _log.debug(
                    "file upload: key=%s field=%r file(s)=%d",
                    view.key,
                    field.name,
                    len(uploads),
                )
                infos = [await self._store_upload(field, upload) for upload in uploads]
                data[field.name] = (
                    [info.to_dict() for info in infos]
                    if field.multiple
                    else infos[0].to_dict()
                )
            elif should_be_deleted:
                _log.debug(
                    "file delete: key=%s field=%r",
                    view.key,
                    field.name,
                )
                data[field.name] = [] if field.multiple else None
            else:
                data[field.name] = self._storable_file_value(field, old_value)

    async def _store_upload(self, field: FileField, upload: UploadFile) -> FileInfo:
        storage = not_none(field.storage)
        filename = secure_filename(upload.filename or "file")
        folder = field.upload_folder.strip("/")
        dest = f"{folder}/{filename}" if folder else filename
        info = await storage.save(upload, dest)
        return await field._post_store(info, upload)

    @staticmethod
    def _storable_file_value(field: FileField, value: Any) -> Any:
        """Normalize an unchanged file value back to its storable dict form."""
        if value is None:
            return [] if field.multiple else None
        if field.multiple and isinstance(value, (list, tuple)):
            return [v.to_dict() if isinstance(v, FileInfo) else v for v in value]
        return value.to_dict() if isinstance(value, FileInfo) else value

    def mount_to(self, app: Starlette) -> None:
        """Build the admin's Starlette app and mount it onto *app*.

        Validates that every `RelationField` (`HasOne`/`HasMany`) points to a
        registered view key before mounting, so misconfigured relations
        fail fast at startup instead of at request time.

        The built admin app is saved as [app][starlette_admin.base.BaseAdmin.app].
        Once mounted, further [add_view][starlette_admin.base.BaseAdmin.add_view]
        calls (and further calls to `mount_to` itself) raise `RuntimeError`,
        since routes/middleware have already been baked into `admin_app`.

        Parameters:
            app: The Starlette (or FastAPI) application to mount the admin onto.

        Raises:
            RuntimeError: If the admin has already been mounted.
        """
        if self._app is not None:
            raise RuntimeError("Admin has already been mounted with mount_to().")
        self._validate_relation_fields()
        admin_app = Starlette(
            routes=self.routes,
            middleware=self.middlewares,
            exception_handlers={HTTPException: self._render_error},
            debug=self.debug,
        )
        admin_app.state.ROUTE_NAME = self.route_name
        app.mount(
            self.base_url,
            app=admin_app,
            name=self.route_name,
        )
        admin_app.router.redirect_slashes = True
        self._app = admin_app
