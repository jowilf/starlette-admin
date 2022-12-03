import enum
from typing import Any, List, Optional

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


class ArticleAdmin(ModelView):
    exclude_fields_from_list = [Article.body]

    @action(
        name="delete",
        text="Delete selected articles",
        confirmation="Are you sure you want to delete this articles ?",
        submit_btn_text="Yes, delete them all",
        submit_btn_class="btn-danger",
    )
    async def delete_action(self, request: Request, pks: List[Any]) -> Optional[int]:
        """
        You can override the default delete action with your own logic or configuration.
        To deactivate, just remove the action decorator
        """
        return await self.delete(request, pks)

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published(self, request: Request, pks: List[Any]) -> Optional[int]:
        session: Session = request.state.session
        for article in await self.find_by_pks(request, pks):
            article.status = Status.Published
            session.add(article)
        session.commit()
        return len(pks)

    @action(
        name="always_failed",
        text="Always Failed",
        confirmation="This action will fail, do you want to continue ?",
        submit_btn_text="Continue",
        submit_btn_class="btn-outline-danger",
    )
    async def always_failed(self, request: Request, pks: List[Any]) -> Optional[int]:
        raise ActionFailed("Your action just failed")
