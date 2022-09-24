from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Union

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import BaseAdmin as Admin, ListField
from starlette_admin import (
    CollectionField,
    DateTimeField,
    IntegerField,
    StringField,
    TagsField,
    TextAreaField,
)
from starlette_admin.exceptions import FormValidationError
from starlette_admin.views import BaseModelView


@dataclass
class Post:
    id: int
    title: str
    content: str
    tags: List[str]
    config: dict = field(default_factory=dict)

    def is_valid_for_term(self, term: str) -> bool:
        return (
            str(term).lower() in self.title.lower()
            or str(term).lower() in self.content.lower()
            or any([str(term).lower() in tag.lower() for tag in self.tags])
        )

    def update(self, data: Dict) -> None:
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


db: Dict[int, Post] = dict()
next_id = 1


def filter_values(values: Iterable[Post], term: str) -> List[Post]:
    filtered_values = []
    for value in values:
        if value.is_valid_for_term(term):
            filtered_values.append(value)
    return filtered_values


class PostView(BaseModelView):
    identity = "post"
    name = "Post"
    label = "Blog Posts"
    icon = "fa fa-blog"
    pk_attr = "id"
    fields = [
        IntegerField("id"),
        StringField("title"),
        TextAreaField("content"),
        ListField(StringField("tags")),
        # CollectionField(
        #     "config",
        #     fields=[
        #         StringField("name", required=True),
        #         TextAreaField("description"),
        #         TagsField("tags"),
        #         DateTimeField("datetime")
        #     ],
        # ),
    ]
    sortable_fields = ("id", "title", "content")
    search_builder = True
    page_size = 10
    page_size_options = [5, 10, -1]

    async def count(
        self,
        request: Request,
        where: Union[Dict[str, Any], str, None] = None,
    ) -> int:
        values = list(db.values())
        if where is not None:
            values = filter_values(values, where)
        return len(values)

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
    ) -> List[Any]:
        values = list(db.values())
        if order_by is not None:
            assert len(order_by) < 2, "Not supported"
            if len(order_by) == 1:
                key, dir = order_by[0].split(maxsplit=1)
                values.sort(key=lambda v: getattr(v, key), reverse=(dir == "desc"))

        if where is not None and isinstance(where, (str, int)):
            values = filter_values(values, where)
        if limit > 0:
            return values[skip : skip + limit]
        return values[skip:]

    async def find_by_pk(self, request: Request, pk: Any) -> Optional[Post]:
        return db.get(int(pk), None)

    async def find_by_pks(self, request: Request, pks: List[Any]) -> List[Post]:
        return [db.get(int(pk)) for pk in pks]

    def validate_data(self, data: Dict) -> None:
        errors = {}
        if data["title"] is None or len(data["title"]) < 3:
            errors["title"] = "Ensure title has at least 03 characters"
        if data["tags"] is None or len(data["tags"]) < 1:
            errors["tags"] = "You need at least one tag"
        if len(errors) > 0:
            raise FormValidationError(errors)

    async def create(self, request: Request, data: Dict) -> Post:
        self.validate_data(data)
        global next_id
        obj = Post(id=next_id, **data)
        db[next_id] = obj
        next_id += 1
        return obj

    async def edit(self, request: Request, pk, data: Dict) -> Post:
        self.validate_data(data)
        db[int(pk)].update(data)
        return db[int(pk)]

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        cnt = 0
        for pk in pks:
            value = await self.find_by_pk(request, pk)
            if value is not None:
                del db[int(pk)]
                cnt += 1
        return cnt


def fill_db() -> None:
    values = [
        {
            "title": "His mother had always taught him",
            "tags": ["history", "american", "crime"],
        },
        {
            "title": "He was an expert but not in a discipline",
            "tags": ["french", "fiction", "english"],
        },
        {
            "title": "Dave watched as the forest burned up on the hill.",
            "tags": ["magical", "history", "french"],
        },
        {
            "title": "All he wanted was a candy bar.",
            "tags": ["mystery", "english", "american"],
        },
        {
            "title": "Hopes and dreams were dashed that day.",
            "tags": ["crime", "mystery", "love"],
        },
    ]
    for value in values:
        global next_id
        db[next_id] = Post(**value, id=next_id, content="Dummy content")
        next_id += 1


app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ]
)
fill_db()
admin = Admin()
admin.add_view(PostView)
admin.mount_to(app)
