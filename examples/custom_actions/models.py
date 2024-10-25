import enum
from typing import Any

from sqlalchemy import Column, Enum, Integer, String, Text
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_admin import RowActionsDisplayType, action, link_row_action, row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed

from . import Base


class Status(str, enum.Enum):
    Draft = "d"
    Published = "p"
    Withdrawn = "w"


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    body = Column(Text, nullable=False)
    views = Column(Integer)
    status = Column(Enum(Status))


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
    ]
    row_actions = ["view", "edit", "go_to_example", "make_published", "delete"]
    row_actions_display_type = RowActionsDisplayType.ICON_LIST

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published_action(self, request: Request, pks: list[Any]) -> str:
        session: Session = request.state.session
        for article in await self.find_by_pks(request, pks):
            article.status = Status.Published
            session.add(article)
        session.commit()
        return f"{len(pks)} articles were successfully marked as published"

    @action(
        name="increase_views",
        text="Increase views",
        confirmation="Are you sure you want to mark selected articles as published ?",
        submit_btn_text="Submit",
        form="""
        <form>
            <div class="mt-3">
                <input type="number" class="form-control" name="value" placeholder="Enter value" min="1" max="1000">
            </div>
        </form>
        """,
    )
    async def increase_views_action(self, request: Request, pks: list[Any]) -> str:
        session: Session = request.state.session
        data = await request.form()
        try:
            value = int(data.get("value"))
        except (TypeError, ValueError) as err:
            raise ActionFailed("Enter a valid number") from err
        for article in await self.find_by_pks(request, pks):
            article.views += value
            session.add(article)
        session.commit()
        return (
            f"The number of views of {len(pks)} articles has been increased by {value}."
        )

    @action(
        name="always_failed",
        text="Always Failed",
        confirmation="This action will fail, do you want to continue ?",
        submit_btn_text="Continue",
        submit_btn_class="btn-outline-danger",
    )
    async def always_failed_action(self, request: Request, pks: list[Any]) -> str:
        raise ActionFailed("Sorry, We can't proceed this action now.")

    @action(
        name="no_confirmation",
        text="No confirmation action",
    )
    async def no_confirmation_action(self, request: Request, pks: list[Any]) -> str:
        return "You have successfully executed an action without confirmation"

    @action(
        name="redirect",
        text="Redirect",
        custom_response=True,
    )
    async def redirect_action(self, request: Request, pks: list[Any]) -> Response:
        return RedirectResponse("https://example.com/")

    @action(
        name="redirect_with_form",
        text="Redirect with form",
        custom_response=True,
        confirmation="Fill the form",
        form="""
            <form>
                <div class="mt-3">
                    <input type="text" class="form-control" name="value" placeholder="Enter value">
                </div>
            </form>
            """,
    )
    async def redirect_with_form(self, request: Request, pks: list[Any]) -> Response:
        data = await request.form()
        return RedirectResponse(f"https://example.com/?value={data['value']}")

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published ?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> str:
        session: Session = request.state.session
        article = await self.find_by_pk(request, pk)
        if article.status == Status.Published:
            raise ActionFailed("The article is already marked as published.")
        article.status = Status.Published
        session.add(article)
        session.commit()
        return "The article was successfully marked as published"

    @link_row_action(
        name="go_to_example",
        text="Go to example.com",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, request: Request, pk: Any) -> str:
        return f"https://example.com/?pk={pk}"
