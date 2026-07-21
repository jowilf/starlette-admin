"""
01-soft-delete: two views on one table, active posts and the trash.

PostView  : hides soft-deleted rows from list and count queries (the detail
            query defaults to the list query, so it is hidden there too);
            "delete" sets deleted_at instead of removing the row from the
            database.
TrashView : shows only soft-deleted rows; supports "restore" (clears
            deleted_at) and hard-purge (real DELETE, via the built-in
            delete action).
"""

import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import uvicorn
from sqlalchemy import DateTime, Integer, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import action, flash
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.helpers import on_commit

DATABASE_FILE = "advanced_01_soft_delete.sqlite"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


# ── Model ──────────────────────────────────────────────────────────────────────


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


# ── Active-posts view ──────────────────────────────────────────────────────────


class PostView(ModelView):
    """Shows only live (non-deleted) posts. Delete soft-deletes by stamping deleted_at."""

    exclude_fields_from_list = ["deleted_at"]
    exclude_fields_from_create = ["deleted_at", "created_at"]
    exclude_fields_from_edit = ["deleted_at", "created_at"]
    fields_default_sort = [("created_at", True)]

    def get_list_query(self, request: Request):
        return super().get_list_query(request).where(Post.deleted_at.is_(None))

    def get_count_query(self, request: Request):
        return super().get_count_query(request).where(Post.deleted_at.is_(None))

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        session: Session = request.state.session
        objs: list[Post] = await self.find_by_pks(request, pks)
        now = datetime.utcnow()
        for obj in objs:
            await self._emit_before_delete(request, obj.id, obj)
            obj.deleted_at = now
            session.add(obj)
        session.flush()

        def _make_after_delete_committed(obj: Post, pk: Any) -> Callable[[], Any]:
            return lambda: self._emit_after_delete_committed(request, pk, obj)

        for obj in objs:
            pk = obj.id
            await self._emit_after_delete(request, pk, obj)
            on_commit(request, _make_after_delete_committed(obj, pk))
        return len(objs)


# ── Trash view ─────────────────────────────────────────────────────────────────


class TrashView(ModelView):
    """Shows only soft-deleted posts. Supports restore and permanent purge."""

    menu_label = "Trash"
    icon = "fa fa-trash"
    fields_default_sort = [("deleted_at", True)]
    actions = ["restore", "delete"]

    def get_list_query(self, request: Request):
        return select(Post).where(Post.deleted_at.isnot(None))

    def get_count_query(self, request: Request):
        return select(func.count()).select_from(Post).where(Post.deleted_at.isnot(None))

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False

    @action(
        name="restore",
        text="Restore",
        confirmation="Restore the selected posts?",
        submit_btn_text="Yes, restore",
        submit_btn_class="btn-success",
    )
    async def restore_action(self, request: Request, pks: list[Any]) -> None:
        session: Session = request.state.session
        objs = await self.find_by_pks(request, pks)
        for obj in objs:
            obj.deleted_at = None
            session.add(obj)
        session.flush()
        count = len(objs)
        flash(request, f"{count} post{'s' if count != 1 else ''} restored.", "success")


# ── App setup ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_: Starlette):
    first_run = not os.path.exists(DATABASE_FILE)
    Base.metadata.create_all(engine)
    if first_run:
        from seed import seed

        with Session(engine) as session:
            seed(session)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>Soft-delete example</h2>"
                "<p>Delete moves posts to the Trash. Restore brings them back.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)

admin = Admin(engine, title="Example: Soft Delete", secret_key="dev-only-change-me")

admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))
admin.add_view(TrashView(Post, key="trash", icon="fa fa-trash"))

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../../.."])
