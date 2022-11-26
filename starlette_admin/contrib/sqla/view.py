from typing import Any, Dict, List, Optional, Type, Union

import anyio.to_thread
from sqlalchemy import Column, func, inspect, select
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, Session, joinedload
from starlette.requests import Request
from starlette_admin.contrib.sqla.exceptions import InvalidModelError
from starlette_admin.contrib.sqla.helpers import (
    build_order_clauses,
    build_query,
    extract_column_python_type,
    normalize_fields,
    normalize_list,
)
from starlette_admin.exceptions import FormValidationError
from starlette_admin.fields import (
    ColorField,
    EmailField,
    FileField,
    PhoneField,
    RelationField,
    StringField,
    TextAreaField,
    URLField,
)
from starlette_admin.helpers import prettify_class_name, slugify_class_name
from starlette_admin.views import BaseModelView


class ModelView(BaseModelView):
    def __init__(
        self,
        model: Type[Any],
        icon: Optional[str] = None,
        name: Optional[str] = None,
        label: Optional[str] = None,
        identity: Optional[str] = None,
    ):
        try:
            mapper = inspect(model)
        except NoInspectionAvailable:
            raise InvalidModelError(  # noqa B904
                f"Class {model.__name__} is not a SQLAlchemy model."
            )
        assert len(mapper.primary_key) == 1, (
            "Multiple PK columns not supported, A possible solution is to override "
            "BaseModelView class and put your own logic "
        )
        self.model = model
        self.identity = identity or slugify_class_name(self.model.__name__)
        self.label = label or prettify_class_name(self.model.__name__) + "s"
        self.name = name or prettify_class_name(self.model.__name__)
        self.icon = icon
        self._pk_column: Column = mapper.primary_key[0]
        self.pk_attr = self._pk_column.key
        self._pk_coerce = extract_column_python_type(self._pk_column)
        if self.fields is None or len(self.fields) == 0:
            self.fields = [
                self.model.__dict__[f].key
                for f in self.model.__dict__
                if type(self.model.__dict__[f]) is InstrumentedAttribute
            ]
        self.fields = normalize_fields(self.fields, mapper)
        self.exclude_fields_from_list = normalize_list(self.exclude_fields_from_list)  # type: ignore
        self.exclude_fields_from_detail = normalize_list(self.exclude_fields_from_detail)  # type: ignore
        self.exclude_fields_from_create = normalize_list(self.exclude_fields_from_create)  # type: ignore
        self.exclude_fields_from_edit = normalize_list(self.exclude_fields_from_edit)  # type: ignore
        _default_list = [
            field.name
            for field in self.fields
            if not isinstance(field, (RelationField, FileField))
        ]
        self.searchable_fields = normalize_list(
            self.searchable_fields
            if (self.searchable_fields is not None)
            else _default_list
        )
        self.sortable_fields = normalize_list(
            self.sortable_fields
            if (self.sortable_fields is not None)
            else _default_list
        )
        self.export_fields = normalize_list(self.export_fields)
        super().__init__()

    async def count(
        self,
        request: Request,
        where: Union[Dict[str, Any], str, None] = None,
    ) -> int:
        session: Union[Session, AsyncSession] = request.state.session
        stmt = select(func.count(self._pk_column))
        if where is not None:
            if isinstance(where, dict):
                where = build_query(where, self.model)
            else:
                where = await self.build_full_text_search_query(
                    request, where, self.model
                )
            stmt = stmt.where(where)
        if isinstance(session, AsyncSession):
            return (await session.execute(stmt)).scalar_one()
        return (await anyio.to_thread.run_sync(session.execute, stmt)).scalar_one()

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
    ) -> List[Any]:
        session: Union[Session, AsyncSession] = request.state.session
        stmt = select(self.model).offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        if where is not None:
            if isinstance(where, dict):
                where = build_query(where, self.model)
            else:
                where = await self.build_full_text_search_query(
                    request, where, self.model
                )
            stmt = stmt.where(where)
        stmt = stmt.order_by(*build_order_clauses(order_by or [], self.model))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(field.name))
        if isinstance(session, AsyncSession):
            return (await session.execute(stmt)).scalars().unique().all()
        return (
            (await anyio.to_thread.run_sync(session.execute, stmt))
            .scalars()
            .unique()
            .all()
        )

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        session: Union[Session, AsyncSession] = request.state.session
        stmt = select(self.model).where(self._pk_column == self._pk_coerce(pk))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(field.name))
        if isinstance(session, AsyncSession):
            return (await session.execute(stmt)).scalars().unique().one_or_none()
        return (
            (await anyio.to_thread.run_sync(session.execute, stmt))
            .scalars()
            .unique()
            .one_or_none()
        )

    async def find_by_pks(self, request: Request, pks: List[Any]) -> List[Any]:
        session: Union[Session, AsyncSession] = request.state.session
        stmt = select(self.model).where(self._pk_column.in_(map(self._pk_coerce, pks)))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(field.name))
        if isinstance(session, AsyncSession):
            return (await session.execute(stmt)).scalars().unique().all()
        return (
            (await anyio.to_thread.run_sync(session.execute, stmt))
            .scalars()
            .unique()
            .all()
        )

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        """
        Inherit this method to validate your data.
        Raise:
            FormValidationError to display errors to users
        """

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        try:
            data = await self._arrange_data(request, data)
            await self.validate(request, data)
            session: Union[Session, AsyncSession] = request.state.session
            obj = await self._populate_obj(request, self.model(), data)
            session.add(obj)
            if isinstance(session, AsyncSession):
                await session.commit()
                await session.refresh(obj)
            else:
                await anyio.to_thread.run_sync(session.commit)
                await anyio.to_thread.run_sync(session.refresh, obj)
            return obj
        except Exception as e:
            return self.handle_exception(e)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        try:
            data = await self._arrange_data(request, data, True)
            await self.validate(request, data)
            session: Union[Session, AsyncSession] = request.state.session
            obj = await self.find_by_pk(request, pk)
            session.add(await self._populate_obj(request, obj, data, True))
            if isinstance(session, AsyncSession):
                await session.commit()
                await session.refresh(obj)
            else:
                await anyio.to_thread.run_sync(session.commit)
                await anyio.to_thread.run_sync(session.refresh, obj)
            return obj
        except Exception as e:
            self.handle_exception(e)

    async def _arrange_data(
        self,
        request: Request,
        data: Dict[str, Any],
        is_edit: bool = False,
    ) -> Dict[str, Any]:
        """
        This function will return a new dict with relationships loaded from
        database.
        """
        arranged_data: Dict[str, Any] = {}
        for field in self.fields:
            if (is_edit and field.exclude_from_edit) or (
                not is_edit and field.exclude_from_create
            ):
                continue
            if isinstance(field, RelationField) and data[field.name] is not None:
                foreign_model = self._find_foreign_model(field.identity)  # type: ignore
                if not field.multiple:
                    arranged_data[field.name] = await foreign_model.find_by_pk(
                        request, data[field.name]
                    )
                else:
                    arranged_data[field.name] = await foreign_model.find_by_pks(
                        request, data[field.name]
                    )
            else:
                arranged_data[field.name] = data[field.name]
        return arranged_data

    async def _populate_obj(
        self,
        request: Request,
        obj: Any,
        data: Dict[str, Any],
        is_edit: bool = False,
    ) -> Any:
        for field in self.fields:
            if (is_edit and field.exclude_from_edit) or (
                not is_edit and field.exclude_from_create
            ):
                continue
            name, value = field.name, data.get(field.name, None)
            if isinstance(field, FileField):
                value, should_be_deleted = value
                if should_be_deleted:
                    setattr(obj, name, None)
                elif (not field.multiple and value is not None) or (
                    field.multiple and isinstance(value, list) and len(value) > 0
                ):
                    setattr(obj, name, value)
            else:
                setattr(obj, name, value)
        return obj

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        session: Union[Session, AsyncSession] = request.state.session
        objs = await self.find_by_pks(request, pks)
        if isinstance(session, AsyncSession):
            for obj in objs:
                await session.delete(obj)
            await session.commit()
        else:
            for obj in objs:
                await anyio.to_thread.run_sync(session.delete, obj)
            await anyio.to_thread.run_sync(session.commit)
        return len(objs)

    async def build_full_text_search_query(
        self, request: Request, term: str, model: Any
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {"or": []}
        for field in self.fields:
            if field.searchable and type(field) in [
                StringField,
                TextAreaField,
                EmailField,
                URLField,
                PhoneField,
                ColorField,
            ]:
                query["or"].append({field.name: {"contains": term}})
        return build_query(query, model)

    def handle_exception(self, exc: Exception) -> None:
        try:
            """Automatically handle sqlalchemy_file error"""
            sqlalchemy_file = __import__("sqlalchemy_file")
            if isinstance(exc, sqlalchemy_file.exceptions.ValidationError):
                raise FormValidationError({exc.key: exc.msg})
        except ImportError:  # pragma: no cover
            pass
        raise exc  # pragma: no cover
