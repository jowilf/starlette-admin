"""Project-wide test fixtures.

This module provides a parametrized `storage` fixture that executes each requesting test twice: once against a temporary `LocalStorage` directory and once against a MinIO-backed `S3Storage` instance.

The MySQL, PostgreSQL, MongoDB, and MinIO containers defined here are session-scoped and live in this top-level conftest so that every test package resolves the same fixture instance instead of each package starting its own container.
"""

import contextlib
import io

import boto3
import pytest
from PIL import Image
from starlette.datastructures import Headers, UploadFile
from starlette_admin.storage import LocalStorage
from starlette_admin.storage.s3 import S3Storage
from testcontainers.minio import MinioContainer
from testcontainers.mongodb import MongoDbContainer
from testcontainers.mysql import MySqlContainer
from testcontainers.postgres import PostgresContainer


@pytest.fixture(autouse=True)
def reset_timezone_state():
    """Resets all timezone context variables to their default values after each test.

    Failure to restore the full state (including `_timezone_conversion_enabled`) after calling `set_timezone()` or `set_database_timezone()` can leave ContextVars in an inconsistent state, potentially causing subsequent tests to apply unexpected timezone conversions.
    """
    yield
    from starlette_admin.i18n import (
        DEFAULT_DB_TIMEZONE,
        DEFAULT_TIMEZONE,
        _current_database_timezone,
        _current_timezone,
        _timezone_conversion_enabled,
    )

    _timezone_conversion_enabled.set(False)
    _current_timezone.set(DEFAULT_TIMEZONE)
    _current_database_timezone.set(DEFAULT_DB_TIMEZONE)


_MINIO_ACCESS_KEY = "minioadmin"
_MINIO_SECRET_KEY = "minioadmin"
_MINIO_BUCKET = "test-bucket"


@pytest.fixture(scope="session")
def minio_container():
    with MinioContainer(
        access_key=_MINIO_ACCESS_KEY,
        secret_key=_MINIO_SECRET_KEY,
    ) as container:
        yield container


@pytest.fixture(scope="session")
def minio_endpoint(minio_container):
    return f"http://{minio_container.get_config()['endpoint']}"


@pytest.fixture(scope="session")
def mysql_container():
    with MySqlContainer(
        image="mysql:8.0",
        dialect="pymysql",
        username="test",
        password="test",
        dbname="test",
    ) as container:
        yield container


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer(
        image="postgres:15",
        driver="psycopg2",
        username="test",
        password="test",
        dbname="test",
    ) as container:
        yield container


@pytest.fixture(scope="session")
def mongo_url():
    with MongoDbContainer("mongo:7.0") as container:
        yield container.get_connection_url()


def make_upload(
    content: bytes = b"data",
    filename: str = "file.txt",
    content_type: str = "text/plain",
) -> UploadFile:
    return UploadFile(
        io.BytesIO(content),
        size=len(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def make_png(width: int = 10, height: int = 4) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height)).save(buffer, "PNG")
    return buffer.getvalue()


def _ensure_bucket(endpoint: str) -> None:
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=_MINIO_ACCESS_KEY,
        aws_secret_access_key=_MINIO_SECRET_KEY,
        region_name="us-east-1",
    )
    with contextlib.suppress(client.exceptions.BucketAlreadyOwnedByYou):
        client.create_bucket(Bucket=_MINIO_BUCKET)


def _make_s3_storage(endpoint: str, prefix: str, public: bool, name: str) -> S3Storage:
    _ensure_bucket(endpoint)
    return S3Storage(
        bucket=_MINIO_BUCKET,
        prefix=prefix,
        region="us-east-1",
        access_key=_MINIO_ACCESS_KEY,
        secret_key=_MINIO_SECRET_KEY,
        public=public,
        endpoint_url=endpoint,
        name=name,
    )


@pytest.fixture(params=["local", "s3"])
def storage(request, tmp_path, minio_endpoint):
    if request.param == "local":
        yield LocalStorage(base_dir=tmp_path, name=f"local-{id(tmp_path)}")
        return

    yield _make_s3_storage(
        endpoint=minio_endpoint,
        prefix="uploads/",
        public=True,
        name=f"s3-{id(tmp_path)}",
    )


@pytest.fixture()
def s3_private_storage(minio_endpoint):
    return _make_s3_storage(
        endpoint=minio_endpoint,
        prefix="priv/",
        public=False,
        name=f"s3-private-{id(minio_endpoint)}",
    )
