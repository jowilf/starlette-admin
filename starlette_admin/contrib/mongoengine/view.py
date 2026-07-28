import functools
from collections.abc import Sequence
from typing import Any, ClassVar

import mongoengine as me
import starlette_admin.fields as sa
from bson import ObjectId
from mongoengine.base import BaseDocument
from mongoengine.errors import DoesNotExist, ValidationError
from mongoengine.fields import GridFSProxy
from mongoengine.queryset import QNode
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette_admin.contrib.mongoengine.converters import (
    BaseMongoEngineModelConverter,
    ModelConverter,
)
from starlette_admin.contrib.mongoengine.fields import FileField, ImageField
from starlette_admin.contrib.mongoengine.filters import (
    MongoEngineFilterRegistry,
    build_filter_query,
)
from starlette_admin.contrib.mongoengine.helpers import (
    Q,
    build_order_clauses,
    normalize_list,
)
from starlette_admin.exceptions import FormValidationError
from starlette_admin.filters import FilterGroup, FilterRegistry
from starlette_admin.helpers import not_none, prettify_class_name, slugify_class_name
from starlette_admin.logging import get_logger
from starlette_admin.views import BaseModelView
from starlette_admin.views import InlineModelView as BaseInlineModelView

_log = get_logger(__name__)


class ModelView(BaseModelView):
    """`BaseModelView` backed by a `mongoengine.Document`.

    Wraps a document class and implements CRUD, search, filtering, and sorting
    against it, converting its declared fields to admin fields via `converter`.
    """

    def __init__(
        self,
        document: type[me.Document],
        icon: str | None = None,
        display_name: str | None = None,
        menu_label: str | None = None,
        key: str | None = None,
        converter: BaseMongoEngineModelConverter | None = None,
    ):
        """
        Parameters:
            document: The mongoengine document class this view manages.
            icon: CSS class for the icon shown in the admin menu.
            display_name: Display name for the view. Defaults to the prettified
                document class name.
            menu_label: Display label for the view. Defaults to the pluralized,
                prettified document class name.
            key: URL-safe identifier for the view. Defaults to the
                slugified document class name.
            converter: Converter used to turn the document's fields into admin
                fields. Defaults to `ModelConverter()`.
        """
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
        if self.fields is None or len(self.fields) == 0:
            self.fields = document._fields_ordered  # ty: ignore[unresolved-attribute]
        self.fields = (converter or ModelConverter()).convert_fields_list(
            fields=self.fields, model=self.document
        )
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
        self.searchable_fields = normalize_list(self.searchable_fields)
        self.sortable_fields = normalize_list(self.sortable_fields)
        self.fields_default_sort = normalize_list(
            self.fields_default_sort, is_default_sort_list=True
        )
        super().__init__()

    def get_filter_registry(self) -> FilterRegistry:
        """Return the registry used to resolve available filters for this view's fields."""
        return MongoEngineFilterRegistry()

    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        """Return the number of documents matching the search term and filters."""
        qs = await self._build_query(request, q, filters)
        total = self.document.objects(qs).count()  # ty: ignore[unresolved-attribute]
        _log.debug("count: key=%r q=%r total=%d", self.key, q, total)
        return total

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        sorts: Sequence[tuple[str, str]] | None = None,
        filters: FilterGroup | None = None,
    ) -> Sequence[Any]:
        """Return a page of documents matching the search term and filters, sorted
        according to `sorts`.

        A non-positive `limit` returns every matching document from `skip` onward.
        """
        _log.debug(
            "find_all: key=%r skip=%d limit=%d q=%r",
            self.key,
            skip,
            limit,
            q,
        )
        qs = await self._build_query(request, q, filters)
        objs = self.document.objects(qs).order_by(  # ty: ignore[unresolved-attribute]
            *build_order_clauses(sorts or [])
        )
        if limit > 0:
            return objs[skip : skip + limit]
        return objs[skip:]

    async def find_by_pk(self, request: Request, pk: Any) -> me.Document | None:
        """Return the document with primary key `pk`, or `None` if it does not
        exist or `pk` is not a valid ObjectId.
        """
        try:
            obj = self.document.objects(id=pk).get()  # ty: ignore[unresolved-attribute]
            _log.debug("find_by_pk: key=%r pk=%s found", self.key, pk)
            return obj
        except (DoesNotExist, ValidationError):
            _log.debug("find_by_pk: key=%r pk=%s not found", self.key, pk)
            return None

    async def find_by_pks(
        self, request: Request, pks: list[Any]
    ) -> Sequence[me.Document]:
        """Return the documents whose primary key is in `pks`."""
        return self.document.objects(id__in=pks)  # ty: ignore[unresolved-attribute]

    async def get_serialized_pk_value(self, request: Request, obj: Any) -> Any:
        return str(await self.get_pk_value(request, obj))

    async def create(self, request: Request, data: dict[str, Any]) -> Any:
        """Create and save a new document from converted form data.

        Emits `BeforeCreateContext`/`AfterCreateContext` events around the save.
        Exceptions are routed through `handle_exception`.
        """
        _log.debug("create: key=%r populating new document", self.key)
        try:
            await self.validate(request, data)
            obj = await self._populate_obj(request, self.document(), data)
            await self._emit_before_create(request, data, obj)
            obj.save()
            _log.info("create: key=%r pk=%s created", self.key, obj.pk)
            await self._emit_after_create(request, obj)
            return obj
        except Exception as e:
            await self.handle_exception(request, e)

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        """Apply converted form data to the document identified by `pk` and save it.

        Emits `BeforeEditContext`/`AfterEditContext` events around the save.
        Exceptions are routed through `handle_exception`.
        """
        _log.debug("edit: key=%r pk=%s populating document", self.key, pk)
        try:
            await self.validate(request, data)
            obj = await self.find_by_pk(request, pk)
            obj = await self._populate_obj(
                request,
                obj,  # ty: ignore[invalid-argument-type]
                data,
                True,
            )
            await self._emit_before_edit(request, data, obj, pk=pk)
            obj.save()
            _log.info("edit: key=%r pk=%s saved", self.key, pk)
            await self._emit_after_edit(request, obj, pk=pk)
            return obj
        except Exception as e:
            await self.handle_exception(request, e)

    async def _populate_obj(
        self,
        request: Request,
        obj: me.Document,
        data: dict[str, Any],
        is_edit: bool = False,
        document: type[BaseDocument] | None = None,
        fields: Sequence[sa.BaseField] | None = None,
    ) -> me.Document:
        """Assign converted form values onto `obj`, one field at a time.

        Skips read-only fields. `document` and `fields` let this be reused for
        embedded documents (see `_handle_embedded_field`), where `obj` is an
        `EmbeddedDocument` instance rather than the top-level document.

        Parameters:
            request: The request being processed.
            obj: The document (or embedded document) instance to populate.
            data: The converted form data, keyed by field name.
            is_edit: `True` when populating for an edit rather than a create.
            document: The document class `fields` is resolved against. Defaults
                to `self.document`.
            fields: The admin fields to populate. Defaults to the view's field list.

        Returns:
            `obj`, populated in place.
        """
        if document is None:
            document = self.document
        if fields is None:
            fields = self.get_fields_list(request)
        for field in fields:
            if field.read_only:
                continue
            name, value = field.name, data.get(field.name)
            me_field = getattr(document, name)
            await self._set_field(request, obj, name, value, me_field, field, is_edit)
        return obj

    async def _set_field(
        self,
        request: Request,
        obj: me.Document,
        name: str,
        value: Any,
        me_field: Any,
        field: sa.BaseField,
        is_edit: bool,
    ) -> None:
        """Assign `value` to `obj`'s `name` attribute, dispatching on field type:
        file fields go through GridFS handling, embedded documents and lists of
        embedded documents recurse through `_populate_obj`, relation fields are
        converted to `ObjectId`, and everything else is a plain `setattr`.
        """
        if isinstance(field, (FileField, ImageField)):
            self._handle_file_field(obj, name, value)
        elif isinstance(me_field, me.EmbeddedDocumentField) and value is not None:
            await self._handle_embedded_field(
                request, obj, name, value, me_field, field, is_edit
            )
        elif (
            isinstance(me_field, me.ListField)
            and isinstance(me_field.field, me.EmbeddedDocumentField)
            and value is not None
        ):
            await self._handle_embedded_list_field(
                request, obj, name, value, me_field, field, is_edit
            )
        elif isinstance(field, sa.HasOne) and value is not None:
            setattr(obj, name, ObjectId(value))
        elif isinstance(field, sa.HasMany) and value is not None:
            setattr(obj, name, [ObjectId(v) for v in value])
        else:
            setattr(obj, name, value)

    def _handle_file_field(self, obj: me.Document, name: str, value: Any) -> None:
        """Delete, replace, or store a file in the GridFS proxy at `obj.<name>`.

        `value` is the `(upload, should_be_deleted)` tuple that `FileField.parse_form_data`
        produces: `should_be_deleted` clears the current file, an `UploadFile`
        replaces or stores it, and any other value leaves the field untouched.
        """
        proxy: GridFSProxy = getattr(obj, name)
        value, should_be_deleted = not_none(value)
        if should_be_deleted:
            proxy.delete()
        elif isinstance(value, UploadFile):
            if proxy.grid_id is not None:
                proxy.replace(
                    value.file, filename=value.filename, content_type=value.content_type
                )
            else:
                proxy.put(
                    value.file, filename=value.filename, content_type=value.content_type
                )

    async def _handle_embedded_field(
        self,
        request: Request,
        obj: me.Document,
        name: str,
        value: Any,
        me_field: me.EmbeddedDocumentField,
        field: sa.BaseField,
        is_edit: bool,
    ) -> None:
        """Populate `obj.<name>`, an `EmbeddedDocumentField`, from `value`.

        Reuses the existing embedded document when present so unrelated
        attributes are preserved; otherwise instantiates a new one via
        `me_field.document_type`.
        """
        assert isinstance(field, sa.CollectionField)
        old_value = getattr(obj, name, None)
        if old_value is None:
            old_value = me_field.document_type()
        setattr(
            obj,
            name,
            await self._populate_obj(
                request, old_value, value, is_edit, me_field.document_type, field.fields
            ),
        )

    async def _handle_embedded_list_field(
        self,
        request: Request,
        obj: me.Document,
        name: str,
        value: list[Any],
        me_field: me.ListField,
        field: sa.BaseField,
        is_edit: bool,
    ) -> None:
        """Populate `obj.<name>`, a list of embedded documents, from `value`.

        Reuses as many existing embedded documents as possible, in order, and
        appends freshly instantiated ones (via `me_field.field.document_type`)
        if `value` is longer than the current list. Extra existing entries
        beyond `len(value)` are dropped by the final `setattr`.
        """
        assert isinstance(field, sa.ListField) and isinstance(
            field.field, sa.CollectionField
        )
        assert me_field.field is not None
        old_value = getattr(obj, name, [])
        if len(old_value) < len(value):
            old_value.extend(
                [
                    me_field.field.document_type()
                    for _ in range(len(value) - len(old_value))
                ]
            )
        setattr(
            obj,
            name,
            [
                await self._populate_obj(
                    request,
                    old_value[idx],
                    _val,
                    is_edit,
                    me_field.field.document_type,
                    field.field.fields,
                )
                for idx, _val in enumerate(value)
            ],
        )

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        """Delete the documents whose primary key is in `pks`.

        Emits `BeforeDeleteContext`/`AfterDeleteContext` events for each
        affected document around the bulk delete.

        Returns:
            The number of documents deleted.
        """
        _log.debug("delete: key=%r pks=%s", self.key, pks)
        objs = self.document.objects(id__in=pks)  # ty: ignore[unresolved-attribute]
        for obj in objs:
            await self._emit_before_delete(
                request, await self.get_pk_value(request, obj), obj
            )
        deleted_count = objs.delete()
        _log.info("delete: key=%r pks=%s affected=%s", self.key, pks, deleted_count)
        for obj in objs:
            await self._emit_after_delete(
                request, await self.get_pk_value(request, obj), obj
            )
        return deleted_count

    async def handle_exception(self, request: Request, exc: Exception) -> None:
        """Translate a mongoengine `ValidationError` into a `FormValidationError`
        so field-level errors surface on the form. Any other exception is logged
        and re-raised unchanged.
        """
        if isinstance(exc, FormValidationError):
            raise exc
        if isinstance(exc, ValidationError):
            _log.debug(
                "handle_exception: key=%r validation error: %s",
                self.key,
                exc.to_dict(),
            )
            raise FormValidationError(exc.to_dict())
        _log.error(
            "handle_exception: key=%r unexpected error: %s",
            self.key,
            exc,
            exc_info=exc,
        )
        raise exc  # pragma: no cover

    async def _build_query(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> QNode:
        """Combine the full-text search term and the parsed filter tree into a
        single `QNode`, ANDing the two together when both are present.
        """
        qs = Q.empty()
        if q is not None:
            qs = await self.build_full_text_search_query(request, q)
        if filters is not None and not filters.is_empty():
            fields_by_name = {f.name: f for f in self.get_fields_list(request)}
            registry = self.get_filter_registry()
            filter_q = build_filter_query(
                filters, fields_by_name, registry, self, request
            )
            if filter_q is not None:
                qs = qs & filter_q
        return qs

    async def build_full_text_search_query(self, request: Request, term: str) -> QNode:
        """Build a `QNode` matching `term` case-insensitively against every
        searchable text-like field (string, text area, email, URL, phone, color),
        excluding the primary key. Fragments are combined with `|` (OR).
        """
        queries = []
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
                queries.append(Q(field.name, term, "icontains"))
        return (
            functools.reduce(lambda q1, q2: q1 | q2, queries) if queries else Q.empty()
        )


class InlineModelView(BaseInlineModelView, ModelView):
    """Inline editing of MongoEngine-backed related documents inside a parent form.

    Declare ``document`` as a class attribute. The parent reference field is
    auto-detected by scanning the child document's fields for a
    ``ReferenceField`` whose ``document_type`` matches the parent document.

    Example::

        class CommentInline(InlineModelView):
            document = Comment
            fields = ["id", "author", "body"]
            extra = 2

        class ArticleView(ModelView):
            document = Article
            inlines = [CommentInline]
    """

    document: ClassVar[type[me.Document]]

    def __init__(self, parent_view: BaseModelView | None = None) -> None:
        self.parent_view = parent_view
        ModelView.__init__(self, type(self).document)
        if not self.fk_attr:
            self.fk_attr = self._detect_fk_from_reference_field()

    def _detect_fk_from_reference_field(self) -> str:
        """Scan the child document's fields for a single `ReferenceField` pointing
        back at the parent document, and return its name for use as `fk_attr`.

        Raises:
            ValueError: If the child document has zero or more than one
                matching `ReferenceField`, since `fk_attr` cannot be inferred
                unambiguously in that case.
        """
        assert self.parent_view is not None, (
            "parent_view must be set to auto-detect fk_attr"
        )
        ref_fields = [
            name
            for name, field in self.document._fields.items()  # ty: ignore[unresolved-attribute]
            if isinstance(field, me.ReferenceField)
            and field.document_type is self.parent_view.document  # ty: ignore[unresolved-attribute]
        ]
        if len(ref_fields) == 1:
            _log.debug(
                "%s: auto-detected fk_attr=%r (single ReferenceField in document)",
                type(self).__name__,
                ref_fields[0],
            )
            return ref_fields[0]
        if len(ref_fields) == 0:
            raise ValueError(
                f"{type(self).__name__}: cannot auto-detect fk_attr. "
                f"{self.document.__name__} has no ReferenceField. "
                "Set fk_attr explicitly."
            )
        raise ValueError(
            f"{type(self).__name__}: cannot auto-detect fk_attr. "
            f"{self.document.__name__} has multiple ReferenceFields "
            f"({ref_fields}). Set fk_attr explicitly."
        )

    async def find_by_parent(self, request: Request, parent: Any) -> Sequence[Any]:
        """Return the child documents whose `fk_attr` equals `parent`'s primary key."""
        # Composite fk_attr (see BaseInlineModelView) is not supported here.
        assert isinstance(self.fk_attr, str)
        _log.debug(
            "find_by_parent %s: parent pk=%s fk_attr=%r",
            self.document.__name__,
            parent.pk,
            self.fk_attr,
        )
        rows = list(
            self.document.objects(**{self.fk_attr: parent.pk})  # ty: ignore[unresolved-attribute]
        )
        _log.debug("find_by_parent %s → %d row(s)", self.document.__name__, len(rows))
        return rows

    async def _populate_obj(
        self,
        request: Request,
        obj: me.Document,
        data: dict[str, Any],
        is_edit: bool = False,
        document: type[BaseDocument] | None = None,
        fields: Sequence[sa.BaseField] | None = None,
    ) -> me.Document:
        """Populate `obj` via the base `ModelView` logic, then stamp the parent
        foreign key onto newly created children.

        The `fk_attr` field is typically excluded from the inline form (its
        value comes from the parent context), so it is set explicitly here
        from `data` rather than through the field-by-field loop in the base
        implementation. This only applies on create: an existing child's
        parent reference is not reassigned on edit.
        """
        await super()._populate_obj(request, obj, data, is_edit, document, fields)
        # Composite fk_attr (see BaseInlineModelView) is not supported here.
        assert isinstance(self.fk_attr, str)
        if not is_edit and self.fk_attr in data:
            _log.debug(
                "_populate_objtry obj : %s, fk : %s, %s", obj, self.fk_attr, data
            )
            setattr(obj, self.fk_attr, data[self.fk_attr])
        return obj
