import base64
import os
import tempfile
from urllib.parse import urlparse, urlunparse

import pytest
from libcloud.storage.drivers.local import LocalStorageDriver
from libcloud.storage.drivers.minio import MinIOStorageDriver

from tests.integration.sqla.utils import get_or_create_container

_MINIO_KEY = "minioadmin"
_MINIO_SECRET = "minioadmin"


@pytest.fixture(scope="session")
def _minio_libcloud_driver(minio_container):
    endpoint = minio_container.get_config()["endpoint"]
    host, _, port_str = endpoint.rpartition(":")
    return MinIOStorageDriver(
        key=_MINIO_KEY,
        secret=_MINIO_SECRET,
        host=host,
        port=int(port_str),
        secure=False,
    )


def _to_async_url(sync_url: str, backend: str) -> str:
    parsed = urlparse(sync_url)
    if backend == "mysql":
        new_scheme = "mysql+aiomysql"
    elif backend == "postgres":
        new_scheme = "postgresql+asyncpg"
    else:
        raise ValueError(f"Unsupported async backend: {backend}")
    return urlunparse(parsed._replace(scheme=new_scheme))


@pytest.fixture(params=["sqlite", "mysql", "postgres"])
def sqla_backend(request, mysql_container, postgres_container):
    """Parametrized database backend for SQLA integration tests.

    Sets ``SQLA_ENGINE`` and ``SQLA_ASYNC_ENGINE`` environment variables so
    that ``get_test_engine()`` / ``get_async_test_engine()`` connect to the
    selected backend.
    """
    backend = request.param
    if backend == "sqlite":
        sync_url = "sqlite:///test.db?check_same_thread=False"
        async_url = "sqlite+aiosqlite:////tmp/test.db?check_same_thread=False"
    elif backend == "mysql":
        sync_url = mysql_container.get_connection_url()
        async_url = _to_async_url(sync_url, "mysql")
    elif backend == "postgres":
        sync_url = postgres_container.get_connection_url()
        async_url = _to_async_url(sync_url, "postgres")
    else:
        raise ValueError(backend)
    os.environ["SQLA_ENGINE"] = sync_url
    os.environ["SQLA_ASYNC_ENGINE"] = async_url
    yield backend


@pytest.fixture(params=["local", "minio"])
def libcloud_container_factory(request, tmp_path):
    """Parametrized factory(name) -> libcloud Container.

    Runs each test twice: once against a local directory backend and once
    against an in-process MinIO container.
    """
    if request.param == "local":
        yield lambda name: get_or_create_container(
            LocalStorageDriver(str(tmp_path)), name
        )
    else:
        driver = request.getfixturevalue("_minio_libcloud_driver")
        yield lambda name: get_or_create_container(driver, name)


@pytest.fixture
def sqla_storage_factory(sqla_backend, tmp_path, _minio_libcloud_driver):
    """Backend-aware storage factory.

    SQLite tests exercise the MinIO code path; MySQL and PostgreSQL tests use
    the local driver so each database backend leg does not also pay for a
    separate MinIO container.
    """
    if sqla_backend == "sqlite":
        driver = _minio_libcloud_driver
    else:
        driver = LocalStorageDriver(str(tmp_path))
    yield lambda name: get_or_create_container(driver, name)


@pytest.fixture
def fake_image_content():
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAAHNJREFUKFOdkLEKwCAMRM/JwUFwdPb"
        "/v8RPEDcdBQcHJyUt0hQ6hGY6Li8XEhVjXM45aK3xVXNOtNagcs6LRAgB1toX23tHSgkUpEopyxhzGRw"
        "+EHljjBv03oM3KJYP1lofkJoHJs3T/4Gi1aJjxO+RPnwDur2EF1gNZukAAAAASUVORK5CYII="
    )


@pytest.fixture
def fake_image(fake_image_content):
    file = tempfile.NamedTemporaryFile(suffix=".png")
    file.write(fake_image_content)
    file.seek(0)
    return file


@pytest.fixture
def fake_invalid_image():
    file = tempfile.NamedTemporaryFile(suffix=".png")
    file.write(b"Pass through content type validation")
    file.seek(0)
    return file


@pytest.fixture
def fake_empty_file():
    file = tempfile.NamedTemporaryFile()
    file.seek(0)
    return file
