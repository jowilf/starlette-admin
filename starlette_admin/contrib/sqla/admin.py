from typing import Any, Dict, Union

from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
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
from starlette_admin.base import BaseAdmin
from starlette_admin.contrib.sqla.middleware import DBSessionMiddleware


class Admin(BaseAdmin):
    def __init__(
        self,
        engine: Union[Engine, AsyncEngine],
        **kwargs: Dict[str, Any],
    ) -> None:
        super().__init__(**kwargs)  # type: ignore
        self.middlewares = [] if self.middlewares is None else list(self.middlewares)
        self.middlewares.insert(0, Middleware(DBSessionMiddleware, engine=engine))

    def mount_to(self, app: Starlette) -> None:
        try:
            """Automatically add route to serve sqlalchemy_file files"""
            __import__("sqlalchemy_file")
            self.routes.append(
                Route(
                    "/api/file/{storage}/{file_id}",
                    _serve_file,
                    methods=["GET"],
                    name="api:file",
                )
            )
        except ImportError:  # pragma: no cover
            pass
        super().mount_to(app)


def _serve_file(request: Request) -> Response:
    from libcloud.storage.drivers.local import LocalStorageDriver
    from libcloud.storage.types import ObjectDoesNotExistError
    from sqlalchemy_file.storage import StorageManager

    try:
        storage = request.path_params.get("storage")
        file_id = request.path_params.get("file_id")
        file = StorageManager.get_file(f"{storage}/{file_id}")
        if isinstance(file.object.driver, LocalStorageDriver):
            """If file is stored in local storage, just return a
            FileResponse with the fill full path."""
            return FileResponse(
                file.get_cdn_url(), media_type=file.content_type, filename=file.filename
            )
        elif file.get_cdn_url() is not None:  # pragma: no cover
            """If file has public url, redirect to this url"""
            return RedirectResponse(file.get_cdn_url())
        else:
            """Otherwise, return a streaming response"""
            return StreamingResponse(
                file.object.as_stream(),
                media_type=file.content_type,
                headers={"Content-Disposition": f"attachment;filename={file.filename}"},
            )
    except ObjectDoesNotExistError:
        return JSONResponse({"detail": "Not found"}, status_code=404)
