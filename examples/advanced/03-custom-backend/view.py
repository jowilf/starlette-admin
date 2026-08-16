from collections.abc import Sequence
from pathlib import Path
from typing import Any

import filetype
from filters import build_query, filter_registry
from models import Post
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette_admin import (
    BaseModelView,
    CollectionField,
    FileField,
    ImageField,
    IntegerField,
    ListField,
    StringField,
    TextAreaField,
)
from starlette_admin.exceptions import FormValidationError
from starlette_admin.fields import BaseField
from starlette_admin.filters import FilterGroup, FilterRegistry
from starlette_admin.storage import LocalStorage
from tinydb import TinyDB
from tinydb.queries import QueryInstance

local_storage = LocalStorage(base_dir=Path(__file__).parent / "assets")


def validate_attachment_bytes(
    request: Request, field: BaseField, upload: UploadFile
) -> None:
    header = upload.file.read(261)  # filetype needs up to 261 bytes
    upload.file.seek(0)
    kind = filetype.guess(header)
    if kind is None or kind.mime != "application/pdf":
        raise ValueError("File content does not match PDF format")


class PostView(BaseModelView):
    key = "post"
    display_name = "Post"
    menu_label = "Blog Posts"
    icon = "fa fa-blog"
    pk_attr = "id"
    fields = [
        IntegerField("id", filters=[]),
        StringField("title"),
        TextAreaField("body"),
        IntegerField("views"),
        ImageField(
            "cover",
            storage=local_storage,
            upload_folder="covers/",
            max_size=20 * 1024,
        ),
        FileField(
            "attachments",
            storage=local_storage,
            upload_folder="attachments/",
            multiple=True,
            max_size=5 * 1024 * 1024,
            accept=".pdf",
            validators=[validate_attachment_bytes],
        ),
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
    sortable_fields = ("id", "title", "views")
    exclude_fields_from_list = ["comments"]
    page_size = 5
    page_size_options = [5, 10, 25, -1]
    show_goto_page = True

    def __init__(self, db: TinyDB):
        super().__init__()
        self.db = db

    def can_import(self, request: Request) -> bool:
        return True

    def get_filter_registry(self) -> FilterRegistry:
        return filter_registry

    async def _build_query(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> QueryInstance | None:
        query = None
        if q is not None:
            query = Post.search_query(q)
        if filters is not None and not filters.is_empty():
            fields_by_name = {
                field.name: field for field in self.get_fields_list(request)
            }
            filter_query = build_query(
                filters, fields_by_name, self.get_filter_registry()
            )
            if filter_query is not None:
                query = filter_query if query is None else (query & filter_query)
        return query

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        sorts: list[tuple[str, str]] | None = None,
        filters: FilterGroup | None = None,
    ) -> Sequence[Any]:
        query = await self._build_query(request, q, filters)
        docs = self.db.search(query) if query is not None else self.db.all()
        values = [Post.from_document(doc) for doc in docs]
        for sort_by, sort_dir in reversed(sorts or []):
            values.sort(
                key=lambda v, s=sort_by: (getattr(v, s) is None, getattr(v, s)),
                reverse=(sort_dir == "desc"),
            )
        if limit > 0:
            return values[skip : skip + limit]
        return values[skip:]

    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        query = await self._build_query(request, q, filters)
        return len(self.db.search(query)) if query is not None else len(self.db.all())

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
        if errors:
            raise FormValidationError(errors)

    async def create(self, request: Request, data: dict) -> Any:
        await self.validate_data(data)
        obj = Post(**data)
        await self._emit_before_create(request, data, obj)
        new_id = self.db.insert(obj.to_dict())
        obj = await self.find_by_pk(request, new_id)
        await self._emit_after_create(request, obj)
        return obj

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        pk = int(pk)
        await self.validate_data(data)
        existing = self.db.get(doc_id=pk)
        old_data = dict(existing) if existing else {}
        obj = Post(**{**old_data, **data})
        await self._emit_before_edit(request, data, obj, pk=pk, old_data=old_data)
        self.db.update(Post(**data).to_dict(), doc_ids=[pk])
        obj = await self.find_by_pk(request, pk)
        await self._emit_after_edit(request, obj, pk=pk, old_data=old_data)
        return obj

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        ids = list(map(int, pks))
        objs = [
            Post.from_document(self.db.get(doc_id=i))
            for i in ids
            if self.db.contains(doc_id=i)
        ]
        for obj in objs:
            await self._emit_before_delete(
                request, await self.get_pk_value(request, obj), obj
            )
        removed = self.db.remove(doc_ids=ids)
        for obj in objs:
            await self._emit_after_delete(
                request, await self.get_pk_value(request, obj), obj
            )
        return len(removed)
