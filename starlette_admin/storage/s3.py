"""S3-compatible storage backend (AWS S3, MinIO, Cloudflare R2, Backblaze B2, ...).

Uses `aiobotocore` for async S3 operations. Install it with:

    pip install starlette-admin[s3]
    # or directly:
    pip install aiobotocore

`aiobotocore` is **not** a hard dependency of starlette-admin; an
`ImportError` is raised at construction time if it's missing.
"""

import uuid
from datetime import UTC, datetime
from urllib.parse import quote

from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.logging import get_logger
from starlette_admin.storage.base import BaseStorage, FileInfo

logger = get_logger(__name__)

_CHUNK_SIZE = 64 * 1024


class S3Storage(BaseStorage):
    """AWS S3 (and compatible) storage backend.

    Parameters:
        bucket: S3 bucket name.
        prefix: Key prefix for every stored object (acts like a folder).
        region: AWS region (used for URL construction and signing).
        access_key: AWS access key ID. Falls back to the standard boto3
            credential chain (env vars, shared credentials file, IAM role).
        secret_key: AWS secret access key. Falls back to the credential chain.
        public: When ``True`` (default), `url()` returns a plain
            ``https://{bucket}.s3.{region}.amazonaws.com/{key}`` URL.
            When ``False``, a pre-signed URL valid for `expires` seconds is
            generated on every render.
        expires: Lifetime of pre-signed URLs in seconds (default 3600 = 1 h).
            Only used when ``public=False`` or when ``url()`` is called with
            ``signed=True``.
        endpoint_url: Override the S3 endpoint URL for MinIO / R2 / Backblaze.
        name: Registry name for this instance. Override it when using several
            `S3Storage` instances.
    """

    name = "s3"

    def __init__(
        self,
        bucket: str,
        prefix: str = "uploads/",
        region: str = "us-east-1",
        access_key: str | None = None,
        secret_key: str | None = None,
        public: bool = True,
        expires: int = 3600,
        endpoint_url: str | None = None,
        name: str | None = None,
    ) -> None:
        try:
            import aiobotocore.session  # noqa: F401
        except ImportError as err:
            raise ImportError(
                "'aiobotocore' is required to use S3Storage. "
                "Install it with: pip install starlette-admin[s3]"
            ) from err
        self.bucket = bucket
        self.prefix = prefix.lstrip("/")
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.public = public
        self.expires = expires
        self.endpoint_url = endpoint_url
        super().__init__(name)

    def _client_kwargs(self) -> dict:

        kwargs: dict = {"region_name": self.region}
        if self.access_key and self.secret_key:
            kwargs["aws_access_key_id"] = self.access_key
            kwargs["aws_secret_access_key"] = self.secret_key
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
        return kwargs

    def _key(self, dest: str) -> str:
        return f"{self.prefix}{dest}" if self.prefix else dest

    def _public_url(self, key: str) -> str:
        if self.endpoint_url:
            base = self.endpoint_url.rstrip("/")
            return f"{base}/{self.bucket}/{quote(key, safe='/')}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{quote(key, safe='/')}"

    async def save(self, upload: UploadFile, dest: str) -> FileInfo:
        import aiobotocore.session

        session = aiobotocore.session.get_session()
        # Always prefix with a random token so each upload gets a unique key
        # without a head_object check. A check-then-write pair is inherently
        # racy: two concurrent uploads to the same dest can both find "not
        # found" and then overwrite each other on put_object.
        key = self._key(f"{uuid.uuid4().hex[:8]}_{dest}")
        content_type = upload.content_type or "application/octet-stream"
        async with session.create_client("s3", **self._client_kwargs()) as client:
            await client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=upload.file,
                ContentType=content_type,
                ContentLength=upload.size or 0,
            )
        logger.debug(
            "Saved %r (%d bytes) to bucket %r", key, upload.size or 0, self.bucket
        )
        url = self._public_url(key) if self.public else ""
        return FileInfo(
            filename=dest.rsplit("/", maxsplit=1)[-1],
            content_type=content_type,
            size=upload.size or 0,
            storage=self.name,
            key=key,
            url=url,
            uploaded_at=datetime.now(UTC),
        )

    async def url(
        self,
        request: Request,
        key: str,
        *,
        signed: bool = False,
        expires: int | None = None,
    ) -> str:
        if self.public and not signed:
            return self._public_url(key)
        import aiobotocore.session

        session = aiobotocore.session.get_session()
        async with session.create_client("s3", **self._client_kwargs()) as client:
            return await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires if expires is not None else self.expires,
            )

    async def delete(self, key: str) -> None:
        import aiobotocore.session

        session = aiobotocore.session.get_session()
        async with session.create_client("s3", **self._client_kwargs()) as client:
            try:
                await client.delete_object(Bucket=self.bucket, Key=key)
            except Exception:  # pragma: no cover
                logger.warning(
                    "Failed to delete %r from bucket %r",
                    key,
                    self.bucket,
                    exc_info=True,
                )
            else:
                logger.debug("Deleted %r from bucket %r", key, self.bucket)

    async def read(self, key: str) -> bytes:
        """Return the object's bytes from S3.

        Raises:
            FileNotFoundError: if the object does not exist at ``key``.
        """
        import aiobotocore.session
        from botocore.exceptions import ClientError

        session = aiobotocore.session.get_session()
        async with session.create_client("s3", **self._client_kwargs()) as client:
            try:
                response = await client.get_object(Bucket=self.bucket, Key=key)
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code")
                if error_code in ("NoSuchKey", "404"):
                    logger.warning(
                        "Read failed: %r not found in bucket %r", key, self.bucket
                    )
                    raise FileNotFoundError(
                        f"No file at key {key!r} in {self.name}"
                    ) from exc
                raise
            async with response["Body"] as stream:
                return await stream.read()

    async def serve(self, request: Request, key: str) -> Response:
        """Redirect to the bucket URL; S3 files are served directly from there."""
        from starlette.responses import RedirectResponse

        return RedirectResponse(await self.url(request, key, signed=not self.public))
