"""
04-user-registration: Public sign-up page built on CustomView + AuthProvider.

Users live in a `users` table with bcrypt-hashed passwords (via passlib). The
login form (built-in AuthProvider page) checks credentials against that
table. A CustomView mounted at /admin/register renders a registration form
that anyone can reach; its route is exempted from the auth check via
`@login_not_required`, and creates the account, logs the user in, and
redirects into the admin.

Run the app, open http://localhost:8000/admin/register, create an account,
and you land in the admin as that user.
"""

from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from passlib.context import CryptContext
from sqlalchemy import DateTime, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Route
from starlette.status import HTTP_303_SEE_OTHER
from starlette_admin import CustomView, route
from starlette_admin.auth import (
    AdminUser,
    AuthProvider,
    LoginFailed,
    login_not_required,
)
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.helpers import HTTP_422, index_url

DATABASE_FILE = "advanced_04_user_registration.sqlite"
SECRET = "change-me-in-production"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), default="")
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    async def __admin_repr__(self, request: Request) -> str:
        return self.full_name or self.username


# ── Password hashing (passlib + bcrypt) ────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, stored: str) -> bool:
    return pwd_context.verify(password, stored)


# ── Auth provider: checks credentials against the users table ─────────────────


class RegistrationAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
    ) -> None:
        with Session(engine) as session:
            user = session.scalar(select(User).where(User.username == username))
            if user and verify_password(password, user.password_hash):
                request.session["user_id"] = user.id
                return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        user_id = request.session.get("user_id")
        if user_id is None:
            return None
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user:
                return AdminUser(username=user.full_name or user.username)
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()


# ── Registration view: a CustomView reachable without login ───────────────────


class RegistrationView(CustomView):
    menu_label = "Register"
    path = "/register"
    add_to_menu = False  # logged-in users don't need a sign-up link

    @route("", methods=["GET", "POST"], name="register")
    @login_not_required
    async def index(self, request: Request) -> Response:
        if request.method == "GET":
            return self._render(request)

        form = await request.form()
        username = str(form.get("username") or "").strip()
        full_name = str(form.get("full_name") or "").strip()
        password = str(form.get("password") or "")
        password_confirm = str(form.get("password_confirm") or "")

        errors: dict[str, str] = {}
        if len(username) < 3:
            errors["username"] = "Username must be at least 3 characters"
        if len(password) < 8:
            errors["password"] = "Password must be at least 8 characters"
        elif password != password_confirm:
            errors["password_confirm"] = "Passwords do not match"

        with Session(engine) as session:
            if not errors and session.scalar(
                select(User).where(User.username == username)
            ):
                errors["username"] = "This username is already taken"
            if errors:
                return self._render(
                    request,
                    errors=errors,
                    values={"username": username, "full_name": full_name},
                    status_code=HTTP_422,
                )
            user = User(
                username=username,
                full_name=full_name,
                password_hash=hash_password(password),
            )
            session.add(user)
            session.commit()
            # Log the new user in right away.
            request.session["user_id"] = user.id

        return RedirectResponse(
            index_url(request),
            status_code=HTTP_303_SEE_OTHER,
        )

    def _render(
        self,
        request: Request,
        errors: dict[str, str] | None = None,
        values: dict[str, str] | None = None,
        status_code: int = 200,
    ) -> Response:
        return self.templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"errors": errors or {}, "values": values or {}},
            status_code=status_code,
        )


# ── Admin views ────────────────────────────────────────────────────────────────


class UserView(ModelView):
    # password_hash is omitted so it never reaches list/detail/forms
    fields = [User.id, User.username, User.full_name, User.created_at]

    def can_create(self, request: Request) -> bool:
        return False  # accounts are created through the registration page

    def can_edit(self, request: Request) -> bool:
        return False


# ── App setup ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_: Starlette):
    Base.metadata.create_all(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    middleware=[Middleware(SessionMiddleware, secret_key=SECRET)],
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>User registration example</h2>"
                '<p><a href="/admin/register">Create an account</a> '
                'or <a href="/admin/">sign in</a>.</p>'
            ),
        )
    ],
)

admin = Admin(
    engine,
    title="Example: User Registration",
    auth_provider=RegistrationAuthProvider(),
    secret_key=SECRET,
)

admin.add_view(RegistrationView())
admin.add_view(UserView(User, icon="fa fa-users", menu_label="Users"))

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../../.."])
