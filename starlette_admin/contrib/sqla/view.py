from typing import Any, Dict, List, Optional, Type, Union, no_type_check

from sqlalchemy import Boolean, Column, func, inspect, select
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    ColumnProperty,
    InstrumentedAttribute,
    RelationshipProperty,
    Session,
    joinedload,
)
from starlette.requests import Request
from starlette_admin import (
    ColorField,
    EmailField,
    PhoneField,
    RelationField,
    StringField,
    TextAreaField,
    URLField,
)
from starlette_admin.contrib.sqla.exceptions import InvalidModelError
from starlette_admin.contrib.sqla.helpers import (
    build_order_clauses,
    build_query,
    convert_to_field,
    extract_column_python_type,
    normalize_list,
)
from starlette_admin.exceptions import FormValidationError
from starlette_admin.fields import BaseField, EnumField, FileField, HasMany, HasOne
from starlette_admin.helpers import prettify_class_name, slugify_class_name
from starlette_admin.views import BaseModelView


class ModelViewMeta(type):
    @no_type_check
    def __new__(mcs, name, bases, attrs: dict, **kwargs: Any):
        cls: Type["ModelView"] = super().__new__(mcs, name, bases, attrs)
        model = kwargs.get("model")
        if model is None:
            return cls
        try:
            mapper = inspect(model)
        except NoInspectionAvailable:
            raise InvalidModelError(
                f"Class {model.__name__} is not a SQLAlchemy model."
            )
        assert len(mapper.primary_key) == 1, (
            "Multiple PK columns not supported, A possible solution is to override "
            "BaseAdminModel class and put your own logic "
        )
        cls._pk_column = mapper.primary_key[0]
        cls.pk_attr = cls._pk_column.key
        cls._pk_coerce = extract_column_python_type(cls._pk_column)
        cls.model = model
        cls.identity = attrs.get("identity", slugify_class_name(cls.model.__name__))
        cls.label = attrs.get("label", prettify_class_name(cls.model.__name__) + "s")
        cls.name = attrs.get("name", prettify_class_name(cls.model.__name__))
        fields = attrs.get(
            "fields",
            [
                cls.model.__dict__[f].key
                for f in cls.model.__dict__
                if type(cls.model.__dict__[f]) is InstrumentedAttribute
            ],
        )
        converted_fields = []
        for field in fields:
            if isinstance(field, BaseField):
                converted_fields.append(field)
            else:
                if isinstance(field, InstrumentedAttribute):
                    attr = mapper.attrs.get(field.key)
                else:
                    attr = mapper.attrs.get(field)
                if attr is None:
                    raise ValueError(f"Can't find column with key {field}")
                if isinstance(attr, RelationshipProperty):
                    identity = slugify_class_name(attr.entity.class_.__name__)
                    if attr.direction.name == "MANYTOONE" or (
                        attr.direction.name == "ONETOMANY" and not attr.uselist
                    ):
                        converted_fields.append(HasOne(attr.key, identity=identity))
                    else:
                        converted_fields.append(HasMany(attr.key, identity=identity))
                elif isinstance(attr, ColumnProperty):
                    assert (
                        len(attr.columns) == 1
                    ), "Multiple-column properties are not supported"
                    column = attr.columns[0]
                    required = False
                    if column.foreign_keys:
                        continue
                    if (
                        not column.nullable
                        and not isinstance(column.type, (Boolean,))
                        and not column.default
                        and not column.server_default
                    ):
                        required = True

                    field = convert_to_field(column)
                    if field is EnumField:
                        field = EnumField.from_enum(attr.key, column.type.enum_class)
                    else:
                        field = field(attr.key)
                        if isinstance(field, FileField) and getattr(
                            column.type, "multiple", False
                        ):
                            field.multiple = True

                    field.required = required
                    converted_fields.append(field)
        cls.fields = converted_fields
        cls.exclude_fields_from_list = normalize_list(
            attrs.get("exclude_fields_from_list", [])
        )
        cls.exclude_fields_from_detail = normalize_list(
            attrs.get("exclude_fields_from_detail", [])
        )
        cls.exclude_fields_from_create = normalize_list(
            attrs.get("exclude_fields_from_create", [])
        )
        cls.exclude_fields_from_edit = normalize_list(
            attrs.get("exclude_fields_from_edit", [])
        )
        _default_list = [
            field.name
            for field in cls.fields
            if not isinstance(field, (RelationField, FileField))
        ]
        cls.searchable_fields = normalize_list(
            attrs.get("searchable_fields", _default_list)
        )
        cls.sortable_fields = normalize_list(
            attrs.get("sortable_fields", _default_list)
        )
        cls.export_fields = normalize_list(attrs.get("export_fields", None))
        return cls


class ModelView(BaseModelView, metaclass=ModelViewMeta):
    model: Type[Any]
    identity: Optional[str] = None
    pk_attr: Optional[str] = None
    _pk_column: Column
    _pk_coerce: type
    fields: List[BaseField] = []

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
                where = self.build_full_text_search_query(request, where, self.model)
            stmt = stmt.where(where)
        if isinstance(session, AsyncSession):
            return (await session.execute(stmt)).scalar_one()
        return session.execute(stmt).scalar_one()

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
                where = self.build_full_text_search_query(request, where, self.model)
            stmt = stmt.where(where)
        stmt = stmt.order_by(*build_order_clauses(order_by or [], self.model))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(field.name))
        if isinstance(session, AsyncSession):
            return (await session.execute(stmt)).scalars().unique().all()
        return session.execute(stmt).scalars().unique().all()

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        session: Union[Session, AsyncSession] = request.state.session
        stmt = select(self.model).where(self._pk_column == self._pk_coerce(pk))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(field.name))
        if isinstance(session, AsyncSession):
            return (await session.execute(stmt)).scalars().unique().one_or_none()
        return session.execute(stmt).scalars().unique().one_or_none()

    async def find_by_pks(self, request: Request, pks: List[Any]) -> List[Any]:
        session: Union[Session, AsyncSession] = request.state.session
        stmt = select(self.model).where(self._pk_column.in_(map(self._pk_coerce, pks)))
        for field in self.fields:
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(field.name))
        if isinstance(session, AsyncSession):
            return (await session.execute(stmt)).scalars().unique().all()
        return session.execute(stmt).scalars().unique().all()

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        """
        Inherit this method to validate your data.
        Raise:
            FormValidationError to display errors to users
        """

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        try:
            await self.validate(request, data)
            session: Union[Session, AsyncSession] = request.state.session
            obj = await self._populate_obj(request, self.model(), data)
            session.add(obj)
            if isinstance(session, AsyncSession):
                await session.commit()
                await session.refresh(obj)
            else:
                session.commit()
                session.refresh(obj)
            return obj
        except Exception as e:
            return self.handle_exception(e)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        try:
            await self.validate(request, data)
            session: Union[Session, AsyncSession] = request.state.session
            obj = await self.find_by_pk(request, pk)
            session.add(await self._populate_obj(request, obj, data, True))
            if isinstance(session, AsyncSession):
                await session.commit()
                await session.refresh(obj)
            else:
                session.commit()
                session.refresh(obj)
            return obj
        except Exception as e:
            self.handle_exception(e)

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
                if data.get(f"_{name}-delete", False):
                    setattr(obj, name, None)
                elif (not field.multiple and value is not None) or (
                    field.multiple and isinstance(value, list) and len(value) > 0
                ):
                    setattr(obj, name, value)
            elif isinstance(field, RelationField) and value is not None:
                foreign_model = self._find_foreign_model(field.identity)  # type: ignore
                if not field.multiple:
                    setattr(
                        obj,
                        name,
                        await foreign_model.find_by_pk(request, value),
                    )
                else:
                    setattr(
                        obj,
                        name,
                        await foreign_model.find_by_pks(request, value),
                    )
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
                session.delete(obj)
            session.commit()
        return len(objs)

    def build_full_text_search_query(
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

    async def serialize_field_value(
        self, value: Any, field: BaseField, action: str, request: Request
    ) -> Any:
        try:
            """to automatically serve sqlalchemy_file"""
            __import__("sqlalchemy_file")
            if isinstance(field, FileField) and value is not None:
                data = []
                for item in value if field.multiple else [value]:
                    path = item["path"]
                    if action == "API" and getattr(item, "thumbnail", None) is not None:
                        path = item["thumbnail"]["path"]
                    storage, file_id = path.split("/")
                    data.append(
                        {
                            "content_type": item["content_type"],
                            "filename": item["filename"],
                            "url": request.url_for(
                                request.app.state.ROUTE_NAME + ":api:file",
                                storage=storage,
                                file_id=file_id,
                            ),
                        }
                    )
                return data if field.multiple else data[0]
        except ImportError:  # pragma: no cover
            pass
        return await super().serialize_field_value(value, field, action, request)
