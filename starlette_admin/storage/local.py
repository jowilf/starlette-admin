import uuid
from datetime import UTC, datetime
from pathlib import Path

from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import FileResponse, Response
from starlette.status import HTTP_404_NOT_FOUND
from starlette_admin.logging import get_logger
from starlette_admin.storage.base import BaseStorage, FileInfo

logger = get_logger(__name__)

_CHUNK_SIZE = 64 * 1024


class LocalStorage(BaseStorage):
    """Filesystem storage rooted at `base_dir`.

    Files are served exclusively through the admin's ``/_files/{storage}/{path}``
    route; no external `StaticFiles` mount is needed or supported.

    Parameters:
        base_dir: Directory under which all files are stored (created if absent).
        name: Registry name for this instance. Override it when using several
            `LocalStorage` instances with different directories.
    """

    name = "local"

    def __init__(
        self,
        base_dir: str | Path,
        name: str | None = None,
    ) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        super().__init__(name)

    def _full_path(self, key: str) -> Path:
        """Resolve ``key`` inside ``base_dir``.

        Rejects keys that contain ``..`` path components (even when the final
        resolved path would still be inside ``base_dir``) and keys whose
        resolved path escapes ``base_dir``.
        """
        parts = Path(key).parts
        if ".." in parts:
            logger.warning("Rejected key %r: contains '..' path component", key)
            raise HTTPException(HTTP_404_NOT_FOUND)
        path = (self.base_dir / key).resolve()
        if not path.is_relative_to(self.base_dir):
            logger.warning("Rejected key %r: resolves outside %s", key, self.base_dir)
            raise HTTPException(HTTP_404_NOT_FOUND)
        return path

    async def save(self, upload: UploadFile, dest: str) -> FileInfo:
        path = self._full_path(dest)
        path.parent.mkdir(parents=True, exist_ok=True)
        while path.exists():
            path = path.with_name(f"{uuid.uuid4().hex[:8]}_{path.name}")
        size = 0
        with path.open("wb") as out:
            while chunk := await upload.read(_CHUNK_SIZE):
                size += len(chunk)
                out.write(chunk)
        logger.debug("Saved %r (%d bytes) to %s", dest, size, path)
        return FileInfo(
            filename=path.name,
            content_type=upload.content_type or "application/octet-stream",
            size=size,
            storage=self.name,
            key=path.relative_to(self.base_dir).as_posix(),
            uploaded_at=datetime.now(UTC),
        )

    async def url(
        self, request: Request, key: str, *, signed: bool = False, expires: int = 3600
    ) -> str:
        route_name = request.app.state.ROUTE_NAME
        return str(request.url_for(f"{route_name}:file", storage=self.name, path=key))

    async def delete(self, key: str) -> None:
        path = self._full_path(key)
        if path.is_file():
            path.unlink()
            logger.debug("Deleted %r from %s", key, self.base_dir)
        else:
            logger.debug("Delete no-op: %r not found in %s", key, self.base_dir)

    async def read(self, key: str) -> bytes:
        path = self._full_path(key)
        if not path.is_file():
            logger.warning("Read failed: %r not found in %s", key, self.base_dir)
            raise FileNotFoundError(f"No file at key {key!r} in {self.base_dir}")
        return path.read_bytes()

    async def serve(self, request: Request, key: str) -> Response:
        path = self._full_path(key)
        if not path.is_file():
            logger.warning("Serve failed: %r not found in %s", key, self.base_dir)
            raise HTTPException(HTTP_404_NOT_FOUND)
        return FileResponse(path)
