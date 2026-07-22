from collections.abc import Callable, Sequence

from jinja2 import BaseLoader
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from starlette.routing import Route
from starlette_admin.auth import BaseAuthProvider
from starlette_admin.base import BaseAdmin
from starlette_admin.contrib.sqla.middleware import (
    DBSessionMiddleware,
    is_async_session_provider,
)
from starlette_admin.contrib.sqla.types import SessionProvider
from starlette_admin.export import ExportConfig
from starlette_admin.i18n import I18nConfig, TimezoneConfig
from starlette_admin.i18n import lazy_gettext as _
from starlette_admin.importers import ImportConfig
from starlette_admin.logging import get_logger
from starlette_admin.plugins import BasePlugin
from starlette_admin.theme import BaseTheme
from starlette_admin.views import CustomView

_log = get_logger(__name__)


class Admin(BaseAdmin):
    def __init__(
        self,
        session_provider: SessionProvider,
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
        theme: BaseTheme | None = None,
        auth_provider: BaseAuthProvider | None = None,
        secret_key: str | None = None,
        middlewares: Sequence[Middleware] | None = None,
        i18n_config: I18nConfig | None = None,
        timezone_config: TimezoneConfig | None = TimezoneConfig(),
        import_config: ImportConfig | None = None,
        export_config: ExportConfig | None = None,
        plugins: Sequence[BasePlugin] | None = None,
        debug: bool = False,
    ) -> None:
        super().__init__(
            title=title,
            base_url=base_url,
            route_name=route_name,
            logo_url=logo_url,
            login_logo_url=login_logo_url,
            favicon_url=favicon_url,
            templates_dir=templates_dir,
            additional_loaders=additional_loaders,
            static_dir=static_dir,
            index_view=index_view,
            theme=theme,
            auth_provider=auth_provider,
            secret_key=secret_key,
            middlewares=middlewares,
            i18n_config=i18n_config,
            timezone_config=timezone_config,
            import_config=import_config,
            export_config=export_config,
            plugins=plugins,
            debug=debug,
        )
        self.middlewares = [] if self.middlewares is None else list(self.middlewares)
        self.middlewares.insert(
            0, Middleware(DBSessionMiddleware, session_provider=session_provider)
        )
        engine_type = "async" if is_async_session_provider(session_provider) else "sync"
        source = (
            "sessionmaker"
            if isinstance(session_provider, (sessionmaker, async_sessionmaker))
            else "engine"
        )
        _log.info(
            "Admin initialized (engine=%s, source=%s, base_url=%r)",
            engine_type,
            source,
            base_url,
        )

    def mount_to(self, app: Starlette) -> None:
        _log.info("Mounting Admin to app at %r", self.base_url)
        try:
            # If sqlalchemy_file is installed, register the route that serves
            # its stored files.
            __import__("sqlalchemy_file")
            self.routes.append(
                Route(
                    "/_api/file/{storage}/{file_id}",
                    _serve_file,
                    methods=["GET"],
                    name="api:file",
                )
            )
            _log.debug("sqlalchemy_file detected, registered file-serving route")
        except ImportError:  # pragma: no cover
            pass
        super().mount_to(app)


def _serve_file(request: Request) -> Response:
    from libcloud.storage.types import ObjectDoesNotExistError
    from sqlalchemy_file.storage import StorageManager

    storage = request.path_params.get("storage")
    file_id = request.path_params.get("file_id")
    _log.debug("Serving file storage=%r file_id=%r", storage, file_id)
    try:
        file = StorageManager.get_file(f"{storage}/{file_id}")
        if file.object.driver.name == "Local Storage":
            # Local storage exposes a filesystem path, so stream it directly
            # instead of redirecting to a CDN URL.
            return FileResponse(
                file.get_cdn_url(),  # type: ignore
                media_type=file.content_type,
                filename=file.filename,
            )
        if file.get_cdn_url() is not None:  # pragma: no cover
            return RedirectResponse(file.get_cdn_url())  # type: ignore
        return StreamingResponse(  # pragma: no cover
            file.object.as_stream(),
            media_type=file.content_type,
            headers={"Content-Disposition": f"attachment;filename={file.filename}"},
        )
    except ObjectDoesNotExistError:
        _log.warning("File not found: storage=%r file_id=%r", storage, file_id)
        return JSONResponse({"detail": "Not found"}, status_code=404)
