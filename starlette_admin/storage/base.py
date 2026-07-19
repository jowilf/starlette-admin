"""Pluggable file storage backends for `FileField` / `ImageField`.

The database column behind a file field stores only a JSON metadata object
(the dict form of [FileInfo][starlette_admin.storage.FileInfo]), never a raw
path string or binary blob. Saving, replacing and deleting the underlying
files is orchestrated by `BaseAdmin` (see `BaseAdmin._process_file_fields`)
and delegated to a [BaseStorage][starlette_admin.storage.BaseStorage]
instance attached to the field.
"""

import os
import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from dataclasses import field as dc_field
from datetime import datetime
from typing import Any

from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.exceptions import StarletteAdminException
from starlette_admin.logging import get_logger

logger = get_logger(__name__)


class UnknownStorageError(StarletteAdminException):
    """Raised when a `FileInfo.storage` name doesn't match any registered storage."""


_FILENAME_SANITIZE_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def secure_filename(filename: str) -> str:
    """Return a sanitised version of an (untrusted) uploaded filename:
    path components are stripped and anything outside ``[A-Za-z0-9_.-]``
    is collapsed to ``_``.
    """
    filename = os.path.basename(filename.replace("\\", "/"))
    filename = _FILENAME_SANITIZE_RE.sub("_", filename).strip("._")
    return filename or "file"


@dataclass(frozen=True)
class FileInfo:
    """Metadata describing a stored file. This (as a dict, via
    [to_dict][starlette_admin.storage.FileInfo.to_dict]) is what file fields
    persist in the database column.

    Attributes:
        filename: Original (sanitised) filename, for display.
        content_type: MIME type reported at upload time.
        size: File size in bytes.
        storage: Name of the storage backend holding the file.
        key: Storage-relative path / object key.
        url: Public-facing URL. Refreshed on every render by
            `BaseStorage.url`; an empty string is stored for backends
            (like `LocalStorage`) whose URLs are request-dependent.
        uploaded_at: UTC timestamp of the upload.
        width: Image width in pixels (`ImageField` only).
        height: Image height in pixels (`ImageField` only).
        thumbnail: Thumbnail metadata (`ImageField` with `thumbnail_size` only),
            holding `{key, width, height, size}`. The thumbnail lives in the
            same storage as the parent file, so no separate storage name is
            recorded.
        extra: Free-form backend-specific metadata.
    """

    filename: str
    content_type: str
    size: int
    storage: str
    key: str
    url: str = ""
    uploaded_at: datetime | None = None
    width: int | None = None
    height: int | None = None
    thumbnail: dict | None = None
    extra: dict = dc_field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict form, suitable for a database JSON column."""
        data = asdict(self)
        if self.uploaded_at is not None:
            data["uploaded_at"] = self.uploaded_at.isoformat()
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileInfo":
        """Rebuild a `FileInfo` from its stored dict form."""
        kwargs = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        uploaded_at = kwargs.get("uploaded_at")
        if isinstance(uploaded_at, str):
            kwargs["uploaded_at"] = datetime.fromisoformat(uploaded_at)
        return cls(**kwargs)


class BaseStorage(ABC):
    """Base class for file storage backends.

    Each instance registers itself under its `name` so that stored values
    (which carry only the storage *name* in their metadata) can be resolved
    back to the backend that holds them. See
    [get_storage][starlette_admin.storage.get_storage].
    """

    name: str = ""

    def __init__(self, name: str | None = None) -> None:
        if name is not None:
            self.name = name
        assert self.name, "storage must have a non-empty name"
        register_storage(self)

    @abstractmethod
    async def save(self, upload: UploadFile, dest: str) -> FileInfo:
        """Persist `upload` under the (sanitised, storage-relative) path
        `dest` and return the resulting [FileInfo][starlette_admin.storage.FileInfo].
        Implementations must never overwrite an existing file: `dest` is
        uniquified when taken.
        """
        raise NotImplementedError()

    @abstractmethod
    async def url(
        self, request: Request, key: str, *, signed: bool = False, expires: int = 3600
    ) -> str:
        """Return a public-facing URL for `key`. Called on every page render;
        signed URLs are never stored.
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove the file identified by `key`. Must not fail if the file is
        already gone.
        """
        raise NotImplementedError()

    async def read(self, key: str) -> bytes:
        """Return the full contents of the file identified by `key` as bytes.

        Used by the export system to embed files into ZIP archives. Backends
        whose files live on an external host (e.g. S3) must override this;
        the default raises `NotImplementedError` so callers can skip the file
        gracefully rather than crashing the export.

        Raises:
            NotImplementedError: for backends that have not implemented this.
            FileNotFoundError: if the file does not exist at `key`.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not implement read(); "
            "override it to support file embedding in ZIP exports."
        )

    async def serve(self, request: Request, key: str) -> Response:
        """Serve the file identified by `key` over HTTP. Backs the admin's
        ``/files/{storage}/{path}`` route; backends whose URLs point at an
        external host don't need to implement it.
        """
        raise NotImplementedError()


_storages: dict[str, BaseStorage] = {}


def register_storage(storage: BaseStorage) -> None:
    """Register `storage` under its name (replacing any previous instance)."""
    if storage.name in _storages:
        logger.debug("Replacing already-registered storage %r", storage.name)
    _storages[storage.name] = storage
    logger.debug("Registered storage %r (%s)", storage.name, type(storage).__name__)


def get_storage(name: str) -> BaseStorage:
    """Resolve a storage name (as stored in `FileInfo.storage`) back to its
    registered instance.

    Raises:
        UnknownStorageError: if no storage with that name has been instantiated.
    """
    try:
        return _storages[name]
    except KeyError as err:
        logger.warning("No storage named %r is registered", name)
        raise UnknownStorageError(
            f"No storage named {name!r} is registered. Storage instances must be"
            " created before values referencing them are rendered."
        ) from err


async def delete_stored_files(value: Any) -> None:
    """Delete the file(s) referenced by a stored file-field value: a
    `FileInfo`, its dict form, or a list of either. Values referencing an
    unregistered storage (or of any other shape) are skipped silently.

    A thumbnail nested under `thumbnail.key` (`ImageField` with
    `thumbnail_size`) is deleted alongside the main file, from the same
    storage.
    """
    values = value if isinstance(value, (list, tuple)) else [value]
    for raw in values:
        item = raw.to_dict() if isinstance(raw, FileInfo) else raw
        if isinstance(item, dict) and item.get("storage") and item.get("key"):
            try:
                storage = get_storage(item["storage"])
            except UnknownStorageError:
                logger.warning(
                    "Skipping delete of key %r: storage %r is not registered",
                    item["key"],
                    item["storage"],
                )
                continue
            logger.debug("Deleting %r from storage %r", item["key"], item["storage"])
            await storage.delete(item["key"])
            thumbnail = item.get("thumbnail")
            if isinstance(thumbnail, dict) and thumbnail.get("key"):
                logger.debug(
                    "Deleting thumbnail %r from storage %r",
                    thumbnail["key"],
                    item["storage"],
                )
                await storage.delete(thumbnail["key"])
