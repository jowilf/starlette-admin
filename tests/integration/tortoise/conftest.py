"""Shared fixtures for Tortoise ORM integration tests.

``tortoise_backend`` parametrizes every test in this package across sqlite,
MySQL, and PostgreSQL. MySQL and PostgreSQL reuse the session-scoped
containers from the top-level conftest, so each test's ``db`` fixture must
call ``reset_schema()`` before closing its connection to leave the shared
container clean for the next test."""

import pytest

from tests.integration.tortoise.utils import mysql_tortoise_url, postgres_tortoise_url


@pytest.fixture(params=["sqlite", "mysql", "postgres"])
def tortoise_backend(request, mysql_container, postgres_container):
    """Yields (backend_name, db_url) for the selected SQL backend."""
    backend = request.param
    if backend == "sqlite":
        return backend, "sqlite://:memory:"
    if backend == "mysql":
        return backend, mysql_tortoise_url(mysql_container)
    return backend, postgres_tortoise_url(postgres_container)
