from collections.abc import Callable, Sequence
from typing import Any, ClassVar

import anyio.to_thread
from sqlalchemy import String, and_, cast, func, inspect, or_, select, tuple_
from sqlalchemy.exc import DBAPIError, NoInspectionAvailable, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    InstrumentedAttribute,
    Mapper,
    RelationshipProperty,
    Session,
    joinedload,
)
from sqlalchemy.sql import Select
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin import BaseField, HasMany
from starlette_admin.actions import ActionSelection
from starlette_admin.contrib.sqla.converters import (
    BaseSQLAModelConverter,
    ModelConverter,
)
from starlette_admin.contrib.sqla.exceptions import InvalidModelError
from starlette_admin.contrib.sqla.fields import MultiplePKField
from starlette_admin.contrib.sqla.filters import SqlaFilterRegistry, build_filter_clause
from starlette_admin.contrib.sqla.helpers import (
    extract_column_python_type,
    normalize_list,
)
from starlette_admin.exceptions import ActionFailed, FormValidationError
from starlette_admin.fields import (
    ColorField,
    EmailField,
    EnumField,
    FileField,
    PhoneField,
    RelationField,
    SlugField,
    StringField,
    TextAreaField,
    URLField,
)
from starlette_admin.filters import FilterGroup, FilterRegistry
from starlette_admin.helpers import (
    not_none,
    on_commit,
    prettify_class_name,
    slugify_class_name,
)
from starlette_admin.logging import get_logger
from starlette_admin.tools import iterdecode
from starlette_admin.views import BaseModelView
from starlette_admin.views import InlineModelView as BaseInlineModelView

_log = get_logger(__name__)


class ModelView(BaseModelView):
    """A view for managing SQLAlchemy models."""

    sortable_field_mapping: ClassVar[dict[str, InstrumentedAttribute]] = {}
    """A dictionary for overriding the default model attribute used for sorting.

    Example:
        ```python
        class Post(Base):
            __tablename__ = "post"

            id: Mapped[int] = mapped_column(primary_key=True)
            title: Mapped[str] = mapped_column()
            user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
            user: Mapped[User] = relationship(back_populates="posts")


        class PostView(ModelView):
            sortable_field = ["id", "title", "user"]
            sortable_field_mapping = {
                "user": User.age,  # Sort by the age of the related user
            }
        ```
    """

    def __init__(
        self,
        model: type[Any],
        icon: str | None = None,
        display_name: str | None = None,
        menu_label: str | None = None,
        key: str | None = None,
        converter: BaseSQLAModelConverter | None = None,
    ):
        _log.debug("Initializing ModelView for model %s", model.__name__)
        try:
            mapper: Mapper = inspect(model)
        except NoInspectionAvailable:
            _log.error("Class %s is not a SQLAlchemy model", model.__name__)
            raise InvalidModelError(  # noqa B904
                f"Class {model.__name__} is not a SQLAlchemy model."
            )
        self.model = model
        self.key = key or self.key or slugify_class_name(self.model.__name__)
        self.menu_label = (
            menu_label
            or self.menu_label
            or prettify_class_name(self.model.__name__) + "s"
        )
        self.display_name = (
            display_name
            or self.display_name
            or prettify_class_name(self.model.__name__)
        )
        self.icon = icon or self.icon
        explicit_fields = self.fields is not None and len(self.fields) > 0
        if not explicit_fields:
            self.fields = [
                self.model.__dict__[f].key
                for f in list(self.model.__dict__.keys())
                if type(self.model.__dict__[f]) is InstrumentedAttribute
            ]
        self.fields = (converter or ModelConverter()).convert_fields_list(
            fields=self.fields,
            model=self.model,
            mapper=mapper,
            explicit_fields=explicit_fields,
        )
        self._columns: set[str] = {attr.key for attr in mapper.column_attrs}
        self._setup_primary_key()
        self.exclude_fields_from_list = (
            normalize_list(self.exclude_fields_from_list) or []
        )
        self.exclude_fields_from_detail = (
            normalize_list(self.exclude_fields_from_detail) or []
        )
        self.exclude_fields_from_create = (
            normalize_list(self.exclude_fields_from_create) or []
        )
        self.exclude_fields_from_edit = (
            normalize_list(self.exclude_fields_from_edit) or []
        )
        self.exclude_fields_from_export = (
            normalize_list(self.exclude_fields_from_export) or []
        )
        self.exclude_fields_from_import = (
            normalize_list(self.exclude_fields_from_import) or []
        )
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
        self.fields_default_sort = normalize_list(
            self.fields_default_sort, is_default_sort_list=True
        )
        super().__init__()
        _log.info(
            "ModelView for %s registered (key=%r, pk=%s, %d field(s))",
            self.model.__name__,
            self.key,
            self.pk_attr,
            len(self.fields),
        )

    def _setup_primary_key(self) -> None:
        # Detect the model's primary key attribute(s).
        _pk_attrs = []
        self._pk_column: tuple[InstrumentedAttribute, ...] | InstrumentedAttribute = ()
        self._pk_coerce: tuple[type, ...] | type = ()
        for key in list(self.model.__dict__.keys()):
            attr = getattr(self.model, key)
            if isinstance(attr, InstrumentedAttribute) and getattr(
                attr, "primary_key", False
            ):
                _pk_attrs.append(key)
        _log.debug(
            "Primary key detection for %s: found %s",
            self.model.__name__,
            _pk_attrs,
        )
        if len(_pk_attrs) > 1:
            _log.debug("Composite PK for %s: %s", self.model.__name__, _pk_attrs)
            self._pk_column = tuple(getattr(self.model, attr) for attr in _pk_attrs)
            self._pk_coerce = tuple(
                extract_column_python_type(c) for c in self._pk_column
            )
            self.pk_field: BaseField = MultiplePKField(_pk_attrs)
        else:
            assert len(_pk_attrs) == 1, (
                f"No primary key found in model {self.model.__name__}"
            )
            self._pk_column = getattr(self.model, _pk_attrs[0])
            self._pk_coerce = extract_column_python_type(self._pk_column)  # type: ignore[arg-type]
            try:
                # Reuse the already-converted field if the PK is declared.
                self.pk_field = next(f for f in self.fields if f.name == _pk_attrs[0])
            except StopIteration:
                # The PK is not among the declared fields, so fall back to
                # treating its value as a plain string.
                _log.warning(
                    "%s: PK field %r not in declared fields, falling back to StringField",
                    self.model.__name__,
                    _pk_attrs[0],
                )
                self.pk_field = StringField(_pk_attrs[0])
        self.pk_attr = self.pk_field.name

    async def handle_action(
        self, request: Request, selection: ActionSelection, name: str
    ) -> None | Response:
        try:
            return await super().handle_action(request, selection, name)
        except SQLAlchemyError as exc:
            _log.error(
                "SQLAlchemyError in action %r (model=%s): %s",
                name,
                self.model.__name__,
                exc,
                exc_info=True,
            )
            raise ActionFailed(str(exc)) from exc

    async def handle_row_action(
        self, request: Request, pk: Any, name: str
    ) -> None | Response:
        try:
            return await super().handle_row_action(request, pk, name)
        except SQLAlchemyError as exc:
            _log.error(
                "SQLAlchemyError in row action %r (model=%s, pk=%r): %s",
                name,
                self.model.__name__,
                pk,
                exc,
                exc_info=True,
            )
            raise ActionFailed(str(exc)) from exc

    def get_detail_query(self, request: Request) -> Select:
        """Return the base `Select` statement used by
        [find_by_pk][starlette_admin.views.BaseModelView.find_by_pk] and
        [find_by_pks][starlette_admin.views.BaseModelView.find_by_pks].

        Defaults to [get_list_query][starlette_admin.contrib.sqla.ModelView.get_list_query]
        so overrides of the latter (e.g. eager loading options) also apply
        to the detail view.

        Examples:
            ```python  hl_lines="3-4"
            class PostView(ModelView):

                    def get_detail_query(self, request: Request):
                        return super().get_detail_query(request).options(selectinload(Post.author))
            ```
        """
        return self.get_list_query(request)

    def get_list_query(self, request: Request) -> Select:
        """Return the base `Select` statement used by
        [find_all][starlette_admin.views.BaseModelView.find_all].

        Examples:
            ```python  hl_lines="3-4"
            class PostView(ModelView):

                    def get_list_query(self, request: Request):
                        return super().get_list_query().where(Post.published == true())

                    def get_count_query(self, request: Request):
                        return super().get_count_query().where(Post.published == true())
            ```

        If you override this method, also override
        [get_count_query][starlette_admin.contrib.sqla.ModelView.get_count_query]
        so the list view displays the correct item count.
        """
        return select(self.model)

    def get_count_query(self, request: Request) -> Select:
        """Return the base `Select` statement used by
        [count][starlette_admin.views.BaseModelView.count].

        Examples:
            ```python hl_lines="6-7"
            class PostView(ModelView):

                    def get_list_query(self, request: Request):
                        return super().get_list_query().where(Post.published == true())

                    def get_count_query(self, request: Request):
                        return super().get_count_query().where(Post.published == true())
            ```
        """
        return select(func.count()).select_from(self.model)

    def get_search_query(self, request: Request, term: str) -> Any:
        """Return the SQLAlchemy WHERE clause used for full-text search.

        Parameters:
           request: The request being processed.
           term: The search term entered by the user.

        Examples:
           ```python
           class PostView(ModelView):

                def get_search_query(self, request: Request, term: str):
                    return Post.title.contains(term)
           ```
        """
        clauses = []
        for field in self.get_fields_list(request):
            if field.searchable and type(field) in [
                StringField,
                SlugField,
                TextAreaField,
                EmailField,
                URLField,
                PhoneField,
                ColorField,
                EnumField,
            ]:
                attr = getattr(self.model, field.name)
                clauses.append(cast(attr, String).ilike(f"%{term}%"))
        return or_(*clauses)

    def get_filter_registry(self) -> FilterRegistry:
        """Return the [FilterRegistry][starlette_admin.filters.FilterRegistry]
        of concrete SQLAlchemy filter implementations
        (`starlette_admin.contrib.sqla.filters`) used to determine which
        filters are available for each field on this view's list page.
        """
        return SqlaFilterRegistry()

    async def _apply_search_and_filters(
        self,
        request: Request,
        stmt: Select,
        q: str | None,
        filters: FilterGroup | None,
    ) -> Select:
        if q is not None:
            _log.debug("Applying full-text search q=%r to %s", q, self.model.__name__)
            stmt = stmt.where(
                await self.build_full_text_search_query(request, q, self.model)
            )
        if filters is not None and not filters.is_empty():
            _log.debug("Applying filter group to %s", self.model.__name__)
            fields_by_name = {f.name: f for f in self.get_fields_list(request)}
            clause = build_filter_clause(
                filters, fields_by_name, self.get_filter_registry(), self, request
            )
            if clause is not None:
                stmt = stmt.where(clause)
        return stmt

    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        _log.debug(
            "count %s (q=%r, has_filters=%s)",
            self.model.__name__,
            q,
            filters is not None and not filters.is_empty(),
        )
        session: Session | AsyncSession = request.state.session
        stmt = await self._apply_search_and_filters(
            request, self.get_count_query(request), q, filters
        )
        if isinstance(session, AsyncSession):
            n = (await session.execute(stmt)).scalar_one()
        else:
            n = (await anyio.to_thread.run_sync(session.execute, stmt)).scalar_one()
        _log.debug("count %s → %d", self.model.__name__, n)
        return n

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        sorts: Sequence[tuple[str, str]] | None = None,
        filters: FilterGroup | None = None,
    ) -> Sequence[Any]:
        _log.debug(
            "find_all %s (skip=%d, limit=%d, q=%r, sorts=%r)",
            self.model.__name__,
            skip,
            limit,
            q,
            sorts,
        )
        session: Session | AsyncSession = request.state.session
        stmt = self.get_list_query(request).offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        stmt = await self._apply_search_and_filters(request, stmt, q, filters)
        stmt = self.build_order_clauses(request, sorts or [], stmt)
        for field in self.get_fields_list(request):
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))
        if isinstance(session, AsyncSession):
            rows = (await session.execute(stmt)).scalars().unique().all()
        else:
            rows = (
                (await anyio.to_thread.run_sync(session.execute, stmt))
                .scalars()
                .unique()
                .all()
            )
        _log.debug("find_all %s → %d row(s)", self.model.__name__, len(rows))
        return rows

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        _log.debug("find_by_pk %s pk=%r", self.model.__name__, pk)
        session: Session | AsyncSession = request.state.session
        if isinstance(self._pk_column, tuple):
            # For a composite primary key, `pk` is a comma-separated string
            # of each primary key attribute's value. For a model with two
            # primary keys (id1, id2), `pk` is "val1,val2" and the generated
            # clause is (id1 == val1 AND id2 == val2).
            assert isinstance(self._pk_coerce, tuple)
            clause = and_(
                *(
                    (
                        _pk_col == _coerce(_pk)
                        if _coerce is not bool
                        # bool("False") is True, so compare the decoded string directly.
                        else _pk_col == (_pk == "True")
                    )
                    for _pk_col, _coerce, _pk in zip(
                        self._pk_column,
                        self._pk_coerce,
                        iterdecode(pk),
                    )
                )
            )
        else:
            assert isinstance(self._pk_coerce, type)
            clause = self._pk_column == self._pk_coerce(pk)
        stmt = self.get_detail_query(request).where(clause)
        for field in self.get_fields_list(request):
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))
        if isinstance(session, AsyncSession):
            obj = (await session.execute(stmt)).scalars().unique().one_or_none()
        else:
            obj = (
                (await anyio.to_thread.run_sync(session.execute, stmt))
                .scalars()
                .unique()
                .one_or_none()
            )
        if obj is None:
            _log.warning("find_by_pk %s pk=%r → not found", self.model.__name__, pk)
        return obj

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        _log.debug("find_by_pks %s: %d pk(s)", self.model.__name__, len(pks))
        has_multiple_pks = isinstance(self._pk_column, tuple)
        try:
            return await self._exec_find_by_pks(request, pks)
        except DBAPIError:  # pragma: no cover
            if has_multiple_pks:
                # The composite IN construct can fail on backends that don't
                # support it; retry with an equivalent OR-of-ANDs clause.
                # Not covered by the test suite: SQLite, MySQL, and
                # PostgreSQL all support the composite IN construct.
                _log.warning(
                    "find_by_pks %s: composite IN failed (DBAPIError), retrying with OR clauses",
                    self.model.__name__,
                )
                return await self._exec_find_by_pks(request, pks, False)
            raise

    async def _exec_find_by_pks(
        self, request: Request, pks: list[Any], use_composite_in: bool = True
    ) -> Sequence[Any]:
        session: Session | AsyncSession = request.state.session

        if isinstance(self._pk_column, tuple):
            # Composite primary key: build a multi-column WHERE clause.
            clause = await self._get_multiple_pks_in_clause(pks, use_composite_in)
        else:
            assert isinstance(self._pk_coerce, type)
            clause = self._pk_column.in_(map(self._pk_coerce, pks))
        stmt = self.get_detail_query(request).where(clause)
        for field in self.get_fields_list(request):
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))
        if isinstance(session, AsyncSession):
            return (await session.execute(stmt)).scalars().unique().all()
        return (
            (await anyio.to_thread.run_sync(session.execute, stmt))
            .scalars()
            .unique()
            .all()
        )

    async def _get_multiple_pks_in_clause(
        self, pks: list[Any], use_composite_in: bool
    ) -> Any:
        """Build the WHERE clause for a model with a composite primary key.

        Parameters:
            pks: Comma-separated primary key values, e.g.
                `["val1,val2", "val3,val4"]` for a model with two PK columns.
            use_composite_in: If `True`, build the clause with SQLAlchemy's
                composite IN construct: `WHERE (id1, id2) IN ((val1, val2),
                (val3, val4))`. Not all database backends support this (see
                https://docs.sqlalchemy.org/en/latest/core/sqlelement.html#sqlalchemy.sql.expression.tuple_).
                If `False`, build the equivalent OR-of-ANDs clause instead:
                `WHERE (id1 == val1 AND id2 == val2) OR (id1 == val3 AND
                id2 == val4)`.
        """
        assert isinstance(self._pk_coerce, tuple)
        assert isinstance(self._pk_column, tuple)
        decoded_pks = tuple(iterdecode(pk) for pk in pks)
        if use_composite_in:
            return tuple_(*self._pk_column).in_(
                tuple(
                    (_coerce(_pk) if _coerce is not bool else _pk == "True")
                    for _coerce, _pk in zip(
                        self._pk_coerce,
                        decoded_pk,
                    )
                )
                for decoded_pk in decoded_pks
            )
        else:  # noqa: RET505, pragma: no cover
            clauses = []
            for decoded_pk in decoded_pks:
                clauses.append(
                    and_(
                        *(
                            (
                                _pk_col == _coerce(_pk)
                                if _coerce is not bool
                                # bool("False") is True, so compare the decoded string directly.
                                else (_pk_col == (_pk == "True"))
                            )
                            for _pk_col, _coerce, _pk in zip(
                                self._pk_column,
                                self._pk_coerce,
                                decoded_pk,
                            )
                        )
                    )
                )
            return or_(*clauses)

    def _refresh_attr_names(self, request: Request) -> list[str]:
        """Column attributes to reload after a create or edit flush."""
        return [
            field.name
            for field in self.get_fields_list(request)
            if field.name in self._columns
        ]

    async def create(self, request: Request, data: dict[str, Any]) -> Any:
        _log.debug("create %s: arranging and validating data", self.model.__name__)
        session: Session | AsyncSession = request.state.session
        try:
            data = await self._arrange_data(request, data)
            await self.validate(request, data)
            if isinstance(session, AsyncSession):
                async with session.begin_nested():
                    obj = await self._populate_obj(request, self.model(), data)
                    await self._emit_before_create(request, data, obj)
                    session.add(obj)
                    await session.flush()
                await session.refresh(obj, self._refresh_attr_names(request))
            else:
                with session.begin_nested():
                    obj = await self._populate_obj(request, self.model(), data)
                    await self._emit_before_create(request, data, obj)
                    session.add(obj)
                    await anyio.to_thread.run_sync(session.flush)
                await anyio.to_thread.run_sync(
                    session.refresh, obj, self._refresh_attr_names(request)
                )
            await self._emit_after_create(request, obj)
            on_commit(
                request,
                lambda: self._emit_after_create_committed(request, obj),
            )
            _log.info("Created %s", self.model.__name__)
            return obj
        except Exception as e:
            if isinstance(e, FormValidationError):
                _log.warning("create %s: validation failed: %s", self.model.__name__, e)
            else:
                _log.error(
                    "create %s: unexpected error: %s",
                    self.model.__name__,
                    e,
                    exc_info=True,
                )
            return await self.handle_exception(request, e)

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        _log.debug(
            "edit %s pk=%r: arranging and validating data", self.model.__name__, pk
        )
        session: Session | AsyncSession = request.state.session
        try:
            data = await self._arrange_data(request, data, True)
            await self.validate(request, data)
            obj = await self.find_by_pk(request, pk)
            old_data = {
                f.name: getattr(obj, f.name, None)
                for f in self.get_fields_list(request)
            }
            if isinstance(session, AsyncSession):
                async with session.begin_nested():
                    await self._populate_obj(request, obj, data, True)
                    await self._emit_before_edit(
                        request, data, obj, pk=pk, old_data=old_data
                    )
                    session.add(obj)
                    await session.flush()
                await session.refresh(obj, self._refresh_attr_names(request))
            else:
                with session.begin_nested():
                    await self._populate_obj(request, obj, data, True)
                    await self._emit_before_edit(
                        request, data, obj, pk=pk, old_data=old_data
                    )
                    session.add(obj)
                    await anyio.to_thread.run_sync(session.flush)
                await anyio.to_thread.run_sync(
                    session.refresh, obj, self._refresh_attr_names(request)
                )
            await self._emit_after_edit(request, obj, pk=pk, old_data=old_data)
            on_commit(
                request,
                lambda: self._emit_after_edit_committed(
                    request, obj, old_data=old_data
                ),
            )
            _log.info("Edited %s pk=%r", self.model.__name__, pk)
            return obj
        except Exception as e:
            if isinstance(e, FormValidationError):
                _log.warning(
                    "edit %s pk=%r: validation failed: %s", self.model.__name__, pk, e
                )
            else:
                _log.error(
                    "edit %s pk=%r: unexpected error: %s",
                    self.model.__name__,
                    pk,
                    e,
                    exc_info=True,
                )
            await self.handle_exception(request, e)

    async def _arrange_data(
        self,
        request: Request,
        data: dict[str, Any],
        is_edit: bool = False,
    ) -> dict[str, Any]:
        """Return a new dict with relation fields resolved to loaded model instances.

        For each `RelationField`, replaces the submitted primary key(s) with
        the corresponding related object(s) fetched from the database.
        """
        _log.debug("_arrange_data %s (is_edit=%s)", self.model.__name__, is_edit)
        arranged_data: dict[str, Any] = {}
        for field in self.get_fields_list(request):
            if field.read_only:
                continue
            if isinstance(field, RelationField) and data[field.name] is not None:
                foreign_view = self._find_foreign_view(field.key)  # type: ignore
                if isinstance(field, HasMany):
                    # `collection_class` also allows a zero-arg factory, but this
                    # call site only ever uses it as an iterable-accepting container type.
                    arranged_data[field.name] = field.collection_class(
                        await foreign_view.find_by_pks(  # ty: ignore[too-many-positional-arguments]
                            request, data[field.name]
                        )
                    )
                else:
                    arranged_data[field.name] = await foreign_view.find_by_pk(
                        request, data[field.name]
                    )
            else:
                arranged_data[field.name] = data[field.name]
        return arranged_data

    async def _populate_obj(
        self,
        request: Request,
        obj: Any,
        data: dict[str, Any],
        is_edit: bool = False,
    ) -> Any:
        for field in self.get_fields_list(request):
            if field.read_only:
                continue
            name, value = field.name, data.get(field.name)
            if isinstance(field, FileField) and field.storage is None:
                value, should_be_deleted = not_none(value)
                if should_be_deleted:
                    setattr(obj, name, None)
                elif (not field.multiple and value is not None) or (
                    field.multiple and isinstance(value, list) and len(value) > 0
                ):
                    setattr(obj, name, value)
            else:
                setattr(obj, name, value)
        return obj

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        _log.debug("delete %s: %d pk(s): %r", self.model.__name__, len(pks), pks)
        session: Session | AsyncSession = request.state.session
        objs = await self.find_by_pks(request, pks)
        try:
            if isinstance(session, AsyncSession):
                async with session.begin_nested():
                    for obj in objs:
                        await self._emit_before_delete(
                            request, await self.get_pk_value(request, obj), obj
                        )
                        await session.delete(obj)
                    await session.flush()
            else:

                def _delete_in_savepoint() -> None:
                    with session.begin_nested():
                        for obj in objs:
                            session.delete(obj)
                        session.flush()

                for obj in objs:
                    await self._emit_before_delete(
                        request, await self.get_pk_value(request, obj), obj
                    )
                await anyio.to_thread.run_sync(_delete_in_savepoint)
        except Exception as e:  # pragma: no cover
            _log.error(
                "delete %s: unexpected error: %s",
                self.model.__name__,
                e,
                exc_info=True,
            )
            raise

        def _make_after_delete_committed(obj: Any, pk: Any) -> Callable[[], Any]:
            return lambda: self._emit_after_delete_committed(request, pk, obj)

        for obj in objs:
            pk = await self.get_pk_value(request, obj)
            await self._emit_after_delete(request, pk, obj)
            # Detach so the committed hook can still read `obj`'s already-loaded
            # attributes later: once the row is gone, a session-attached instance
            # would try to re-SELECT expired attributes on commit and raise
            # ObjectDeletedError.
            session.expunge(obj)
            on_commit(request, _make_after_delete_committed(obj, pk))
        n = len(objs)
        _log.info("Deleted %d %s record(s)", n, self.model.__name__)
        return n

    async def build_full_text_search_query(
        self, request: Request, term: str, model: Any
    ) -> Any:
        return self.get_search_query(request, term)

    def build_order_clauses(
        self,
        request: Request,
        sorts: Sequence[tuple[str, str]],
        stmt: Select,
    ) -> Select:
        for sort_by, sort_dir in sorts:
            _log.debug("Ordering %s by %r %s", self.model.__name__, sort_by, sort_dir)
            model_attr = getattr(self.model, sort_by, None)
            if model_attr is not None and isinstance(
                model_attr.property, RelationshipProperty
            ):
                stmt = stmt.outerjoin(model_attr)
            sorting_attr = self.sortable_field_mapping.get(sort_by, model_attr)
            stmt = stmt.order_by(
                not_none(sorting_attr).desc() if sort_dir == "desc" else sorting_attr
            )
        return stmt

    async def get_pk_value(self, request: Request, obj: Any) -> Any:
        return await self.pk_field.parse_obj(request, obj)

    async def get_serialized_pk_value(self, request: Request, obj: Any) -> Any:
        value = await self.get_pk_value(request, obj)
        return await self.pk_field.serialize_value(request, value)

    async def handle_exception(self, request: Request, exc: Exception) -> None:
        try:
            # Convert a sqlalchemy_file validation error into a form error,
            # if sqlalchemy_file is installed.
            from sqlalchemy_file.exceptions import ValidationError

            if isinstance(exc, ValidationError):
                raise FormValidationError({exc.key: exc.msg})
        except ImportError:  # pragma: no cover
            pass
        raise exc  # pragma: no cover


class InlineModelView(BaseInlineModelView, ModelView):
    """Inline editing of SQLAlchemy-backed related records inside a parent form.

    Declare `model` as a class attribute. `fk_attr` is optional: when omitted,
    it is auto-detected from the SQLAlchemy relationship on the parent model
    (the relationship whose `mapper.class_` matches `model`).

    Set `fk_attr` explicitly only when auto-detection is ambiguous (multiple
    relationships to the same child model) or the relationship is missing:

    - Simple FK: `fk_attr = "article_id"`
    - Composite FK: `fk_attr = ("order_store_id", "order_seq")`

    Example (zero config, `fk_attr` inferred from `Article.comments`):

        ```python
        class CommentInline(InlineModelView):
            model = Comment
            fields = ["id", "author", "body"]
            extra = 2


        class ArticleView(ModelView):
            inlines = [CommentInline]
        ```
    """

    model: ClassVar[type]  # type: ignore[misc]

    def __init__(self, parent_view: BaseModelView | None = None) -> None:
        self.parent_view = parent_view
        ModelView.__init__(self, type(self).model)

    def _get_fk_attr(self) -> str | tuple[str, ...]:
        """Return the FK attr(s), auto-detecting from the parent relationship if not set."""
        if self.fk_attr:
            return self.fk_attr
        if not hasattr(self, "_auto_fk_attr"):
            self._auto_fk_attr: str | tuple[str, ...] = (
                self._detect_fk_from_parent_relationship()
            )
        return self._auto_fk_attr

    def _detect_fk_from_parent_relationship(self) -> str | tuple[str, ...]:
        """Inspect the parent model's relationships to find the child FK column(s)."""
        if self.parent_view is None:
            raise RuntimeError(
                "Cannot auto-detect fk_attr before the inline is wired to a parent view"
            )
        parent_mapper = inspect(self.parent_view.model)  # ty: ignore[unresolved-attribute]
        child_mapper: Any = inspect(self.model)
        for rel in parent_mapper.relationships:
            if rel.mapper.class_ is not self.model:
                continue
            # synchronize_pairs = [(parent_col, child_col), ...] in definition order
            fk_keys: list[str] = []
            for _, child_col in rel.synchronize_pairs:
                for prop in child_mapper.column_attrs:
                    if child_col in prop.columns:
                        fk_keys.append(prop.key)
                        break
            if len(fk_keys) == 1:
                _log.debug(
                    "%s: auto-detected fk_attr=%r from relationship to %s",
                    type(self).__name__,
                    fk_keys[0],
                    self.parent_view.model.__name__,  # ty: ignore[unresolved-attribute]
                )
                return fk_keys[0]
            if fk_keys:
                _log.debug(
                    "%s: auto-detected composite fk_attr=%r from relationship to %s",
                    type(self).__name__,
                    tuple(fk_keys),
                    self.parent_view.model.__name__,  # ty: ignore[unresolved-attribute]
                )
                return tuple(fk_keys)
        _log.error(
            "%s: cannot auto-detect fk_attr, no relationship from %s to %s",
            type(self).__name__,
            self.parent_view.model.__name__,  # ty: ignore[unresolved-attribute]
            self.model.__name__,
        )
        raise ValueError(
            f"{type(self).__name__}: cannot auto-detect fk_attr, "
            f"no relationship from {self.parent_view.model.__name__} to "  # ty: ignore[unresolved-attribute]
            f"{self.model.__name__} found. Set fk_attr explicitly."
        )

    def _build_fk_parent_map(self) -> dict[str, str]:
        """Return `{child_fk_attr: parent_attr}` for a composite FK.

        Uses the parent's already-computed `_pk_column` to scope the column
        lookup to PK columns only.
        """
        fk_attr = self._get_fk_attr()
        assert isinstance(fk_attr, tuple)
        child_mapper: Any = inspect(self.model)

        # Restrict parent_col_map to PK columns using parent_view._pk_column
        assert self.parent_view is not None
        parent_view: ModelView = self.parent_view  # ty: ignore[invalid-assignment]
        parent_pk_cols = (
            parent_view._pk_column
            if isinstance(parent_view._pk_column, tuple)
            else (parent_view._pk_column,)
        )
        parent_mapper = inspect(parent_view.model)
        pk_col_ids = {id(col) for ia in parent_pk_cols for col in ia.property.columns}
        parent_col_map: dict[int, str] = {
            id(col): prop.key
            for prop in parent_mapper.column_attrs
            for col in prop.columns
            if id(col) in pk_col_ids
        }

        result: dict[str, str] = {}
        for attr_name in fk_attr:
            child_col = child_mapper.attrs[attr_name].columns[0]
            for fk in child_col.foreign_keys:
                result[attr_name] = parent_col_map.get(id(fk.column), fk.column.name)
                break
        return result

    async def build_fk_value(self, request: Request, parent: Any) -> Any:
        """Return the FK value(s) for a new inline row.

        For a single FK, delegates to the parent's PK value (via `pk_field`).
        For a composite FK, returns a dict mapping child FK attr to parent
        value, resolved via SQLAlchemy FK constraint introspection.
        """
        if isinstance(self._get_fk_attr(), tuple):
            return {
                child_attr: getattr(parent, parent_attr)
                for child_attr, parent_attr in self._build_fk_parent_map().items()
            }
        return await super().build_fk_value(request, parent)

    async def _arrange_data(
        self,
        request: Request,
        data: dict[str, Any],
        is_edit: bool = False,
    ) -> dict[str, Any]:
        # ModelView._arrange_data only keeps declared fields; preserve the FK
        # column(s) so _populate_obj can set them on the new object.
        fk_attr = self._get_fk_attr()
        if isinstance(fk_attr, tuple):
            fk_snapshot = {attr: data.get(attr) for attr in fk_attr}
        else:
            fk_snapshot = {fk_attr: data.get(fk_attr)}
        arranged = await super()._arrange_data(request, data, is_edit)
        if not is_edit:
            for attr, val in fk_snapshot.items():
                if val is not None:
                    arranged[attr] = val
        return arranged

    async def _populate_obj(
        self,
        request: Request,
        obj: Any,
        data: dict[str, Any],
        is_edit: bool = False,
    ) -> Any:
        await super()._populate_obj(request, obj, data, is_edit)
        if not is_edit:
            fk_attr = self._get_fk_attr()
            if isinstance(fk_attr, tuple):
                for attr in fk_attr:
                    if attr in data:
                        setattr(obj, attr, data[attr])
            elif fk_attr in data:
                setattr(obj, fk_attr, data[fk_attr])
        return obj

    async def find_by_parent(self, request: Request, parent: Any) -> Sequence[Any]:
        _log.debug(
            "find_by_parent %s: parent type=%s",
            self.model.__name__,
            type(parent).__name__,
        )
        session: Session | AsyncSession = request.state.session
        fk_attr = self._get_fk_attr()
        stmt: Any
        if isinstance(fk_attr, tuple):
            clause = and_(
                *(
                    getattr(self.model, child_attr) == getattr(parent, parent_attr)
                    for child_attr, parent_attr in self._build_fk_parent_map().items()
                )
            )
            stmt = select(self.model).where(clause)
        else:
            assert self.parent_view is not None
            parent_pk = await self.parent_view.get_pk_value(request, parent)
            fk_col = getattr(self.model, fk_attr)
            stmt = select(self.model).where(fk_col == parent_pk)
        for field in self.get_fields_list(request):
            if isinstance(field, RelationField):
                stmt = stmt.options(joinedload(getattr(self.model, field.name)))
        if isinstance(session, AsyncSession):
            rows = (await session.execute(stmt)).scalars().unique().all()
        else:
            rows = (
                (await anyio.to_thread.run_sync(session.execute, stmt))
                .scalars()
                .unique()
                .all()
            )
        _log.debug("find_by_parent %s → %d row(s)", self.model.__name__, len(rows))
        return rows
