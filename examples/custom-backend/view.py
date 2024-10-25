from collections.abc import Sequence
from operator import attrgetter
from typing import Any, Optional, Union

from starlette.requests import Request
from starlette_admin import (
    BaseModelView,
    CollectionField,
    IntegerField,
    ListField,
    StringField,
    TextAreaField,
)
from starlette_admin.exceptions import FormValidationError
from tinydb import TinyDB

from .models import Post


class PostView(BaseModelView):
    identity = "post"
    name = "Post"
    label = "Blog Posts"
    icon = "fa fa-blog"
    pk_attr = "id"
    fields = [
        IntegerField("id"),
        StringField("title"),
        TextAreaField("body"),
        ListField(StringField("tags")),
        ListField(
            CollectionField(
                "comments",
                fields=[
                    StringField("username"),
                    StringField("body", help_text="Please, be kind"),
                ],
            ),
        ),
    ]
    sortable_fields = ("id", "title", "content")
    exclude_fields_from_list = ["comments"]
    search_builder = False
    page_size = 5
    page_size_options = [5, 10, 25, -1]

    def __init__(self, db: TinyDB):
        super().__init__()
        self.db = db

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[dict[str, Any], str, None] = None,
        order_by: Optional[list[str]] = None,
    ) -> Sequence[Any]:
        docs = []
        if where is not None:
            assert not isinstance(where, dict)  # search_builder is disabled
            docs = self.db.search(Post.search_query(where))
        else:
            docs = self.db.all()
        values = [Post.from_document(doc) for doc in docs]
        if order_by is not None:
            """Multiple sort"""
            for item in reversed(order_by):
                key, dir = item.split(maxsplit=1)
                values.sort(key=attrgetter(key), reverse=(dir == "desc"))
        if limit > 0:
            return values[skip : skip + limit]
        return values[skip:]

    async def count(
        self, request: Request, where: Union[dict[str, Any], str, None] = None
    ) -> int:
        if where is not None:
            assert not isinstance(where, dict)  # search_builder is disabled
            return len(self.db.search(Post.search_query(where)))
        return len(self.db.all())

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        pk = int(pk)
        if self.db.contains(doc_id=pk):
            return Post.from_document(self.db.get(doc_id=pk))
        return None

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        return [Post.from_document(self.db.get(doc_id=pk)) for pk in map(int, pks)]

    async def validate_data(self, data: dict) -> None:
        errors = {}
        if data["title"] is None or len(data["title"]) < 3:
            errors["title"] = "Ensure title has at least 03 characters"
        if data["tags"] is None or len(data["tags"]) < 1:
            errors["tags"] = "You need at least one tag"
        if len(errors) > 0:
            raise FormValidationError(errors)

    async def create(self, request: Request, data: dict) -> Any:
        await self.validate_data(data)
        new_id = self.db.insert(Post(**data).to_dict())
        return await self.find_by_pk(request, new_id)

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        pk = int(pk)
        await self.validate_data(data)
        self.db.update(Post(**data).to_dict(), doc_ids=[pk])
        return await self.find_by_pk(request, pk)

    async def delete(self, request: Request, pks: list[Any]) -> Optional[int]:
        return len(self.db.remove(doc_ids=map(int, pks)))
