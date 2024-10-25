from typing import Any

from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette_admin import action
from starlette_admin.contrib.sqla import ModelView

from .model import Article, Status


class ArticleView(ModelView):
    exclude_fields_from_list = [Article.body]

    def can_view_details(self, request: Request) -> bool:
        return "read" in request.state.user["roles"]

    def can_create(self, request: Request) -> bool:
        return "create" in request.state.user["roles"]

    def can_edit(self, request: Request) -> bool:
        return "edit" in request.state.user["roles"]

    def can_delete(self, request: Request) -> bool:
        return "delete" in request.state.user["roles"]

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "action_make_published" in request.state.user["roles"]
        return await super().is_action_allowed(request, name)

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
