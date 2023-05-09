# from devtools import debug  # noqa
from typing import Optional, Sequence

from bson import ObjectId
from gridfs import GridFS
from mongoengine.connection import get_db
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route
from starlette_admin.auth import AuthProvider
from starlette_admin.base import BaseAdmin
from starlette_admin.contrib.beanie.middleware import GridFSMiddleware
from starlette_admin.i18n import I18nConfig
from starlette_admin.i18n import lazy_gettext as _
from starlette_admin.views import CustomView


class Admin(BaseAdmin):
    def __init__(
        self,
        fs: GridFS,
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
    ) -> None:
        super().__init__(
            title=title,
            base_url=base_url,
            route_name=route_name,
            logo_url=logo_url,
            login_logo_url=login_logo_url,
            templates_dir=templates_dir,
            statics_dir=statics_dir,
            index_view=index_view,
            auth_provider=auth_provider,
            middlewares=middlewares,
            debug=debug,
            i18n_config=i18n_config,
        )
        self.middlewares = [] if self.middlewares is None else list(self.middlewares)
        self.middlewares.insert(0, Middleware(GridFSMiddleware, fs=fs))

    def mount_to(self, app: Starlette) -> None:
        self.routes.append(
            Route(
                "/api/file/{db}/{col}/{pk}",
                endpoint=_serve_file,
                methods=["GET"],
                name="api:file",
            )
        )
        super().mount_to(app)


def _serve_file(request: Request) -> Response:
    pk = request.path_params.get("pk")
    col = request.path_params.get("col")
    db = request.path_params.get("db")
    fs = GridFS(get_db(db), col)  # type: ignore
    try:
        file = fs.get(ObjectId(pk))
        return StreamingResponse(
            file,
            media_type=file.content_type,
            headers={"Content-Disposition": f"attachment;filename={file.filename}"},
        )
    except Exception:
        raise HTTPException(404)  # noqa B904
