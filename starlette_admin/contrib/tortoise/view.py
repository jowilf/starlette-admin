from collections.abc import Sequence
from typing import Any, ClassVar

from starlette.requests import Request
from starlette_admin.contrib.tortoise.converters import (
    BaseTortoiseModelConverter,
    ModelConverter,
)
from starlette_admin.contrib.tortoise.exceptions import InvalidModelError
from starlette_admin.contrib.tortoise.filters import (
    TortoiseFilterRegistry,
    build_filter_query,
)
from starlette_admin.contrib.tortoise.helpers import (
    build_order_clauses,
    default_field_names,
    relation_source_field,
)
from starlette_admin.exceptions import FormValidationError
from starlette_admin.fields import (
    BaseField,
    ColorField,
    EmailField,
    FileField,
    HasMany,
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
    prettify_class_name,
    slugify_class_name,
)
from starlette_admin.logging import get_logger
from starlette_admin.views import BaseModelView
from starlette_admin.views import InlineModelView as BaseInlineModelView
from tortoise.exceptions import ValidationError
from tortoise.expressions import Q
from tortoise.models import Model
from tortoise.queryset import QuerySet

_log = get_logger(__name__)


class ModelView(BaseModelView):
    """A view for managing Tortoise ORM models."""

    def __init__(
        self,
        model: type[Model],
        icon: str | None = None,
        display_name: str | None = None,
        menu_label: str | None = None,
        key: str | None = None,
        converter: BaseTortoiseModelConverter | None = None,
    ):
        if not (isinstance(model, type) and issubclass(model, Model)):
            _log.error("Class %s is not a Tortoise ORM model", model.__name__)
            raise InvalidModelError(
                f"Class {model.__name__} is not a Tortoise ORM model."
            )
        self.model = model
        self._meta = model._meta
        self._ensure_relations_initialized()
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
        self.pk_attr = self._meta.pk_attr
        declared_fields: Sequence[Any] = (
            self.fields
            if self.fields is not None and len(self.fields) > 0
            else default_field_names(model)
        )
        self.fields = (converter or ModelConverter()).convert_fields_list(
            fields=declared_fields, model=model
        )
        try:
            # Reuse the already-converted field if the PK is declared.
            self.pk_field: BaseField = next(
                f for f in self.fields if f.name == self.pk_attr
            )
        except StopIteration:
            # The PK is not among the declared fields, so fall back to
            # treating its value as a plain string.
            self.pk_field = StringField(self.pk_attr)
        _default_list = [
            field.name
            for field in self.fields
            if not isinstance(field, (RelationField, FileField))
        ]
        if self.searchable_fields is None:
            self.searchable_fields = _default_list
        if self.sortable_fields is None:
            self.sortable_fields = _default_list
        super().__init__()
        _log.info(
            "ModelView for %s registered (key=%r, pk=%s, %d field(s))",
            self.model.__name__,
            self.key,
            self.pk_attr,
            len(self.fields),
        )

    def _ensure_relations_initialized(self) -> None:
        """Fail fast when the model's relations have not been resolved yet.

        Tortoise resolves relation targets (and creates backward relation
        fields) in `Tortoise.init()` / `Tortoise.init_models()`. Views are
        usually built at import time, before the async `Tortoise.init()` has
        run, so `Tortoise.init_models()` is the way to register models early.
        """
        meta = self._meta
        for name in meta.fk_fields | meta.o2o_fields | meta.m2m_fields:
            if meta.fields_map[name].related_model is None:  # ty: ignore[unresolved-attribute]
                raise InvalidModelError(
                    f"Relations of {self.model.__name__} are not initialized."
                    ' Call Tortoise.init_models(["path.to.models"], "models")'
                    " before creating admin views."
                )

    def get_list_query(self, request: Request) -> QuerySet:
        """Return the base `QuerySet` used by
        [find_all][starlette_admin.views.BaseModelView.find_all].

        Examples:
            ```python  hl_lines="3-4"
            class PostView(ModelView):

                    def get_list_query(self, request: Request):
                        return super().get_list_query(request).filter(published=True)
            ```

        If you override this method, also override
        [get_count_query][starlette_admin.contrib.tortoise.ModelView.get_count_query]
        so the list view displays the correct item count.
        """
        return self.model.all()

    def get_count_query(self, request: Request) -> QuerySet:
        """Return the base `QuerySet` used by
        [count][starlette_admin.views.BaseModelView.count].
        """
        return self.model.all()

    def get_detail_query(self, request: Request) -> QuerySet:
        """Return the base `QuerySet` used by
        [find_by_pk][starlette_admin.views.BaseModelView.find_by_pk] and
        [find_by_pks][starlette_admin.views.BaseModelView.find_by_pks].

        Defaults to [get_list_query][starlette_admin.contrib.tortoise.ModelView.get_list_query]
        so overrides of the latter also apply to the detail view.
        """
        return self.get_list_query(request)

    def get_search_query(self, request: Request, term: str) -> Q:
        """Return the ``Q`` expression used for full-text search: a
        case-insensitive `contains` match across the searchable string-like
        fields. Enum and relation fields are excluded because their raw
        filter values cannot be matched as substrings.
        """
        queries = [
            Q(**{f"{field.name}__icontains": term})
            for field in self.get_fields_list(request)
            if field.searchable
            and type(field)
            in [
                StringField,
                SlugField,
                TextAreaField,
                EmailField,
                URLField,
                PhoneField,
                ColorField,
            ]
        ]
        result = Q()
        for query in queries:
            result = result | query
        return result

    def get_filter_registry(self) -> FilterRegistry:
        """Return the [FilterRegistry][starlette_admin.filters.FilterRegistry]
        of concrete Tortoise filter implementations
        (`starlette_admin.contrib.tortoise.filters`) used to determine which
        filters are available for each field on this view's list page.
        """
        return TortoiseFilterRegistry()

    def _prefetch_names(self, request: Request) -> list[str]:
        """Relation names to prefetch so serialization never triggers lazy loads."""
        return [
            field.name
            for field in self.get_fields_list(request)
            if field.name in self._meta.fetch_fields
        ]

    def _coerce_pk(self, pk: Any) -> Any:
        """Coerce a raw primary key (usually a URL string) to its Python type.

        Returns `None` when the value cannot represent a valid key, so
        lookups with garbage input simply find nothing.
        """
        try:
            return self._meta.pk.to_python_value(pk)
        except (ValueError, TypeError):
            return None

    async def _apply_search_and_filters(
        self,
        request: Request,
        stmt: QuerySet,
        q: str | None,
        filters: FilterGroup | None,
    ) -> QuerySet:
        if q is not None:
            _log.debug("Applying full-text search q=%r to %s", q, self.model.__name__)
            stmt = stmt.filter(await self.build_full_text_search_query(request, q))
        if filters is not None and not filters.is_empty():
            _log.debug("Applying filter group to %s", self.model.__name__)
            fields_by_name = {f.name: f for f in self.get_fields_list(request)}
            query = build_filter_query(
                filters, fields_by_name, self.get_filter_registry(), self, request
            )
            if query is not None:
                stmt = stmt.filter(query)
        return stmt

    async def build_full_text_search_query(self, request: Request, term: str) -> Q:
        return self.get_search_query(request, term)

    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        stmt = await self._apply_search_and_filters(
            request, self.get_count_query(request), q, filters
        )
        n = await stmt.count()
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
        stmt = await self._apply_search_and_filters(
            request, self.get_list_query(request), q, filters
        )
        if sorts:
            stmt = stmt.order_by(*build_order_clauses(self.model, sorts))
        if skip > 0:
            stmt = stmt.offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        return await stmt.prefetch_related(*self._prefetch_names(request))

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        pk = self._coerce_pk(pk)
        if pk is None:
            return None
        stmt = self.get_detail_query(request).filter(**{not_none(self.pk_attr): pk})
        return await stmt.prefetch_related(*self._prefetch_names(request)).first()

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        coerced = [value for value in map(self._coerce_pk, pks) if value is not None]
        stmt = self.get_detail_query(request).filter(**{f"{self.pk_attr}__in": coerced})
        return await stmt.prefetch_related(*self._prefetch_names(request))

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
        arranged_data: dict[str, Any] = {}
        for field in self.get_fields_list(request):
            if field.read_only:
                continue
            if isinstance(field, RelationField) and data.get(field.name) is not None:
                foreign_view = self._find_foreign_view(not_none(field.key))
                if isinstance(field, HasMany):
                    arranged_data[field.name] = list(
                        await foreign_view.find_by_pks(request, data[field.name])
                    )
                else:
                    arranged_data[field.name] = await foreign_view.find_by_pk(
                        request, data[field.name]
                    )
            else:
                arranged_data[field.name] = data.get(field.name)
        return arranged_data

    async def _populate_obj(
        self,
        request: Request,
        obj: Model,
        data: dict[str, Any],
        is_edit: bool = False,
    ) -> dict[str, list[Any]]:
        """Set submitted values on `obj` and return the pending many-to-many
        values, which can only be written after the object has been saved.
        """
        m2m_values: dict[str, list[Any]] = {}
        for field in self.get_fields_list(request):
            if field.read_only:
                continue
            name, value = field.name, data.get(field.name)
            if isinstance(field, HasMany):
                m2m_values[name] = value or []
            else:
                setattr(obj, name, value)
        return m2m_values

    async def _sync_m2m(
        self, obj: Model, m2m_values: dict[str, list[Any]], clear: bool = False
    ) -> None:
        """Write pending many-to-many values through their relation managers."""
        for name, items in m2m_values.items():
            manager = getattr(obj, name)
            if clear:
                await manager.clear()
            if items:
                await manager.add(*items)

    async def create(self, request: Request, data: dict[str, Any]) -> Any:
        try:
            data = await self._arrange_data(request, data)
            await self.validate(request, data)
            obj = self.model()
            m2m_values = await self._populate_obj(request, obj, data)
            await self._emit_before_create(request, data, obj)
            await obj.save()
            await self._sync_m2m(obj, m2m_values)
            await self._emit_after_create(request, obj)
            _log.info("Created %s", self.model.__name__)
            return obj
        except Exception as e:
            return await self.handle_exception(request, e)

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        try:
            data = await self._arrange_data(request, data, True)
            await self.validate(request, data)
            obj = await self.find_by_pk(request, pk)
            assert obj is not None, "Object not found"
            old_data = {
                f.name: getattr(obj, f.name, None)
                for f in self.get_fields_list(request)
            }
            m2m_values = await self._populate_obj(request, obj, data, True)
            await self._emit_before_edit(request, data, obj, pk=pk, old_data=old_data)
            await obj.save()
            await self._sync_m2m(obj, m2m_values, clear=True)
            await self._emit_after_edit(request, obj, pk=pk, old_data=old_data)
            _log.info("Edited %s pk=%r", self.model.__name__, pk)
            return obj
        except Exception as e:
            return await self.handle_exception(request, e)

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        cnt = 0
        for pk in pks:
            obj = await self.find_by_pk(request, pk)
            if obj is not None:
                await self._emit_before_delete(request, pk, obj)
                await obj.delete()
                await self._emit_after_delete(request, pk, obj)
                cnt += 1
        _log.info("Deleted %d %s record(s)", cnt, self.model.__name__)
        return cnt

    async def get_pk_value(self, request: Request, obj: Any) -> Any:
        return getattr(obj, not_none(self.pk_attr))

    async def get_serialized_pk_value(self, request: Request, obj: Any) -> Any:
        value = await self.get_pk_value(request, obj)
        return await self.pk_field.serialize_value(request, value)

    async def handle_exception(self, request: Request, exc: Exception) -> None:
        """Translate a Tortoise `ValidationError` into a `FormValidationError`
        so the offending field is highlighted on the form.

        Tortoise formats validation messages as `"<field>: <detail>"`; the
        error is attached to that field when it exists on the model.
        """
        if isinstance(exc, ValidationError):
            field_name, sep, detail = str(exc).partition(":")
            if sep and field_name.strip() in self._meta.fields_map:
                raise FormValidationError({field_name.strip(): detail.strip()}) from exc
        raise exc


class InlineModelView(BaseInlineModelView, ModelView):
    """Inline editing of Tortoise-backed related records inside a parent form.

    Declare ``model`` as a class attribute. The FK is either set explicitly
    via ``fk_attr`` (the relation name or its raw key column) or auto-detected
    by scanning the child model's to-one relations for one pointing at the
    parent model. Either way it is normalized to the raw key column
    (`article_id` for a relation named `article`), so new rows are linked by
    assigning the parent's primary key directly.

    Example:
        ```python
        class CommentInline(InlineModelView):
            model = Comment
            # fk_attr auto-detected: Comment has exactly one FK to Article
            fields = ["id", "author", "body"]
            extra = 2

        class ArticleView(ModelView):
            inlines = [CommentInline]
        ```
    """

    model: ClassVar[type[Model]]  # type: ignore[misc]

    def __init__(self, parent_view: BaseModelView | None = None) -> None:
        self.parent_view = parent_view
        ModelView.__init__(self, type(self).model)
        if self.fk_attr:
            self.fk_attr = self._normalize_fk_attr(str(self.fk_attr))
        else:
            self.fk_attr = self._detect_fk_attr()

    def _normalize_fk_attr(self, fk_attr: str) -> str:
        """Resolve a user-supplied `fk_attr` to the raw key column name."""
        meta = self.model._meta
        if fk_attr in meta.fk_fields | meta.o2o_fields:
            return relation_source_field(self.model, fk_attr)
        if fk_attr in meta.fields_map:
            return fk_attr
        raise ValueError(
            f"{type(self).__name__}: fk_attr {fk_attr!r} is not a field of "
            f"{self.model.__name__}."
        )

    def _detect_fk_attr(self) -> str:
        """Scan the child model's to-one relations for one pointing at the parent model."""
        parent_model = getattr(self.parent_view, "model", None)
        if parent_model is None:
            raise ValueError(
                f"cannot auto-detect fk_attr for {type(self).__name__}: "
                "parent_view has no 'model' attribute. Set fk_attr explicitly."
            )
        meta = self.model._meta
        candidates = [
            name
            for name in meta.fk_fields | meta.o2o_fields
            if meta.fields_map[name].related_model is parent_model  # ty: ignore[unresolved-attribute]
        ]
        if len(candidates) == 1:
            source = relation_source_field(self.model, candidates[0])
            _log.debug(
                "%s: auto-detected fk_attr=%r (relation %r)",
                type(self).__name__,
                source,
                candidates[0],
            )
            return source
        if not candidates:
            raise ValueError(
                f"cannot auto-detect fk_attr for {type(self).__name__}: "
                f"{self.model.__name__} has no relation pointing to "
                f"{parent_model.__name__}. Set fk_attr explicitly."
            )
        raise ValueError(
            f"cannot auto-detect fk_attr for {type(self).__name__}: "
            f"{self.model.__name__} has multiple relations to "
            f"{parent_model.__name__}: {sorted(candidates)}. Set fk_attr explicitly."
        )

    async def find_by_parent(self, request: Request, parent: Any) -> Sequence[Any]:
        parent_pk = await not_none(self.parent_view).get_pk_value(request, parent)
        stmt = self.model.filter(**{str(self.fk_attr): parent_pk})
        return await stmt.prefetch_related(*self._prefetch_names(request))

    async def _arrange_data(
        self,
        request: Request,
        data: dict[str, Any],
        is_edit: bool = False,
    ) -> dict[str, Any]:
        # ModelView._arrange_data only keeps declared fields; preserve the FK
        # column so _populate_obj can link the new row to its parent.
        fk_attr = str(self._get_fk_attr())
        fk_value = data.get(fk_attr)
        arranged = await super()._arrange_data(request, data, is_edit)
        if not is_edit and fk_value is not None:
            arranged[fk_attr] = fk_value
        return arranged

    async def _populate_obj(
        self,
        request: Request,
        obj: Model,
        data: dict[str, Any],
        is_edit: bool = False,
    ) -> dict[str, list[Any]]:
        m2m_values = await super()._populate_obj(request, obj, data, is_edit)
        fk_attr = str(self._get_fk_attr())
        if not is_edit and fk_attr in data:
            setattr(obj, fk_attr, data[fk_attr])
        return m2m_values
