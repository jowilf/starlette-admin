import os
import uuid

import sqlalchemy.types as types
from libcloud.storage.base import Container, StorageDriver
from libcloud.storage.drivers.local import LocalStorageDriver
from libcloud.storage.drivers.minio import MinIOStorageDriver
from libcloud.storage.types import ContainerDoesNotExistError
from sqlalchemy import create_engine
from sqlalchemy.dialects import mysql
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def get_test_engine() -> Engine:
    return create_engine(os.environ["SQLA_ENGINE"])


def get_async_test_engine() -> AsyncEngine:
    return create_async_engine(os.environ["SQLA_ASYNC_ENGINE"])


def get_or_create_container(driver: StorageDriver, name: str) -> Container:
    try:
        return driver.get_container(name)
    except ContainerDoesNotExistError:
        return driver.create_container(name)


def get_test_container(name: str) -> Container:
    provider = os.environ.get("STORAGE_PROVIDER", "LOCAL")
    if provider == "MINIO":
        key = os.environ.get("MINIO_KEY", "minioadmin")
        secret = os.environ.get("MINIO_SECRET", "minioadmin")
        host = os.environ.get("MINIO_HOST", "127.0.0.1")
        port = int(os.environ.get("MINIO_PORT", "9000"))
        secure = os.environ.get("MINIO_SECURE", "False").lower() == "true"
        return get_or_create_container(
            MinIOStorageDriver(
                key=key, secret=secret, host=host, port=port, secure=secure
            ),
            name,
        )
    dir_path = os.environ.get("LOCAL_PATH", "/tmp/storage")
    os.makedirs(dir_path, 0o777, exist_ok=True)
    return get_or_create_container(LocalStorageDriver(dir_path), name)


class Uuid(types.TypeDecorator):
    """
    Platform-independent UUID type for testing.
    """

    impl = types.CHAR

    def load_dialect_impl(self, dialect):
        return mysql.CHAR(32) if dialect == "mysql" else types.CHAR(32)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value


        return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)

        return value
