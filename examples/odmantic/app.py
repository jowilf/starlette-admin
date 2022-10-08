import datetime
from typing import Any, Dict, List, Optional, Union

from bson import ObjectId
from odmantic import AIOEngine, Field, Model, Reference
from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route

from examples.odmantic.helpers import build_raw_query
from starlette_admin import BaseModelView, EnumField, IntegerField, StringField
from starlette_admin.contrib.odmantic import ModelView, Admin
from starlette_admin.exceptions import FormValidationError

engine = AIOEngine()
app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ]
)


class Author(Model):
    name: str = Field(min_length=3, max_length=100, key_name="db_name")
    age: int = Field(ge=5, lt=150)
    sex: Optional[str]
    tags: Optional[List[str]]
    dts: Optional[List[datetime.datetime]]


class Book(Model):
    title: str
    pages: int
    publisher: Author = Reference()


def build_query(where: Union[Dict[str, Any], str, None] = None) -> Any:
    if where is None:
        return {}
    if isinstance(where, dict):
        return build_raw_query(where)  # from mongoengine integration
    else:
        return Author.name.match(where)


def build_order_clauses(order_list: List[str]):
    clauses = []
    for value in order_list:
        key, order = value.strip().split(maxsplit=1)
        clause = getattr(Author, key)
        clauses.append(clause.desc() if order.lower() == "desc" else clause)
    return tuple(clauses) if len(clauses) > 0 else None


def pydantic_error_to_form_validation_errors(exc: ValidationError):
    errors: Dict[str, str] = dict()
    for pydantic_error in exc.errors():
        errors[str(pydantic_error["loc"][-1])] = pydantic_error["msg"]
    return FormValidationError(errors)


class AuthorView(BaseModelView):
    identity = "author"
    name = "Author"
    label = "Authors"
    pk_attr = "id"
    fields = [
        StringField("id"),
        StringField("name"),
        IntegerField("age"),
        EnumField.from_choices("sex", [("male", "MALE"), ("female", "FEMALE")]),
    ]

    async def count(
            self,
            request: Request,
            where: Union[Dict[str, Any], str, None] = None,
    ) -> int:
        return await engine.count(Author, build_query(where))

    async def find_all(
            self,
            request: Request,
            skip: int = 0,
            limit: int = 100,
            where: Union[Dict[str, Any], str, None] = None,
            order_by: Optional[List[str]] = None,
    ) -> List[Any]:
        return await engine.find(
            Author,
            build_query(where),
            sort=build_order_clauses(order_by),
            skip=skip,
            limit=limit,
        )

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        return await engine.find_one(Author, Author.id == ObjectId(pk))

    async def find_by_pks(self, request: Request, pks: List[Any]) -> List[Any]:
        return await engine.find(Author.id.in_(pks))

    async def create(self, request: Request, data: Dict) -> Any:
        try:
            return await engine.save(Author(**data))
        except ValidationError as exc:
            raise pydantic_error_to_form_validation_errors(exc)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        try:
            author = await self.find_by_pk(request, pk)
            author.update(data)
            return await engine.save(author)
        except ValidationError as exc:
            raise pydantic_error_to_form_validation_errors(exc)


admin = Admin(AIOEngine())
admin.add_view(ModelView(Author))
admin.add_view(ModelView(Book))
# admin.add_view(AuthorView)
admin.mount_to(app)
