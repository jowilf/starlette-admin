import enum
import os
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from sqlalchemy import Enum, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Route
from starlette_admin import (
    ActionSelection,
    RowActionsDisplayType,
    RowActionsPosition,
    action,
    flash,
    link_row_action,
    row_action,
)
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.exceptions import ActionFailed

DATABASE_FILE = "09_actions.sqlite"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


# ── Models ─────────────────────────────────────────────────────────────────────


class Status(enum.StrEnum):
    Draft = "d"
    Published = "p"
    Withdrawn = "w"


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    views: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[Status | None] = mapped_column(Enum(Status))


# ── Admin view ─────────────────────────────────────────────────────────────────


class ArticleView(ModelView):
    exclude_fields_from_list = [Article.body]

    actions = [
        "make_published",
        "increase_views",
        "delete",
        "always_failed",
        "no_confirmation",
        "redirect",
        "redirect_with_form",
        "sync_all",
        "purge_drafts",
        "publish_matching",
    ]
    row_actions = ["view", "edit", "go_to_example", "make_published", "delete"]
    row_actions_display_type = RowActionsDisplayType.KEBAB
    row_actions_position = RowActionsPosition.AFTER_COLUMNS

    # ── Batch actions ──────────────────────────────────────────────────────────

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        session: Session = request.state.session
        articles = await selection.rows()
        for article in articles:
            article.status = Status.Published
            session.add(article)
        # flush() only pushes pending changes to the DB within the transaction; the
        # session is committed automatically at the end of each request
        session.flush()
        flash(
            request,
            f"{len(articles)} article(s) were successfully marked as published",
            "success",
        )

    @action(
        name="increase_views",
        text="Increase views",
        confirmation="By how much should the view count increase?",
        submit_btn_text="Submit",
        form="""
        <form>
            <div class="mt-3">
                <input type="number" class="form-control" name="value"
                       placeholder="Enter value" min="1" max="1000">
            </div>
        </form>
        """,
    )
    async def increase_views_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        session: Session = request.state.session
        data = await request.form()
        try:
            value = int(data.get("value"))
        except (TypeError, ValueError) as err:
            raise ActionFailed("Enter a valid number") from err
        articles = await selection.rows()
        for article in articles:
            article.views = (article.views or 0) + value
            session.add(article)
        session.flush()  # the session is committed automatically at the end of each request
        flash(
            request,
            f"View count of {len(articles)} article(s) increased by {value}.",
            "success",
        )

    @action(
        name="always_failed",
        text="Always Failed",
        confirmation="This action will always fail. Continue?",
        submit_btn_text="Continue",
        submit_btn_class="btn-outline-danger",
    )
    async def always_failed_action(
        self, request: Request, selection: ActionSelection
    ) -> str:
        raise ActionFailed("Sorry, we can't process this action right now.")

    @action(
        name="no_confirmation",
        text="No confirmation action",
    )
    async def no_confirmation_action(
        self, request: Request, _selection: ActionSelection
    ) -> None:
        flash(request, "Action executed without a confirmation dialog.", "info")

    @action(
        name="redirect",
        text="Redirect",
        custom_response=True,
    )
    async def redirect_action(
        self, _request: Request, _selection: ActionSelection
    ) -> Response:
        return RedirectResponse("https://example.com/")

    @action(
        name="redirect_with_form",
        text="Redirect with form",
        custom_response=True,
        confirmation="Fill the form",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="value"
                       placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def redirect_with_form_action(
        self, request: Request, _selection: ActionSelection
    ) -> Response:
        data = await request.form()
        return RedirectResponse(f"https://example.com/?value={data['value']}")

    # ── Global actions ─────────────────────────────────────────────────────────
    # `allow_empty_selection=True` renders the action in a separate, always
    # visible "Actions" dropdown that doesn't require a row selection.

    @action(
        name="sync_all",
        text="Sync all articles",
        confirmation="Re-sync every article from the upstream source?",
        submit_btn_text="Sync",
        allow_empty_selection=True,
    )
    async def sync_all_action(
        self, request: Request, _selection: ActionSelection
    ) -> None:
        # A real implementation would call out to the upstream source here.
        flash(request, "All articles were successfully synced.", "success")

    @action(
        name="purge_drafts",
        text="Purge drafts",
        confirmation="Delete every draft article? This cannot be undone.",
        submit_btn_text="Yes, delete them",
        submit_btn_class="btn-danger",
        allow_empty_selection=True,
    )
    async def purge_drafts_action(
        self, request: Request, _selection: ActionSelection
    ) -> None:
        session: Session = request.state.session
        drafts = session.query(Article).filter(Article.status == Status.Draft).all()
        for article in drafts:
            session.delete(article)
        session.flush()  # the session is committed automatically at the end of each request
        flash(request, f"{len(drafts)} draft article(s) were purged.", "success")

    # ── Filter-aware action ────────────────────────────────────────────────────
    # An "advanced" handler: it reads `selection.filters`/`selection.q` (the
    # list page's current filter/search) directly instead of materializing
    # `selection.rows()`, so it always runs against whatever is filtered,
    # not just the checked rows or the whole table. It is also never capped
    # by `action_select_all_limit`, since it never calls
    # `rows()`/`pks()`/`count()`.

    @action(
        name="publish_matching",
        text="Publish all matching",
        confirmation="Mark every article matching the current filter/search as published?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        allow_empty_selection=True,
    )
    async def publish_matching_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        session: Session = request.state.session
        articles = await self.find_all(
            request, skip=0, limit=-1, q=selection.q, filters=selection.filters
        )
        for article in articles:
            article.status = Status.Published
            session.add(article)
        session.flush()  # the session is committed automatically at the end of each request
        flash(
            request,
            f"{len(articles)} article(s) matching the current filter were marked as published.",
            "success",
        )

    # ── Row actions ────────────────────────────────────────────────────────────

    async def is_row_action_allowed_for_obj(
        self, request: Request, name: str, obj: Article
    ) -> bool:
        # Hide "make_published" once the article no longer needs it
        if name == "make_published":
            return obj.status != Status.Published
        return await super().is_row_action_allowed_for_obj(request, name, obj)

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published?",
        icon_class="fas fa-bullhorn",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> None:
        session: Session = request.state.session
        article = await self.find_by_pk(request, pk)
        if article.status == Status.Published:
            raise ActionFailed("This article is already published.")
        article.status = Status.Published
        session.add(article)
        session.flush()  # the session is committed automatically at the end of each request
        flash(request, "Article successfully marked as published.", "success")

    @link_row_action(
        name="go_to_example",
        text="Go to example.com",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, _request: Request, pk: Any) -> str:
        return f"https://example.com/?pk={pk}"


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
            lambda _: HTMLResponse('<a href="/admin/">Go to Admin →</a>'),
        )
    ],
)

admin = Admin(engine, title="Example: Custom Actions", secret_key="dev-only-change-me")

admin.add_view(ArticleView(Article, icon="fa fa-newspaper"))

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
