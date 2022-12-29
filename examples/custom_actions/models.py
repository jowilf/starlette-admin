import enum
from typing import Any, List

from sqlalchemy import Column, Enum, Integer, String, Text
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette_admin import action
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
    status = Column(Enum(Status))


class ArticleView(ModelView):
    exclude_fields_from_list = [Article.body]
    actions = ["make_published", "delete", "always_failed", "no_confirmation"]

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        form="""<div class="form-floating mb-3">
        <input name="tags" class="form-control" id="floating-input" value="">
        <label for="floating-input">Tags</label>
        </div>""",
    )
    async def make_published_action(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        for article in await self.find_by_pks(request, pks):
            article.status = Status.Published
            session.add(article)
        session.commit()
        return "{} articles were successfully marked as published (tags: {})".format(
            len(pks), request.query_params["tags"]
        )

    @action(
        name="always_failed",
        text="Always Failed",
        confirmation="This action will fail, do you want to continue ?",
        submit_btn_text="Continue",
        submit_btn_class="btn-outline-danger",
    )
    async def always_failed_action(self, request: Request, pks: List[Any]) -> str:
        raise ActionFailed("Sorry, We can't proceed this action now.")

    @action(
        name="no_confirmation",
        text="No confirmation action",
    )
    async def no_confirmation_action(self, request: Request, pks: List[Any]) -> str:
        return "You have successfully executed an action without confirmation"
