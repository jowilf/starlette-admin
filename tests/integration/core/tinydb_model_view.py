"""TinyDB-backed base model and view for core integration tests.

Mirrors examples/custom-backend exactly: Pydantic model layer on top of a
TinyDB(MemoryStorage) store, with full CRUD, full-text search, and real
FilterGroup support via TinyDB query fragments (same pattern as
examples/custom-backend/filters.py). Replaces tests/dummy_model_view.py.

Each concrete subclass of TinydbModelView that declares a ``model`` attribute
in its own ``__dict__`` gets a fresh in-memory TinyDB instance via
``__init_subclass__``. Subclasses that *don't* redeclare ``model`` (e.g., a
small override class defined inside a test function) inherit the parent _db,
so data seeded before the test remains visible.
"""

import re
from collections.abc import Sequence
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict
from starlette.requests import Request
from starlette_admin import (
    HasMany,
    HasOne,
    IntegerField,
    ListField,
    StringField,
    TextAreaField,
)
from starlette_admin.fields import BaseField
from starlette_admin.filters import (
    FilterApplyContext,
    FilterGroup,
    FilterRegistry,
    FilterRule,
)
from starlette_admin.filters.generic import (
    EqualFilter,
    IsNotNullFilter,
    IsNullFilter,
    NotEqualFilter,
)
from starlette_admin.filters.string import (
    ContainsFilter,
    EndsWithFilter,
    NotContainsFilter,
    StartsWithFilter,
)
from starlette_admin.helpers import prettify_class_name, slugify_class_name
from starlette_admin.views import BaseModelView, InlineModelView
from tinydb import Query, TinyDB
from tinydb.queries import QueryInstance
from tinydb.storages import MemoryStorage

# ── TinyDB filter implementations ────────────────────────────────────────────


def _field(ctx: FilterApplyContext) -> Query:
    return Query()[ctx.field_name]


class TinyDBEqualFilter(EqualFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx) == ctx.value


class TinyDBNotEqualFilter(NotEqualFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx) != ctx.value


class TinyDBIsNullFilter(IsNullFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx).test(lambda v: not v)


class TinyDBIsNotNullFilter(IsNotNullFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx).test(bool)


class TinyDBContainsFilter(ContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx).search(re.escape(ctx.value), flags=re.IGNORECASE)


class TinyDBNotContainsFilter(NotContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return ~_field(ctx).search(re.escape(ctx.value), flags=re.IGNORECASE)


class TinyDBStartsWithFilter(StartsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx).matches(f"{re.escape(ctx.value)}.*", flags=re.IGNORECASE)


class TinyDBEndsWithFilter(EndsWithFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return _field(ctx).matches(f".*{re.escape(ctx.value)}", flags=re.IGNORECASE)


# ── Default filter registry (mirrors examples/custom-backend/filters.py) ─────

#: IntegerField gets no filters: id is stored as the TinyDB doc_id and is
#: never visible to Query conditions (same constraint as the custom-backend).
_default_filter_registry = FilterRegistry()
_default_filter_registry.register(IntegerField)
_default_filter_registry.register(
    StringField,
    TinyDBContainsFilter,
    TinyDBNotContainsFilter,
    TinyDBStartsWithFilter,
    TinyDBEndsWithFilter,
    TinyDBEqualFilter,
    TinyDBNotEqualFilter,
)
_default_filter_registry.register(
    TextAreaField,
    TinyDBContainsFilter,
    TinyDBNotContainsFilter,
    TinyDBStartsWithFilter,
    TinyDBEndsWithFilter,
)
_default_filter_registry.register(ListField, TinyDBIsNullFilter, TinyDBIsNotNullFilter)


def _build_filter_query(
    group: FilterGroup,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    """Recursively turn a FilterGroup tree into a TinyDB QueryInstance."""
    fragments = []
    for rule in group.rules:
        if isinstance(rule, FilterGroup):
            frag = _build_filter_query(rule, fields_by_name, registry)
        else:
            assert isinstance(rule, FilterRule)
            filter_cls = registry.get_filter(fields_by_name[rule.field], rule.filter)
            if filter_cls is None:
                continue
            ctx = FilterApplyContext(
                query=None,
                field_name=rule.field,
                value=rule.value,
                value2=rule.value2,
            )
            frag = filter_cls().apply(ctx)
        if frag is not None:
            fragments.append(frag)

    if not fragments:
        return None
    combined = fragments[0]
    for frag in fragments[1:]:
        combined = (combined | frag) if group.logic == "or" else (combined & frag)
    return combined


# ── Pydantic model base ───────────────────────────────────────────────────────


class TinydbBaseModel(BaseModel):
    """Pydantic model base for TinyDB-backed test views.

    ``id`` maps to the TinyDB ``doc_id`` and is excluded from stored
    documents; it is reconstructed from the document on read.
    """

    id: int | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_tinydb_doc(self) -> dict:
        """Serialise to a dict suitable for TinyDB (id excluded)."""
        return self.model_dump(exclude={"id"})

    @classmethod
    def from_tinydb_doc(cls, doc: Any) -> "TinydbBaseModel":
        """Reconstruct from a TinyDB Document."""
        return cls.model_validate({**dict(doc), "id": doc.doc_id})


# ── View base ────────────────────────────────────────────────────────────────


class TinydbModelView(BaseModelView):
    """BaseModelView backed by an in-memory TinyDB instance.

    Pass the model class as the first argument to ``__init__``, mirroring the
    SQLAlchemy ``ModelView`` constructor.  Every concrete subclass automatically
    gets its own fresh TinyDB(MemoryStorage) at class-definition time so that
    class-level helpers (``_db``, ``_get``, ``_len``, ``_all_pks``) are usable
    in autouse fixtures before any instance is created.

    Usage in tests::

        class ArticleView(TinydbModelView):
            fields = [IntegerField("id"), ...]

        article_view = ArticleView(Article)
        admin.add_view(article_view)

        # In fixture / setup_method:
        ArticleView._db.truncate()
        ArticleView._db.insert(Article(status=Status.Draft).to_tinydb_doc())

        # In assertions:
        assert ArticleView._get(1).status == Status.Published
        assert ArticleView._len() == 3
        assert ArticleView._all_pks() == [1, 2, 3]
    """

    pk_attr: ClassVar[str] = "id"
    _db: ClassVar[TinyDB]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Create a fresh _db for:
        #   (a) direct subclasses of TinydbModelView (the root concrete views)
        #   (b) classes that declare `model` in their own __dict__ (inline views)
        # Override helpers (e.g., PostViewWithRestrictedTitle(PostView)) do NOT fall
        # into either category and therefore inherit the parent class's _db.
        if TinydbModelView in cls.__bases__ or "model" in cls.__dict__:
            cls._db = TinyDB(storage=MemoryStorage)

    def __init__(
        self,
        model: type[TinydbBaseModel],
        icon: str | None = None,
        display_name: str | None = None,
        menu_label: str | None = None,
        key: str | None = None,
    ) -> None:
        self.model = model
        type(
            self
        ).model = model  # keep class-level reference for classmethods (_get etc.)
        self.icon = icon
        self.key = key or self.key or slugify_class_name(model.__name__)
        self.menu_label = (
            menu_label or self.menu_label or prettify_class_name(model.__name__) + "s"
        )
        self.display_name = (
            display_name or self.display_name or prettify_class_name(model.__name__)
        )
        super().__init__()

    # ── test helpers ────────────────────────────────────────────────────────

    @classmethod
    def _get(cls, pk: int) -> Any | None:
        """Synchronous PK lookup (for test assertions only)."""
        doc = cls._db.get(doc_id=pk)
        return cls.model.from_tinydb_doc(doc) if doc else None

    @classmethod
    def _len(cls) -> int:
        """Record count (for test assertions only)."""
        return len(cls._db)

    @classmethod
    def _all_pks(cls) -> list[int]:
        """Sorted doc_id list (for test assertions only)."""
        return sorted(doc.doc_id for doc in cls._db.all())

    # ── filter support ───────────────────────────────────────────────────────

    def get_filter_registry(self) -> FilterRegistry:
        return _default_filter_registry

    async def _build_query(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> QueryInstance | None:
        """Combine full-text q and FilterGroup tree into one TinyDB query."""
        query = None
        if q is not None:
            q_lower = q.lower()
            sq = None
            for field_name in self.searchable_fields or []:
                frag = Query()[field_name].test(
                    lambda v, t=q_lower: v is not None and t in str(v).lower()
                )
                sq = frag if sq is None else (sq | frag)
            if sq is not None:
                query = sq
        if filters is not None and not filters.is_empty():
            fields_by_name = {f.name: f for f in self.get_fields_list(request)}
            fq = _build_filter_query(
                filters, fields_by_name, self.get_filter_registry()
            )
            if fq is not None:
                query = fq if query is None else (query & fq)
        return query

    # ── internal helpers ─────────────────────────────────────────────────────

    async def _arrange(self, request: Request, data: dict) -> dict:
        """Resolve HasOne/HasMany PKs to model instances."""
        for field in self.fields:
            if isinstance(field, HasOne) and data.get(field.name) is not None:
                data[field.name] = await self._find_foreign_view(field.key).find_by_pk(
                    request, int(data[field.name])
                )
            elif isinstance(field, HasMany) and data.get(field.name) is not None:
                data[field.name] = await self._find_foreign_view(field.key).find_by_pks(
                    request, list(map(int, data[field.name]))
                )
        return data

    # ── BaseModelView contract ───────────────────────────────────────────────

    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        tq = await self._build_query(request, q, filters)
        if tq is not None:
            return len(type(self)._db.search(tq))
        return len(type(self)._db)

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        sorts: list[tuple[str, str]] | None = None,
        filters: FilterGroup | None = None,
    ) -> Sequence[Any]:
        tq = await self._build_query(request, q, filters)
        raw = type(self)._db.search(tq) if tq is not None else type(self)._db.all()
        values = [self.model.from_tinydb_doc(d) for d in raw]
        # Apply multi-sort: iterate in reverse so earlier sorts have higher priority
        for sort_by, sort_dir in reversed(sorts or []):
            values.sort(
                key=lambda v, s=sort_by: (getattr(v, s) is None, getattr(v, s)),
                reverse=(sort_dir == "desc"),
            )
        if limit > 0:
            return values[skip : skip + limit]
        return values[skip:]

    async def find_by_pk(self, request: Request, pk: Any) -> Any | None:
        doc = type(self)._db.get(doc_id=int(pk))
        return self.model.from_tinydb_doc(doc) if doc else None

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        return [
            self.model.from_tinydb_doc(type(self)._db.get(doc_id=int(pk))) for pk in pks
        ]

    async def validate_data(self, data: dict) -> None:
        """Override in subclasses to raise FormValidationError on bad input."""

    async def create(self, request: Request, data: dict) -> Any:
        data = await self._arrange(request, data)
        await self.validate_data(data)
        clean = {k: v for k, v in data.items() if v is not None}
        obj = self.model.model_validate({"id": None, **clean})
        await self._emit_before_create(request, data, obj)
        doc_id = type(self)._db.insert(obj.to_tinydb_doc())
        obj = self.model.from_tinydb_doc(type(self)._db.get(doc_id=doc_id))
        await self._emit_after_create(request, obj)
        return obj

    async def edit(self, request: Request, pk: Any, data: dict) -> Any:
        pk = int(pk)
        data = await self._arrange(request, data)
        await self.validate_data(data)
        existing = type(self)._db.get(doc_id=pk)
        base = dict(existing) if existing else {}
        merged = {**base, **dict(data.items())}
        obj = self.model.model_validate({"id": pk, **merged})
        await self._emit_before_edit(request, data, obj, pk=pk, old_data=base)
        type(self)._db.update(obj.to_tinydb_doc(), doc_ids=[pk])
        obj = self.model.from_tinydb_doc(type(self)._db.get(doc_id=pk))
        await self._emit_after_edit(request, obj, pk=pk, old_data=base)
        return obj

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        ids = list(map(int, pks))
        objs = [
            self.model.from_tinydb_doc(type(self)._db.get(doc_id=i))
            for i in ids
            if type(self)._db.get(doc_id=i) is not None
        ]
        for obj in objs:
            await self._emit_before_delete(
                request, await self.get_pk_value(request, obj), obj
            )
        removed = type(self)._db.remove(doc_ids=ids)
        for obj in objs:
            await self._emit_after_delete(
                request, await self.get_pk_value(request, obj), obj
            )
        return len(removed)


class TinydbInlineModelView(TinydbModelView, InlineModelView):
    """TinyDB-backed inline view for integration tests.

    Declare ``model`` as a class attribute (same pattern as the SQLAlchemy
    ``InlineModelView``).  The constructor reads it from the class and passes
    it to ``TinydbModelView.__init__``.

    Usage::

        class CommentInline(TinydbInlineModelView):
            model = Comment
            fk_attr = "article_id"
            fields = [IntegerField("id"), StringField("body")]
    """

    model: ClassVar[type[TinydbBaseModel]]  # type: ignore[misc]

    def __init__(self, parent_view: BaseModelView | None = None) -> None:
        self.parent_view = parent_view
        TinydbModelView.__init__(self, type(self).model)

    async def find_by_parent(self, request: Request, parent: Any) -> Sequence[Any]:
        if self.parent_view is None:
            raise RuntimeError(
                "TinydbInlineModelView.find_by_parent called before wiring "
                "to a parent view"
            )
        parent_pk = await self.parent_view.get_pk_value(request, parent)
        rows = type(self)._db.search(Query()[self.fk_attr] == parent_pk)
        return [self.model.from_tinydb_doc(d) for d in rows]
