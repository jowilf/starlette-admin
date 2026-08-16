import gridfs
from bson import ObjectId
from mongoengine.connection import get_db
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route
from starlette_admin.base import BaseAdmin


class Admin(BaseAdmin):
    """MongoEngine-flavored `BaseAdmin` that also mounts the GridFS file-serving route."""

    def mount_to(self, app: Starlette) -> None:
        self.routes.append(
            Route(
                "/api/file/{db}/{col}/{pk}",
                _serve_file,
                methods=["GET"],
                name="api:file",
            )
        )
        super().mount_to(app)


def _serve_file(request: Request) -> Response:
    """Stream a file stored in GridFS back to the client.

    Mounted at `/api/file/{db}/{col}/{pk}` and referenced by the URLs that
    [FileField][starlette_admin.contrib.mongoengine.fields.FileField] and
    [ImageField][starlette_admin.contrib.mongoengine.fields.ImageField] generate.
    """
    pk = request.path_params.get("pk")
    col = request.path_params.get("col")
    db = request.path_params.get("db")
    fs = gridfs.GridFS(get_db(db), col)  # type: ignore
    try:
        file = fs.get(ObjectId(pk))
        content_type = file._file.get("contentType") or "application/octet-stream"
        return StreamingResponse(
            file,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment;filename={file.filename}"},
        )
    except Exception:
        # Any failure here (bad ObjectId, unknown db/collection, missing file)
        # surfaces to the client as a plain 404.
        raise HTTPException(404)  # noqa B904
