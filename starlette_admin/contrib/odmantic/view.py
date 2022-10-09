from typing import Any, Dict, Iterable, List, Optional, Type, Union

import anyio
from bson import ObjectId
from odmantic import AIOEngine, Model, Reference, SyncEngine, query
from odmantic.field import FieldProxy
from odmantic.query import QueryExpression
from pydantic import ValidationError
from starlette.requests import Request
from starlette_admin import BaseField, CollectionField, HasMany, HasOne, ListField, StringField, TextAreaField, \
    EmailField, RelationField
from starlette_admin.contrib.odmantic.helpers import (
    convert_odm_field_to_admin_field,
    normalize_list,
    resolve_query,
)
from starlette_admin.helpers import (
    prettify_class_name,
    pydantic_error_to_form_validation_errors,
    slugify_class_name,
)
from starlette_admin.views import BaseModelView


class ModelView(BaseModelView):
    def __init__(
        self,
        model: Type[Model],
        icon: Optional[str] = None,
        name: Optional[str] = None,
        label: Optional[str] = None,
        identity: Optional[str] = None,
    ):
        self.model = model
        self.identity = identity or slugify_class_name(self.model.__name__)
        self.label = label or prettify_class_name(self.model.__name__) + "s"
        self.name = name or prettify_class_name(self.model.__name__)
        self.icon = icon
        self.pk_attr = "id"
        if self.fields is None or len(self.fields) == 0:
            _all_list = list(model.__odm_fields__.keys())
            self.fields = _all_list[-1:] + _all_list[:-1]  # Move 'id' to start
        converted_fields = []
        for value in self.fields:
            if isinstance(value, BaseField):
                converted_fields.append(value)
            else:
                if isinstance(value, FieldProxy):
                    field_name = +value
                elif isinstance(value, str) and hasattr(model, value):
                    field_name = value
                else:
                    raise ValueError(f"Can't find column with key {value}")
                converted_fields.append(
                    convert_odm_field_to_admin_field(
                        model.__odm_fields__[field_name],
                        field_name,
                        model.__annotations__[field_name],
                    )
                )
        self.fields = converted_fields
        self.exclude_fields_from_list = normalize_list(self.exclude_fields_from_list)  # type: ignore
        self.exclude_fields_from_detail = normalize_list(self.exclude_fields_from_detail)  # type: ignore
        self.exclude_fields_from_create = normalize_list(self.exclude_fields_from_create)  # type: ignore
        self.exclude_fields_from_edit = normalize_list(self.exclude_fields_from_edit)  # type: ignore
        self.searchable_fields = normalize_list(self.searchable_fields)
        self.sortable_fields = normalize_list(self.sortable_fields)
        self.export_fields = normalize_list(self.export_fields)
        super().__init__()

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
    ) -> Iterable[Any]:
        engine: Union[AIOEngine, SyncEngine] = request.state.engine
        q = await self._build_query(request, where)
        o = await self._build_order_clauses(order_by)
        print(q)
        if isinstance(engine, AIOEngine):
            return await engine.find(
                self.model,
                q,
                sort=o,
                skip=skip,
                limit=limit,
            )
        return await anyio.to_thread.run_sync(
            lambda: engine.find(
                self.model,
                q,
                sort=self._build_order_clauses(order_by),
                skip=skip,
                limit=limit,
            )
        )

    async def count(
        self, request: Request, where: Union[Dict[str, Any], str, None] = None
    ) -> int:
        engine: Union[AIOEngine, SyncEngine] = request.state.engine
        if isinstance(engine, AIOEngine):
            return await engine.count(
                self.model, await self._build_query(request, where)
            )
        return await anyio.to_thread.run_sync(
            engine.count, self.model, self._build_query(request, where)
        )

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        engine: Union[AIOEngine, SyncEngine] = request.state.engine
        if isinstance(engine, AIOEngine):
            return await engine.find_one(self.model, self.model.id == ObjectId(pk))
        return await anyio.to_thread.run_sync(
            engine.find_one, self.model, self.model.id == ObjectId(pk)
        )

    async def find_by_pks(self, request: Request, pks: List[Any]) -> Iterable[Any]:
        pks = map(ObjectId, pks)
        engine: Union[AIOEngine, SyncEngine] = request.state.engine
        if isinstance(engine, AIOEngine):
            return await engine.find(self.model, self.model.id.in_(pks))
        return await anyio.to_thread.run_sync(
            engine.find, self.model, self.model.id.in_(pks)
        )

    async def create(self, request: Request, data: Dict) -> Any:
        engine: Union[AIOEngine, SyncEngine] = request.state.engine
        data = await self._arrange_data(request, data)
        try:
            if isinstance(engine, AIOEngine):
                return await engine.save(self.model(**data))
            return await anyio.to_thread.run_sync(engine.save, self.model(**data))
        except Exception as e:
            self.handle_exception(e)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        engine: Union[AIOEngine, SyncEngine] = request.state.engine
        data = await self._arrange_data(request, data, is_edit=True)
        try:
            instance = await self.find_by_pk(request, pk)
            instance.update(data)
            if isinstance(engine, AIOEngine):
                return await engine.save(instance)
            return await anyio.to_thread.run_sync(engine.save, instance)
        except Exception as e:
            self.handle_exception(e)

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        pks = map(ObjectId, pks)
        engine: Union[AIOEngine, SyncEngine] = request.state.engine
        if isinstance(engine, AIOEngine):
            return await engine.remove(self.model, self.model.id.in_(pks))
        return await anyio.to_thread.run_sync(engine.remove, self.model.id.in_(pks))

    def handle_exception(self, exc: Exception) -> None:
        if isinstance(exc, ValidationError):
            raise pydantic_error_to_form_validation_errors(exc)
        raise exc  # pragma: no cover

    async def _arrange_data(
        self,
        request: Request,
        data: Dict[str, Any],
        is_edit: bool = False,
        fields: Optional[List[BaseField]] = None,
    ):
        arranged_data = dict()
        if fields is None:
            fields = self.fields
        for field in fields:
            if (is_edit and field.exclude_from_edit) or (
                not is_edit and field.exclude_from_create
            ):
                continue
            name, value = field.name, data.get(field.name, None)
            if isinstance(field, CollectionField) and value is not None:
                arranged_data[name] = await self._arrange_data(
                    request, value, is_edit, field.fields
                )
            elif (
                isinstance(field, ListField)
                and isinstance(field.field, CollectionField)
                and value is not None
            ):
                arranged_data[name] = [
                    await self._arrange_data(request, v, is_edit, field.field.fields)
                    for v in value
                ]
            elif isinstance(field, HasOne) and value is not None:
                arranged_data[name] = await self._find_foreign_model(
                    field.identity
                ).find_by_pk(request, value)
            elif isinstance(field, HasMany) and value is not None:
                arranged_data[name] = [ObjectId(v) for v in value]
            else:
                arranged_data[name] = value
        return arranged_data

    async def _build_query(
        self, request: Request, where: Union[Dict[str, Any], str, None] = None
    ) -> Any:
        print(where)
        if where is None:
            return {}
        if isinstance(where, dict):
            return resolve_query(where, self.model)
        else:
            return await self.build_full_text_search_query(request, where)

    async def _build_order_clauses(self, order_list: List[str]):
        clauses = []
        for value in order_list:
            key, order = value.strip().split(maxsplit=1)
            clause = getattr(self.model, key)
            clauses.append(clause.desc() if order.lower() == "desc" else clause)
        return tuple(clauses) if len(clauses) > 0 else None

    async def build_full_text_search_query(
        self, request: Request, term: str
    ) -> QueryExpression:
        _list = []
        for field in self.fields:
            if field.searchable and field.name != "id" and not issubclass(type(field), (ListField, CollectionField, RelationField)) :
                _list.append(getattr(self.model, field.name).match(term))
        print(query.or_(*_list))
        return query.or_(*_list) if len(_list) > 0 else QueryExpression({})


if __name__ == "__main__":

    class Publisher(Model):
        name: str
        founded: int
        location: str

    class Book(Model):
        title: str
        pages: int
        publisher: Publisher = Reference()

    print(Book.__annotations__)
    print(ModelView(Book).fields)

    exit()

    engine = SyncEngine()
    engine.remove(Book)
    engine.remove(Publisher)

    hachette = Publisher(name="Hachette Livre", founded=1826, location="FR")
    harper = Publisher(name="HarperCollins", founded=1989, location="US")
    engine.save(hachette)
    books = [
        Book(title="They Didn't See Us Coming", pages=304, publisher=hachette),
        Book(title="This Isn't Happening", pages=256, publisher=hachette),
        Book(title="Prodigal Summer", pages=464, publisher=harper),
    ]

    # engine.save_all(books)
    print(list(engine.find_one(Book, Book.pages == 304)))
