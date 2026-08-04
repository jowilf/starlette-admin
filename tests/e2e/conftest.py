"""Fixtures for the Playwright e2e suite.

Runs the test app (tests/e2e/app.py) via uvicorn in a background thread and
exposes it through a session-scoped ``base_url`` override (pytest-base-url's
own fixture resolves at session scope, so this one can't be narrowed). Logs
in once per backend so most tests can reuse an already-authenticated
``page``.

Parametrized over mysql/postgres, one server per backend for the whole
session. Containers come from the session-scoped fixtures in tests/conftest.py,
shared with tests/integration/sqla rather than started fresh here.

Tests create, edit, and delete records, so an autouse, module-scoped fixture
wipes and reseeds the database before each test file's first test, keeping
one file's mutations from skewing another file's row-count assertions.
"""

import socket
import threading
import time
from contextlib import closing

import pytest
import uvicorn
from playwright.sync_api import Browser
from sqlalchemy import create_engine

from tests.e2e.app import ADMIN_PASSWORD, ADMIN_USERNAME


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session", params=["mysql", "postgres"])
def db_url(request, mysql_container, postgres_container):
    """Parametrized database URL, one per backend the e2e suite runs against."""
    backend = request.param
    if backend == "mysql":
        return mysql_container.get_connection_url()
    if backend == "postgres":
        return postgres_container.get_connection_url()
    raise ValueError(f"Unsupported e2e backend: {backend}")


@pytest.fixture(scope="session")
def live_server_url(db_url):
    from tests.e2e.app import build_app

    app = build_app(db_url)

    config = uvicorn.Config(
        app, host="127.0.0.1", port=_free_port(), log_level="warning"
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    assert server.started, "test server did not start in time"

    yield f"http://127.0.0.1:{config.port}"

    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture(scope="session")
def base_url(live_server_url: str) -> str:
    """Overrides pytest-playwright's `base_url` so relative `page.goto()` calls work."""
    return live_server_url


@pytest.fixture(autouse=True, scope="module")
def _reset_db(db_url, live_server_url):
    """Wipes and reseeds the database before each test module's first test."""
    from tests.e2e.seed import reset_and_seed

    engine = create_engine(db_url)
    reset_and_seed(engine)
    engine.dispose()


@pytest.fixture(scope="session")
def storage_state_path(browser: Browser, live_server_url: str, tmp_path_factory) -> str:
    """Logs in once and persists cookies, so authenticated tests can skip the login form."""
    context = browser.new_context(base_url=live_server_url)
    page = context.new_page()
    page.goto("/admin/login")
    page.fill('input[name="username"]', ADMIN_USERNAME)
    page.fill('input[name="password"]', ADMIN_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_url("**/admin/")
    path = tmp_path_factory.mktemp("auth") / "state.json"
    context.storage_state(path=str(path))
    context.close()
    return str(path)


@pytest.fixture
def browser_context_args(browser_context_args: dict, storage_state_path: str) -> dict:
    return {**browser_context_args, "storage_state": storage_state_path}


@pytest.fixture
def guest_page(browser: Browser, live_server_url: str):
    """A page with a fresh, unauthenticated browser context, for login/logout tests."""
    context = browser.new_context(base_url=live_server_url)
    page = context.new_page()
    yield page
    context.close()
