import pytest
from sqlalchemy import Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import StaticPool
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin.contrib.sqla import Admin, ModelView

from {{ cookiecutter.package_slug }} import {{ cookiecutter.class_prefix }}Theme


class Base(DeclarativeBase):
    """Base class for the in-memory demo model used across tests."""


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str]


class ProductView(ModelView):
    fields = ["id", "name"]


class CsrfTestClient(TestClient):
    """Drop-in TestClient that auto-attaches the CSRF token.

    BaseAdmin always attaches CSRF middleware, so plain mutating POSTs return
    403. This client fetches the admin index to seed the signed
    starlette_admin_csrftoken cookie, then sends it as X-CSRFToken on every
    mutating request.
    """

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.get("/admin/")
        self._csrf_token = self.cookies.get("starlette_admin_csrftoken", "")

    def _with_csrf_header(self, kwargs: dict) -> dict:
        headers = dict(kwargs.pop("headers", None) or {})
        headers.setdefault("X-CSRFToken", self._csrf_token)
        kwargs["headers"] = headers
        return kwargs

    def post(self, url, **kwargs):
        return super().post(url, **self._with_csrf_header(kwargs))

    def put(self, url, **kwargs):
        return super().put(url, **self._with_csrf_header(kwargs))

    def delete(self, url, **kwargs):
        return super().delete(url, **self._with_csrf_header(kwargs))


@pytest.fixture
def theme():
    return {{ cookiecutter.class_prefix }}Theme()


@pytest.fixture
def admin(theme):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    admin = Admin(engine, secret_key="test", theme=theme)
    admin.add_view(ProductView(Product))
    return admin


@pytest.fixture
def client(admin):
    app = Starlette()
    admin.mount_to(app)
    return CsrfTestClient(app, base_url="http://testserver")
