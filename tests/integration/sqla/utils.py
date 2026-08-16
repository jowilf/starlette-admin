import os
import uuid

import sqlalchemy.types as types
from libcloud.storage.base import Container, StorageDriver
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


class Uuid(types.TypeDecorator):
    """
    Platform-independent UUID type for testing.
    """

    impl = types.CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return mysql.CHAR(32) if dialect == "mysql" else types.CHAR(32)

    def process_bind_param(self, value, dialect):
        if isinstance(value, uuid.UUID):
            return value.hex
        return uuid.UUID(value).hex

    def process_result_value(self, value, dialect):

        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)

        return value
