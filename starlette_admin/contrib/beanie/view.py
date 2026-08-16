import functools
import types as _types
from collections.abc import Iterable, Sequence
from typing import (
    Any,
    ClassVar,
    Generic,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

import bson.errors
import starlette_admin.fields as sa
from beanie import Document, Link, PydanticObjectId
from beanie.odm.operators.find import BaseFindOperator
from beanie.operators import In, Or, RegEx, Text
from pydantic import ValidationError
from starlette.requests import Request
from starlette_admin.contrib.beanie.converters import BeanieModelConverter
from starlette_admin.contrib.beanie.filters import (
    BeanieFilterRegistry,
    build_filter_query,
)
from starlette_admin.contrib.beanie.helpers import (
    BeanieLogicalOperator,
    build_order_clauses,
    is_link_type,
    is_list_of_links_type,
    normalize_field_list,
)
from starlette_admin.filters import FilterGroup, FilterRegistry
from starlette_admin.helpers import (
    not_none,
    prettify_class_name,
    pydantic_error_to_form_validation_errors,
    slugify_class_name,
)
from starlette_admin.logging import get_logger
from starlette_admin.views import BaseModelView
from starlette_admin.views import InlineModelView as BaseInlineModelView

_log = get_logger(__name__)

T = TypeVar("T", bound=Document)


class ModelView(BaseModelView, Generic[T]):
    """A view for managing Beanie documents."""

    full_text_override_order_by: bool = False
    """When `True`, list-page results matched through a MongoDB `$text` index
    are sorted by relevance score instead of the view's configured sort. Has
    no effect for the regex-based fallback used when the collection has no
    text index.
    """

    def __init__(
        self,
        document: type[T],
        icon: str | None = None,
        display_name: str | None = None,
        menu_label: str | None = None,
        key: str | None = None,
        converter: BeanieModelConverter | None = None,
    ):
        self.document = document
        self.key = key or self.key or slugify_class_name(self.document.__name__)
        self.menu_label = (
            menu_label
            or self.menu_label
            or prettify_class_name(self.document.__name__) + "s"
        )
        self.display_name = (
            display_name
            or self.display_name
            or prettify_class_name(self.document.__name__)
        )
        self.icon = icon or self.icon
        self.pk_attr = "id"
        self.has_full_text_index: bool | None = None

        self.fields_pydantic = list(document.model_fields.items())

        self.exclude_fields_from_create = [
            *self.exclude_fields_from_create,
            "revision_id",
        ]
        self.exclude_fields_from_edit = [
            *self.exclude_fields_from_edit,
            "revision_id",
            self.pk_attr,
        ]
        self.exclude_fields_from_list = [*self.exclude_fields_from_list, "revision_id"]
        self.exclude_fields_from_detail = [
            *self.exclude_fields_from_detail,
            "revision_id",
        ]

        self.exclude_fields_from_create = normalize_field_list(
            field_list=self.exclude_fields_from_create
        )
        self.exclude_fields_from_edit = normalize_field_list(
            field_list=self.exclude_fields_from_edit
        )
        self.exclude_fields_from_list = normalize_field_list(
            field_list=self.exclude_fields_from_list
        )
        self.exclude_fields_from_detail = normalize_field_list(
            field_list=self.exclude_fields_from_detail
        )
        self.exclude_fields_from_export = normalize_field_list(
            field_list=self.exclude_fields_from_export
        )
        self.exclude_fields_from_import = normalize_field_list(
            field_list=self.exclude_fields_from_import
        )

        if self.searchable_fields is not None:
            self.searchable_fields = normalize_field_list(list(self.searchable_fields))
        if self.sortable_fields is not None:
            self.sortable_fields = normalize_field_list(list(self.sortable_fields))
        if self.fields_default_sort is not None:
            self.fields_default_sort = normalize_field_list(
                list(self.fields_default_sort), is_default_sort_list=True
            )

        if self.fields is None or len(self.fields) == 0:
            self.fields = document.model_fields.keys()

        self.fields = list(
            (converter or BeanieModelConverter()).convert_fields_list(
                fields=self.fields, model=self.document
            )
        )

        super().__init__()

    async def check_full_text_index(self) -> None:
        """Detect whether the document's collection has a MongoDB text index.

        Sets `has_full_text_index` accordingly. `build_full_text_search_query`
        calls this once and reuses the cached result for later searches.
        """
        indexes = await self.document.get_pymongo_collection().index_information()
        for index in indexes.values():
            if any(field_type == "text" for _, field_type in index["key"]):
                self.has_full_text_index = True
                return
        self.has_full_text_index = False

    def get_filter_registry(self) -> FilterRegistry:
        """Return the [FilterRegistry][starlette_admin.filters.FilterRegistry]
        of concrete Beanie filter implementations
        (`starlette_admin.contrib.beanie.filters`) used to determine which
        filters are available for each field on this view's list page.
        """
        return BeanieFilterRegistry()

    async def _build_query(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> tuple[dict, bool]:
        """Build the MongoDB query dict used by `count` and `find_all`.

        Combines the full-text search query for `q` (if given) with the
        filter query built from `filters` (if given), ANDing the two
        together when both are present.

        Returns:
            A tuple of the combined query dict and whether it's a MongoDB
            `$text` query (see `build_full_text_search_query`).
        """
        text_query: dict = {}
        is_full_text = False

        if q is not None:
            operator, is_full_text = await self.build_full_text_search_query(request, q)
            text_query = dict(operator.query)

        filter_query: dict = {}
        if filters and not filters.is_empty():
            registry = self.get_filter_registry()
            fields_by_name = {f.name: f for f in self.get_fields_list(request)}
            fq = build_filter_query(filters, fields_by_name, registry, self, request)
            if fq:
                filter_query = fq

        if text_query and filter_query:
            return {"$and": [text_query, filter_query]}, is_full_text
        if filter_query:
            return filter_query, False
        if text_query:
            return text_query, is_full_text
        return {}, False

    async def build_full_text_search_query(
        self, request: Request, term: str
    ) -> tuple[BaseFindOperator, bool]:
        """Build the Beanie find operator used for the list page's search box.

        Uses the collection's MongoDB text index when one exists. Otherwise,
        falls back to a case-insensitive regex `OR` across the searchable
        string-like fields (`StringField`, `TextAreaField`, `EmailField`,
        `URLField`, `PhoneField`, `ColorField`), excluding `id`.

        Returns:
            A tuple of the find operator to pass to `Document.find` and
            whether it's a MongoDB `$text` query (`True`) or a regex-based
            query (`False`).
        """
        if self.has_full_text_index is None:
            await self.check_full_text_index()
        if self.has_full_text_index:
            return (
                Text(term, case_sensitive=False),
                True,
            )
        queries: list[BaseFindOperator] = []
        for field in self.get_fields_list(request):
            if (
                field.searchable
                and field.name != "id"
                and type(field)
                in [
                    sa.StringField,
                    sa.TextAreaField,
                    sa.EmailField,
                    sa.URLField,
                    sa.PhoneField,
                    sa.ColorField,
                ]
            ):
                queries.append(RegEx(field.name, term, options="i"))
        if queries:
            return (
                functools.reduce(Or, queries),
                False,
            )
        return BeanieLogicalOperator(), False

    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        query, _ = await self._build_query(request, q, filters)
        if not query:
            return (
                await self.document.get_pymongo_collection().estimated_document_count()
            )
        result = self.document.find(query)
        return await result.count()

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        sorts: Sequence[tuple[str, str]] | None = None,
        filters: FilterGroup | None = None,
    ) -> list[T]:
        query, is_full_text_query = await self._build_query(request, q, filters)
        result = self.document.find(query, fetch_links=True, nesting_depth=1)

        if is_full_text_query and self.full_text_override_order_by:
            result = result.sort(("score", {"$meta": "textScore"}))
        elif sorts:
            result = result.sort(build_order_clauses(sorts))
        result = result.skip(skip)
        if limit > 0:
            result = result.limit(limit)
        return await result.to_list()

    async def find_by_pk(self, request: Request, pk: PydanticObjectId) -> T | None:
        if not isinstance(pk, PydanticObjectId):
            try:
                pk = PydanticObjectId(pk)
            except bson.errors.InvalidId:
                return None

        return await self.document.get(pk, fetch_links=True, nesting_depth=1)

    async def find_by_pks(
        self, request: Request, pks: Iterable[PydanticObjectId]
    ) -> list[T]:
        object_ids = [PydanticObjectId(pk) for pk in pks]
        return await self.document.find(
            In(self.document.id, object_ids), fetch_links=True, nesting_depth=1
        ).to_list()

    async def get_pk_value(self, request: Request, obj: Any) -> Any:
        if isinstance(obj, Link):
            return getattr(obj.ref, not_none(self.pk_attr))

        return getattr(obj, not_none(self.pk_attr))

    async def get_serialized_pk_value(self, request: Request, obj: Any) -> Any:
        return str(await self.get_pk_value(request, obj))

    async def create(self, request: Request, data: dict) -> Any:
        try:
            await self.validate(request, data)
            doc = self.document(**data)
            await self._emit_before_create(request, data, doc)
            doc = await doc.create()
            await self._emit_after_create(request, doc)
            return doc
        except Exception as e:
            await self.handle_exception(request, e)

    async def edit(self, request: Request, pk: PydanticObjectId, data: dict) -> Any:
        doc: Document | None = await self.document.get(pk)
        assert doc is not None, "Document not found"
        try:
            await self.validate(request, data)
            for key, value in data.items():
                if key in self.document.model_fields:
                    field_type = self.document.model_fields[key].annotation
                    coerced: Any
                    if is_link_type(field_type):
                        coerced = (
                            value
                            if isinstance(value, PydanticObjectId)
                            else (None if not value else PydanticObjectId(value))
                        )
                    elif is_list_of_links_type(field_type):
                        coerced = [PydanticObjectId(item) for item in value if item]
                    else:
                        coerced = value

                    setattr(doc, key, coerced)

            # Re-validate the whole document: setattr() bypasses the
            # validation pydantic normally runs at construction time.
            validated_doc: T = self.document.model_validate(doc.model_dump())

            await self._emit_before_edit(request, data=data, obj=validated_doc, pk=pk)
            updated_doc = await validated_doc.replace()
            await self._emit_after_edit(request, updated_doc, pk=pk)

            return updated_doc

        except Exception as e:
            await self.handle_exception(request, e)

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        cnt = 0
        for pk in pks:
            value = await self.find_by_pk(request, pk)
            if value is not None:
                await self._emit_before_delete(request, pk, value)
                await value.delete()
                await self._emit_after_delete(request, pk, value)
                cnt += 1
        return cnt

    async def handle_exception(self, request: Request, exc: Exception) -> None:
        if isinstance(exc, ValidationError):
            raise pydantic_error_to_form_validation_errors(exc) from exc
        raise exc


def _get_link_target(ann: type) -> type | None:
    """Extract T from Link[T] or Optional[Link[T]]."""
    if get_origin(ann) is Link:
        args = get_args(ann)
        return args[0] if args else None
    if get_origin(ann) is Union or isinstance(ann, _types.UnionType):
        for arg in get_args(ann):
            if get_origin(arg) is Link:
                inner = get_args(arg)
                return inner[0] if inner else None
    return None


class InlineModelView(BaseInlineModelView, ModelView):
    """Inline editing of Beanie-backed related documents inside a parent form.

    Declare ``document`` as a class attribute. The FK field is either set
    explicitly via ``fk_attr`` or auto-detected by scanning the child
    document's model fields for a ``Link[ParentDoc]`` field.

    Both plain ``PydanticObjectId`` FK fields and ``Link[Parent]`` fields are
    supported. For a plain ObjectId FK, the value returned by
    ``build_fk_value`` is ``parent.id``; for a Link FK, it is the full parent
    document so Beanie can build the DBRef on save.

    Example:
        ```python
        class CommentInline(InlineModelView):
            document = Comment
            # fk_attr auto-detected: Comment has exactly one Link[Article] field
            fields = ["id", "author", "body"]
            extra = 2

        class ArticleView(ModelView):
            document = Article
            inlines = [CommentInline]
        ```
    """

    document: ClassVar[type[Document]]  # type: ignore[misc]

    def __init__(self, parent_view: BaseModelView | None = None) -> None:
        self.parent_view = parent_view
        ModelView.__init__(self, type(self).document)
        if not self.fk_attr:
            self.fk_attr = self._detect_fk_from_link_field()

    def _detect_fk_from_link_field(self) -> str:
        """Scan the child document's model fields for a Link to the parent document."""
        parent_doc_type = getattr(self.parent_view, "document", None)
        if parent_doc_type is None:
            raise ValueError(
                f"cannot auto-detect fk_attr for {type(self).__name__}: "
                "parent_view has no 'document' attribute. Set fk_attr explicitly."
            )
        link_fields = [
            name
            for name, fi in self.document.model_fields.items()
            if is_link_type(fi.annotation)
            and _get_link_target(fi.annotation) is parent_doc_type
        ]
        if len(link_fields) == 1:
            _log.debug(
                "%s: auto-detected fk_attr=%r (Link field in document)",
                type(self).__name__,
                link_fields[0],
            )
            return link_fields[0]
        if not link_fields:
            raise ValueError(
                f"cannot auto-detect fk_attr for {type(self).__name__}: "
                f"{self.document.__name__} has no Link field pointing to "
                f"{parent_doc_type.__name__}. Set fk_attr explicitly."
            )
        raise ValueError(
            f"cannot auto-detect fk_attr for {type(self).__name__}: "
            f"{self.document.__name__} has multiple Link fields to "
            f"{parent_doc_type.__name__}: {link_fields}. Set fk_attr explicitly."
        )

    def _fk_is_link(self) -> bool:
        """Return True when fk_attr refers to a Beanie Link field."""
        fk = self.fk_attr if isinstance(self.fk_attr, str) else self.fk_attr[0]
        fi = self.document.model_fields.get(str(fk))
        return fi is not None and is_link_type(fi.annotation)

    async def find_by_parent(self, request: Request, parent: Any) -> list[Any]:
        """Return all inline rows whose FK field references `parent`.

        A `Link` FK is stored as a DBRef, so it's matched through its
        embedded `$id` key rather than the field itself.
        """
        fk = self.fk_attr if isinstance(self.fk_attr, str) else self.fk_attr[0]
        if self._fk_is_link():
            return await self.document.find({f"{fk}.$id": parent.id}).to_list()
        return await self.document.find({str(fk): parent.id}).to_list()

    async def build_fk_value(self, request: Request, parent: Any) -> Any:
        """Return the value to store in `fk_attr` for a newly created inline row.

        Returns the full `parent` document when `fk_attr` is a Beanie `Link`
        field, since Beanie needs the document instance to build the DBRef.
        Otherwise returns `parent.id` for a plain `PydanticObjectId` FK field.
        """
        if self.parent_view is None:
            raise RuntimeError(
                "InlineModelView.build_fk_value called before the inline "
                "was wired to a parent view"
            )
        if self._fk_is_link():
            return parent  # Beanie Link fields accept a Document instance
        return parent.id  # plain PydanticObjectId field
