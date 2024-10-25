from collections.abc import Iterable
from typing import Any, Optional, Union

from pydantic import BaseModel
from requests import Request
from starlette_admin import HasMany, HasOne
from starlette_admin.helpers import prettify_class_name, slugify_class_name
from starlette_admin.views import BaseModelView


class DummyBaseModel(BaseModel):
    id: int

    def is_valid_for_term(self, term, searchable_fields):
        for field in searchable_fields:
            attr = getattr(self, field)
            if attr is not None and str(term).lower() in str(attr).lower():
                return True
        return False

    def update(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class DummyModelView(BaseModelView):
    """Custom ModelView which store data in memory only for testing purpose"""

    pk_attr = "id"
    model: Optional[type[DummyBaseModel]] = None
    db: dict[int, DummyBaseModel] = {}
    seq = 1

    def __init__(self):
        self.identity = slugify_class_name(self.model.__name__)
        self.name = prettify_class_name(self.model.__name__)
        self.label = prettify_class_name(self.model.__name__) + "s"
        super().__init__()

    def filter_values(self, values: Iterable[DummyBaseModel], term):
        filtered_values = []
        for value in values:
            if value.is_valid_for_term(term, self.searchable_fields):
                filtered_values.append(value)
        return filtered_values

    async def count(
        self,
        request: Request,
        where: Union[dict[str, Any], str, None] = None,
    ) -> int:
        values = list(self.db.values())
        if where is not None and isinstance(where, (str, int)):
            values = self.filter_values(values, where)
        return len(values)

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[dict[str, Any], str, None] = None,
        order_by: Optional[list[str]] = None,
    ) -> list[Any]:
        db = type(self).db
        values = list(db.values())
        if order_by is not None:
            for clause in order_by:
                key, dir = clause.split(maxsplit=1)
                values = sorted(
                    values,
                    key=lambda v: getattr(v, key),  # B023
                    reverse=(dir == "desc"),
                )
        if where is not None and isinstance(where, (str, int)):
            values = self.filter_values(values, where)
        if limit > 0:
            return values[skip : skip + limit]
        return values[skip:]

    async def find_by_pk(self, request: Request, pk):
        return type(self).db.get(int(pk), None)

    async def find_by_pks(self, request: Request, pks) -> list[Any]:
        return [type(self).db.get(int(pk)) for pk in pks]

    async def validate_data(self, data: dict):
        pass

    async def arrange(self, request: Request, data: dict):
        for field in self.fields:
            if isinstance(field, HasOne) and data[field.name] is not None:
                data[field.name] = await self._find_foreign_model(
                    field.identity
                ).find_by_pk(request, int(data[field.name]))
            elif isinstance(field, HasMany) and data[field.name] is not None:
                data[field.name] = await self._find_foreign_model(
                    field.identity
                ).find_by_pks(request, list(map(int, data[field.name])))
        return data

    async def create(self, request: Request, data: dict):
        data = await self.arrange(request, data)
        await self.validate_data(data)
        obj = self.model(id=type(self).seq, **data)
        type(self).db[type(self).seq] = obj
        type(self).seq += 1
        return obj

    async def edit(self, request: Request, pk, data: dict):
        data = await self.arrange(request, data)
        await self.validate_data(data)
        type(self).db[int(pk)].update(data)
        return type(self).db[int(pk)]

    async def delete(self, request: Request, pks: list[Any]) -> Optional[int]:
        cnt = 0
        for pk in pks:
            value = await self.find_by_pk(request, pk)
            if value is not None:
                del type(self).db[int(pk)]
                cnt += 1
        return cnt
