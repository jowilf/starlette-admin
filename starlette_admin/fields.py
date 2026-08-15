import builtins
import decimal
import inspect
import io
import json
from collections.abc import Callable, Collection, Sequence
from dataclasses import asdict, dataclass, replace
from dataclasses import field as dc_field
from datetime import UTC, date, datetime, time
from enum import Enum, IntEnum
from json import JSONDecodeError
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

from starlette.datastructures import FormData, Headers, UploadFile
from starlette.requests import Request
from starlette_admin.helpers import (
    _URL_ALLOWED_SCHEMES,
    field_error_payload,
    html_params,
    is_empty_file,
    is_empty_value,
    maybe_async,
    not_none,
    safe_url,
    static_url,
    to_form_entry,
)
from starlette_admin.i18n import (
    format_date,
    format_datetime,
    format_time,
    get_countries_list,
    get_currencies_list,
    get_database_tzinfo,
    get_locale,
    get_tzinfo,
    is_timezone_conversion_enabled,
)
from starlette_admin.i18n import (
    lazy_gettext as _,
)
from starlette_admin.logging import get_logger
from starlette_admin.storage.base import (
    BaseStorage,
    FileInfo,
    UnknownStorageError,
    get_storage,
)
from starlette_admin.types import Formatter, Getter, Parser, RequestAction
from starlette_admin.utils.timezones import common_timezones
from starlette_admin.validators import (
    Validator,
    email,
    file_size,
    file_type,
    ip_address,
    number_range,
    slug,
    url,
    uuid,
    valid_image,
)

_log = get_logger(__name__)

DEFAULT_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

if TYPE_CHECKING:
    from starlette_admin.filters.base import BaseFilter
    from starlette_admin.views import BaseModelView

try:
    import arrow
except ImportError:
    arrow = None  # ty: ignore[invalid-assignment]


@dataclass
class BaseField:
    """
    The base configuration class for all model fields.

    Parameters:
        name: The field's name, which must match the attribute name in your model.
        label: A human-readable label used for display purposes.
        help_text: An optional hint or description to display within forms.
        type: The unique identifier for the field's type.
        disabled: If `True`, the field is rendered as disabled in forms.
        read_only: If `True`, the field is rendered as read-only in forms.
        default: The default value used to prefill the field on creation forms.
            This can be a static value or a callable that accepts zero or one
            positional argument (the current request).
        getter: `(request, obj) -> value`, sync or async. When set, used by
            [parse_obj][starlette_admin.fields.BaseField.parse_obj] instead of
            `getattr(obj, self.name, None)`, so a field's value can be derived
            without subclassing. See [ComputedField][starlette_admin.fields.ComputedField].
        formatter: Maps a [RequestAction][starlette_admin.types.RequestAction] to a
            `(request, value) -> value` callable, sync or async. When the current
            action has an entry, its callable replaces `serialize_value` /
            `serialize_none_value` entirely; its return value (including for a
            `None` input) is used as-is.
        parser: Maps a [RequestAction][starlette_admin.types.RequestAction] to a
            `(request, raw) -> value` callable, sync or async. When the current
            action has an entry, its callable replaces this field's default
            parsing entirely, so custom form/import parsing can be attached
            without subclassing. See
            [parse_input][starlette_admin.fields.BaseField.parse_input].
        id: A unique identifier for the field instance.
        filters: An explicit override for the list page filters available for this
            field. If `None` (the default), the view's filter registry automatically
            selects filters based on the field's `type`. See
            [FilterRegistry][starlette_admin.filters.FilterRegistry].
        required: If `True`, the field is marked as required in forms and
            enforced server-side by [validate][starlette_admin.fields.BaseField.validate].
        validators: Callables `(request, field, value)` run in order against the
            parsed form value, each raising `ValueError` to reject it. The first
            error is reported and the remaining validators are skipped. Empty
            values are only checked against `required`; validators never run on
            them. See [starlette_admin.validators][] for built-in validators.
        exclude_from_list: If `True`, hides the field from the list view.
        exclude_from_detail: If `True`, hides the field from the detail view.
        exclude_from_create: If `True`, hides the field from the creation form.
        exclude_from_edit: If `True`, hides the field from the edit form.
        exclude_from_export: If `True`, excludes the field when exporting data.
        exclude_from_import: If `True`, ignores the field when importing data.
        searchable: If `True`, the field is included in search queries.
        orderable: If `True`, allows sorting by this field in the list view.
        inline_editable: If `True`, this field can be edited inline from the
            list page. Set automatically by the view from
            `BaseModelView.inline_editable_fields`; do not set directly.
        copy_to_clipboard: If `True`, renders a button next to the field's value
            on the detail page that copies it to the clipboard.
        list_template: The template path used to render this field in the list view.
        form_template: The template path used to render this field in create/edit forms.
        detail_template: The template path used to render this field in the detail view.
        null_template: The template path used to render this field when its value is `None`,
            in both the list and detail views.
        empty_template: The template path used to render this field when its value is an
            empty list or tuple, in both the list and detail views.
        extra: A dictionary for storing custom metadata. Starlette-admin neither reads
            nor writes to this dictionary. It is provided solely as a convenience for
            developers to attach arbitrary data to a field (e.g., to access within custom
            templates or [BaseAdmin][starlette_admin.base.BaseAdmin] hooks) without needing
            to subclass the field.
    """

    name: str
    label: str | None = None
    type: str | None = None
    help_text: str | None = None
    disabled: bool | None = False
    read_only: bool | None = False
    default: Any | None = None
    # Excluded from equality: closures never compare equal.
    getter: Getter | None = dc_field(default=None, compare=False)
    formatter: dict[RequestAction, Formatter] | None = dc_field(
        default=None, compare=False
    )
    parser: dict[RequestAction, Parser] | None = dc_field(default=None, compare=False)
    id: str = ""
    filters: list[builtins.type["BaseFilter"]] | None = None
    required: bool | None = False
    # Excluded from equality: validators are closures, which never compare equal.
    validators: list[Validator] = dc_field(default_factory=list, compare=False)
    exclude_from_list: bool | None = False
    exclude_from_detail: bool | None = False
    exclude_from_create: bool | None = False
    exclude_from_edit: bool | None = False
    exclude_from_export: bool | None = False
    exclude_from_import: bool | None = False
    searchable: bool | None = True
    orderable: bool | None = True
    inline_editable: bool | None = False
    copy_to_clipboard: bool | None = False
    list_template: str = "fields/list/text.html"
    form_template: str = "fields/form/input.html"
    label_template: str = "fields/form/_label.html"
    detail_template: str = "fields/detail/text.html"
    null_template: str = "fields/detail/_null.html"
    empty_template: str = "fields/detail/_empty.html"
    extra: dict[str, Any] | None = None
    error_class = "is-invalid"
    # Set by `BaseModelView._init_fields`: the field's fully dotted name.
    # Differs from `name` only for fields nested under a CollectionField.
    _name: str = dc_field(default="", init=False, repr=False, compare=False)
    # Set by `BaseModelView._init_fields` on RelationField/CollectionField
    # instances, so nested serialization can resolve the owning view.
    _view: "BaseModelView | None" = dc_field(
        default=None, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if self.label is None:
            self.label = self.name.replace("_", " ").capitalize()
        if self.type is None:
            self.type = type(self).__name__
        self.id = self.name
        _log.debug(
            "field initialized: name=%r type=%s label=%r",
            self.name,
            self.type,
            self.label,
        )

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        """
        Extracts the value of this field from submitted form data.
        """
        raw = form_data.get(self.id)
        _log.debug(
            "parse_form_data: field=%r id=%r raw=%r",
            self.name,
            self.id,
            raw,
        )
        return raw

    async def parse_input(self, request: Request, raw: Any) -> Any:
        """Single entry point for turning raw input into this field's value.

        Routes to [parse_import_value][starlette_admin.fields.BaseField.parse_import_value]
        when `request.state.action` is IMPORT, otherwise to
        [parse_form_data][starlette_admin.fields.BaseField.parse_form_data]
        (CREATE, EDIT, INLINE_EDIT).

        Checks `self.parser` first, keyed by `request.state.action`: when the
        current action has an entry, its callable replaces the field's
        default parsing entirely, and `raw` is passed to it unchanged.

        Args:
            raw: A `FormData` for CREATE, EDIT, and INLINE_EDIT; the raw
                import cell value for IMPORT.
        """
        action = request.state.action
        parser = (self.parser or {}).get(action)
        if action == RequestAction.IMPORT:
            if parser is not None:
                return await maybe_async(parser(request, raw))
            return await self.parse_import_value(request, raw)
        if parser is not None:
            source = (
                raw.getlist(self.id)
                if getattr(self, "multiple", False)
                else raw.get(self.id)
            )
            return await maybe_async(parser(request, source))
        return await self.parse_form_data(request, raw)

    async def validate(
        self, request: Request, value: Any, form_values: dict[str, Any]
    ) -> None:
        """Validates this field's parsed form value, raising `ValueError` on
        the first failure.

        An empty value (`None`, `""`, or an empty collection) is only checked
        against `required`; the `validators` chain runs solely on non-empty
        values, so validators never have to handle missing input.

        Parameters:
            request: The request being processed.
            value: This field's own parsed value.
            form_values: The full submitted data, keyed by field name, parsed
                before validation started.
        """
        if is_empty_value(value):
            if self.required:
                raise ValueError(_("This field is required."))
            return
        await self._run_validators(request, self.validators, value, form_values)

    async def _run_validators(
        self,
        request: Request,
        validators: Sequence[Validator],
        value: Any,
        form_values: dict[str, Any],
    ) -> None:
        """Runs each validator in order, awaiting async ones, stopping at the
        first `ValueError`."""
        for validator in validators:
            result = validator(request, self, value, form_values)
            if inspect.isawaitable(result):
                await result

    async def parse_obj(self, request: Request, obj: Any) -> Any:
        """Extracts the value of this field from a model instance.

        By default, this function returns the value of the attribute with the name `self.name` from `obj`,
        or the result of `self.getter(request, obj)` when `getter` is set.
        This function can also be overridden to provide custom logic for computing the value of a field.

        ??? Example

            ```py
            # Suppose we have a `User` model with `id`, `first_name`, and `last_name` fields.
            # We define a custom field called `MyCustomField` to compute the full name of the user:

            class MyCustomField(StringField):
                async def parse_obj(self, request: Request, obj: Any) -> Any:
                    return f"{obj.first_name} {obj.last_name}"  # Returns the full name of the user


            # Then, we can define our view as follows

            class UserView(ModelView):
                fields = ["id", MyCustomField("full_name")]
            ```
        """
        value = (
            await maybe_async(self.getter(request, obj))
            if self.getter is not None
            else getattr(obj, self.name, None)
        )
        _log.debug(
            "parse_obj: field=%r obj_type=%s value=%r",
            self.name,
            type(obj).__name__,
            value,
        )
        return value

    async def serialize_none_value(self, request: Request) -> Any:
        """Formats a None value for sending to the frontend.

        Args:
            request: The current request object.

        Returns:
            Any: The formatted None value.
        """
        _log.debug(
            "serialize_none_value: field=%r action=%s",
            self.name,
            request.state.action,
        )
        return None

    async def serialize_value(self, request: Request, value: Any) -> Any:
        """Formats a value for sending to the frontend based on the current request action.

        !!! important

            Make sure this value is JSON Serializable for RequestAction.LIST and RequestAction.RELATION_LOOKUP

        Args:
            request: The current request object.
            value: The value to format.

        Returns:
            Any: The formatted value.
        """
        _log.debug(
            "serialize_value: field=%r action=%s value=%r",
            self.name,
            request.state.action,
            value,
        )
        return value

    async def parse_import_value(self, request: Request, value: Any) -> Any:
        """Parse a raw cell value from an import row into the value that
        ``view.create()`` expects for this field.

        Delegates to :meth:`parse_form_data` by building a minimal
        :class:`~starlette.datastructures.FormData` from the cell value, so
        import parsing stays consistent with form-submission parsing.  When
        *value* is a list (e.g. a multi-value column from JSON), each item is
        added as a separate form entry under ``self.id`` so that
        :meth:`~starlette.datastructures.FormData.getlist` returns the full
        sequence. Values are stringified through :func:`to_form_entry` so
        non-string primitives round-trip: a `date` is already an ISO string, a
        `bool` becomes `"true"`/`"false"`, and a `dict`/`list` becomes
        `json.dumps(...)` rather than Python `repr`, matching what
        `JSONField.parse_form_data` feeds to `json.loads`.

        Override this method for fields whose import logic cannot be expressed
        as a simple :class:`FormData` round-trip.

        Args:
            request: The request being processed.
            value: Raw value (string, number, bool, list, …) read from the
                import file for this field's column.

        Returns:
            The value to store in the ``data`` dict passed to ``view.create()``.
        """
        _log.debug(
            "parse_import_value: field=%r raw_type=%s raw=%r",
            self.name,
            type(value).__name__,
            value,
        )
        if value is None:
            form_data = FormData([])
        elif isinstance(value, list):
            form_data = FormData([(self.id, to_form_entry(v)) for v in value])
        else:
            form_data = FormData([(self.id, to_form_entry(value))])
        result = await self.parse_form_data(request, form_data)
        _log.debug(
            "parse_import_value: field=%r result=%r",
            self.name,
            result,
        )
        return result

    def additional_css_links(self, request: Request) -> list[str]:
        """Returns a list of CSS file URLs to include for the current request action."""
        return []

    def additional_js_links(self, request: Request) -> list[str]:
        """Returns a list of JavaScript file URLs to include for the current request action."""
        return []

    def _needs_form_assets(self, request: Request) -> bool:
        """True on a form request (create/edit/inline-edit, per `is_form()`),
        or on the list page when this field is `inline_editable`: the
        inline-edit popover renders this field's form fragment on the list
        page, so the list page must ship the same CSS/JS."""
        action = request.state.action
        return action.is_form() or (
            bool(self.inline_editable) and action == RequestAction.LIST
        )

    def dict(self) -> dict[str, Any]:
        """Return the dataclass instance as a dictionary."""
        return asdict(self)

    def input_params(self) -> str:
        """Return HTML input parameters as a string."""
        return html_params(
            {
                "disabled": self.disabled,
                "readonly": self.read_only,
            }
        )

    async def get_create_default(self, request: Request) -> Any:
        """Return the value that should be used to prefill this field on the
        create form.

        ``default`` may be:

        * a static value (e.g. ``default="hello"``),
        * a callable that takes no arguments (e.g. ``default=datetime.now``),
        * a callable that takes the current request as its only argument
          (e.g. ``default=lambda request: request.user.locale``).

        Subclasses may override this method to coerce the default into the
        shape expected by their form templates.
        """
        if self.default is None:
            return None
        if callable(self.default):
            result = self._call_default(request)
            if inspect.isawaitable(result):
                return await result
            return result
        return self.default

    def _call_default(self, request: Request) -> Any:
        """Invoke a callable ``default`` value, passing ``request`` only when
        the callable expects a positional argument.
        """
        assert callable(self.default)
        try:
            sig = inspect.signature(self.default)
        except (ValueError, TypeError):
            return self.default()
        required = [
            p
            for p in sig.parameters.values()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            and p.default is inspect.Parameter.empty
        ]
        if len(required) == 1:
            return self.default(request)
        return self.default()


@dataclass
class BooleanField(BaseField):
    """This field displays the `true/false` value of a boolean property."""

    list_template: str = "fields/list/boolean.html"
    form_template: str = "fields/form/boolean.html"
    detail_template: str = "fields/detail/boolean.html"

    async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
        raw = form_data.get(self.id)
        result = (
            raw.lower() in ("on", "true", "yes")
            if (raw is not None and isinstance(raw, str))
            else False
        )
        _log.debug(
            "BooleanField.parse_form_data: field=%r raw=%r -> %r",
            self.name,
            raw,
            result,
        )
        return result

    async def serialize_value(self, request: Request, value: Any) -> bool:
        result = bool(value)
        _log.debug(
            "BooleanField.serialize_value: field=%r value=%r -> %r",
            self.name,
            value,
            result,
        )
        return result


@dataclass
class StringField(BaseField):
    """This field is used to represent any kind of short text content."""

    maxlength: int | None = None
    minlength: int | None = None
    input_type: str = "text"
    class_: str = "field-string form-control"
    placeholder: str | None = None

    def input_params(self) -> str:
        return html_params(
            {
                "type": self.input_type,
                "minlength": self.minlength,
                "maxlength": self.maxlength,
                "placeholder": self.placeholder,
                "required": self.required,
                "disabled": self.disabled,
                "readonly": self.read_only,
            }
        )

    async def serialize_value(self, request: Request, value: Any) -> Any:
        return str(value)


@dataclass
class TextAreaField(StringField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    class_: str = "field-textarea form-control"
    form_template: str = "fields/form/textarea.html"
    detail_template: str = "fields/detail/textarea.html"

    def input_params(self) -> str:
        return html_params(
            {
                "rows": self.rows,
                "minlength": self.minlength,
                "maxlength": self.maxlength,
                "placeholder": self.placeholder,
                "required": self.required,
                "disabled": self.disabled,
                "readonly": self.read_only,
            }
        )


@dataclass
class TinyMCEEditorField(TextAreaField):
    """A field that provides a WYSIWYG editor for long text content using the
     [TinyMCE](https://www.tiny.cloud/) library.

    This field can be used as an alternative to the [TextAreaField][starlette_admin.fields.TextAreaField]
    to provide a more sophisticated editor for user input.

    Parameters:
        version_tinymce: TinyMCE version
        version_tinymce_jquery: TinyMCE jQuery version
        height: Height of the editor
        menubar: Show/hide the menubar in the editor
        statusbar: Show/hide the statusbar in the editor
        toolbar: Toolbar options to show in the editor
        content_style: CSS style to apply to the editor content
        extra_options: Other options to pass to TinyMCE
    """

    class_: str = "field-tinymce-editor form-control"
    detail_template: str = "fields/detail/tinymce.html"
    version_tinymce: str = "6.4"
    version_tinymce_jquery: str = "2.0"
    height: int = 300
    menubar: bool | str = False
    statusbar: bool = False
    toolbar: str = (
        "undo redo | formatselect | bold italic backcolor | alignleft aligncenter"
        " alignright alignjustify | bullist numlist outdent indent | removeformat"
    )
    content_style: str = (
        "body { font-family: -apple-system, BlinkMacSystemFont, San Francisco, Segoe"
        " UI, Roboto, Helvetica Neue, sans-serif; font-size: 14px;"
        " -webkit-font-smoothing: antialiased; }"
    )
    extra_options: dict[str, Any] = dc_field(default_factory=dict)
    """For more options, see the [TinyMCE | Documentation](https://www.tiny.cloud/docs/tinymce/6/)"""

    def additional_js_links(self, request: Request) -> list[str]:
        if self._needs_form_assets(request):
            return [
                f"https://cdn.jsdelivr.net/npm/tinymce@{self.version_tinymce}/tinymce.min.js",
                f"https://cdn.jsdelivr.net/npm/@tinymce/tinymce-jquery@{self.version_tinymce_jquery}/dist/tinymce-jquery.min.js",
            ]
        return []

    def input_params(self) -> str:
        _options = {
            "height": self.height,
            "menubar": self.menubar,
            "statusbar": self.statusbar,
            "toolbar": self.toolbar,
            "content_style": self.content_style,
            **self.extra_options,
        }

        return (
            super().input_params()
            + " "
            + html_params({"data-options": json.dumps(_options)})
        )


@dataclass
class NumberField(StringField):
    """This field is used to represent the value of properties
    that store numbers of any type (integers or decimals).
    Should not be used directly. use [IntegerField][starlette_admin.fields.IntegerField]
    or [DecimalField][starlette_admin.fields.DecimalField]
    """

    input_type: str = "number"
    max: int | None = None
    min: int | None = None
    step: str | int | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.validators and (self.min is not None or self.max is not None):
            self.validators = [number_range(min=self.min, max=self.max)]

    def input_params(self) -> str:
        return html_params(
            {
                "type": self.input_type,
                "min": self.min,
                "max": self.max,
                "step": self.step,
                "placeholder": self.placeholder,
                "required": self.required,
                "disabled": self.disabled,
                "readonly": self.read_only,
            }
        )


@dataclass
class IntegerField(NumberField):
    """
    This field is used to represent the value of properties that store integer numbers.
    Erroneous input is ignored and will not be accepted as a value."""

    class_: str = "field-integer form-control"

    async def parse_form_data(
        self, request: Request, form_data: FormData
    ) -> int | None:
        raw = form_data.get(self.id)
        try:
            result = int(raw)  # ty: ignore[invalid-argument-type]
            _log.debug(
                "IntegerField.parse_form_data: field=%r raw=%r -> %r",
                self.name,
                raw,
                result,
            )
            return result
        except (ValueError, TypeError):
            _log.warning(
                "IntegerField.parse_form_data: field=%r cannot coerce raw=%r to int; returning None",
                self.name,
                raw,
            )
            return None

    async def parse_import_value(self, request: Request, value: Any) -> int | None:
        if value is None or value == "":
            _log.debug(
                "IntegerField.parse_import_value: field=%r empty value; returning None",
                self.name,
            )
            return None
        try:
            result = int(value)
            _log.debug(
                "IntegerField.parse_import_value: field=%r raw=%r -> %r",
                self.name,
                value,
                result,
            )
            return result
        except (ValueError, TypeError) as exc:
            _log.error(
                "IntegerField.parse_import_value: field=%r invalid integer raw=%r; %s",
                self.name,
                value,
                exc,
            )
            raise ValueError(
                _("Invalid integer value for %(field)s") % {"field": self.name}
            ) from exc

    async def serialize_value(self, request: Request, value: Any) -> Any:
        result = int(value)
        _log.debug(
            "IntegerField.serialize_value: field=%r value=%r -> %r",
            self.name,
            value,
            result,
        )
        return result


@dataclass
class DecimalField(NumberField):
    """
    This field is used to represent the value of properties that store decimal numbers.
    Erroneous input is ignored and will not be accepted as a value.
    """

    step: str = "any"
    class_: str = "field-decimal form-control"

    async def parse_form_data(
        self, request: Request, form_data: FormData
    ) -> decimal.Decimal | None:
        raw = form_data.get(self.id)
        try:
            result = decimal.Decimal(raw)  # ty: ignore[invalid-argument-type]
            _log.debug(
                "DecimalField.parse_form_data: field=%r raw=%r -> %r",
                self.name,
                raw,
                result,
            )
            return result
        except (decimal.InvalidOperation, TypeError, ValueError):
            _log.warning(
                "DecimalField.parse_form_data: field=%r cannot coerce raw=%r to Decimal; returning None",
                self.name,
                raw,
            )
            return None

    async def parse_import_value(
        self, request: Request, value: Any
    ) -> decimal.Decimal | None:
        if value is None or value == "":
            _log.debug(
                "DecimalField.parse_import_value: field=%r empty value; returning None",
                self.name,
            )
            return None
        try:
            result = decimal.Decimal(value)
            _log.debug(
                "DecimalField.parse_import_value: field=%r raw=%r -> %r",
                self.name,
                value,
                result,
            )
            return result
        except (decimal.InvalidOperation, ValueError, TypeError) as exc:
            _log.error(
                "DecimalField.parse_import_value: field=%r invalid decimal raw=%r; %s",
                self.name,
                value,
                exc,
            )
            raise ValueError(
                _("Invalid decimal value for %(field)s") % {"field": self.name}
            ) from exc

    async def serialize_value(self, request: Request, value: Any) -> str:
        result = str(value)
        _log.debug(
            "DecimalField.serialize_value: field=%r value=%r -> %r",
            self.name,
            value,
            result,
        )
        return result


@dataclass
class FloatField(StringField):
    """
    A text field, except all input is coerced to an float.
     Erroneous input is ignored and will not be accepted as a value.
    """

    class_: str = "field-float form-control"

    async def parse_form_data(
        self, request: Request, form_data: FormData
    ) -> float | None:
        raw = form_data.get(self.id)
        try:
            result = float(raw)  # ty: ignore[invalid-argument-type]
            _log.debug(
                "FloatField.parse_form_data: field=%r raw=%r -> %r",
                self.name,
                raw,
                result,
            )
            return result
        except ValueError:
            _log.warning(
                "FloatField.parse_form_data: field=%r cannot coerce raw=%r to float; returning None",
                self.name,
                raw,
            )
            return None

    async def parse_import_value(self, request: Request, value: Any) -> float | None:
        if value is None or value == "":
            _log.debug(
                "FloatField.parse_import_value: field=%r empty value; returning None",
                self.name,
            )
            return None
        try:
            result = float(value)
            _log.debug(
                "FloatField.parse_import_value: field=%r raw=%r -> %r",
                self.name,
                value,
                result,
            )
            return result
        except (ValueError, TypeError) as exc:
            _log.error(
                "FloatField.parse_import_value: field=%r invalid float raw=%r; %s",
                self.name,
                value,
                exc,
            )
            raise ValueError(
                _("Invalid float value for %(field)s") % {"field": self.name}
            ) from exc

    async def serialize_value(self, request: Request, value: Any) -> float:
        result = float(value)
        _log.debug(
            "FloatField.serialize_value: field=%r value=%r -> %r",
            self.name,
            value,
            result,
        )
        return result


@dataclass
class TagsField(BaseField):
    """
    This field is used to represent the value of properties that store a list of
    string values. Render as `select2` tags input.
    """

    list_template: str = "fields/list/tags.html"
    detail_template: str = "fields/detail/tags.html"
    form_template: str = "fields/form/tags.html"
    form_js: str = "js/field/forms/tags.js"
    class_: str = "form-control form-select"

    async def parse_form_data(self, request: Request, form_data: FormData) -> list[str]:
        result = form_data.getlist(self.id)
        _log.debug(
            "TagsField.parse_form_data: field=%r id=%r -> %d item(s) %r",
            self.name,
            self.id,
            len(result),
            result,
        )
        return result  # ty: ignore[invalid-return-type]

    async def serialize_value(self, request: Request, value: Any) -> Any:
        action = request.state.action
        _log.debug(
            "TagsField.serialize_value: field=%r action=%s value=%r",
            self.name,
            action,
            value,
        )
        if action == RequestAction.EXPORT:
            if (
                getattr(getattr(request.state, "export_type", None), "extension", None)
                == "json"
            ):
                return (
                    value
                    if isinstance(value, list)
                    else ([str(value)] if value is not None else [])
                )
            if isinstance(value, list):
                return "\n".join(str(v) for v in value)
            return str(value) if value is not None else ""
        return value

    async def parse_import_value(self, request: Request, value: Any) -> list[str]:
        _log.debug(
            "TagsField.parse_import_value: field=%r raw_type=%s raw=%r",
            self.name,
            type(value).__name__,
            value,
        )
        if isinstance(value, str):
            items = [v for v in value.split("\n") if v]
        elif isinstance(value, list):
            items = [str(v) for v in value]
        else:
            items = []
        _log.debug(
            "TagsField.parse_import_value: field=%r parsed %d item(s)",
            self.name,
            len(items),
        )
        form_data = FormData([(self.id, item) for item in items])
        return await self.parse_form_data(request, form_data)

    def additional_css_links(self, request: Request) -> list[str]:
        if self._needs_form_assets(request):
            return [static_url(request, "css/vendor/select2.min.css", v="4.1.0")]
        return []

    def additional_js_links(self, request: Request) -> list[str]:
        if self._needs_form_assets(request):
            return [static_url(request, "js/vendor/select2.min.js", v="4.1.0")]
        return []


@dataclass
class EmailField(StringField):
    """This field is used to represent a text content
    that stores a single email address.

    [email][starlette_admin.validators.email] is used as the default validator
    when `validators` is empty, to ensure the value is a valid email address.
    Pass your own `validators` to override it.
    """

    input_type: str = "email"
    list_template: str = "fields/list/email.html"
    class_: str = "field-email form-control"
    detail_template: str = "fields/detail/email.html"

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.validators:
            self.validators = [email()]


@dataclass
class URLField(StringField):
    """This field is used to represent a text content that stores a single URL.

    [url][starlette_admin.validators.url] is used as the default validator
    when `validators` is empty, to ensure the value is a valid absolute URL.
    Pass your own `validators` to override it.

    Attributes:
        allowed_schemes: Schemes allowed when rendering the value on the list
            and detail pages. Any other scheme (javascript:, data:, vbscript:,
            …) is stripped. Defaults to `http`, `https`, `mailto`, `tel`,
            `ftp`, `ftps`, and `sms`. Set to `None` to skip this check and
            render the value as-is.
    """

    input_type: str = "url"
    list_template: str = "fields/list/url.html"
    class_: str = "field-url form-control"
    detail_template: str = "fields/detail/url.html"
    allowed_schemes: Collection[str] | None = dc_field(
        default_factory=lambda: _URL_ALLOWED_SCHEMES
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.validators:
            self.validators = [url(schemes=self.allowed_schemes)]

    async def serialize_value(self, request: Request, value: Any) -> Any:
        value = await super().serialize_value(request, value)
        if self.allowed_schemes is not None and request.state.action in (
            RequestAction.LIST,
            RequestAction.DETAIL,
        ):
            return safe_url(value, self.allowed_schemes)
        return value


@dataclass
class PhoneField(StringField):
    """A StringField, except renders an `<input type="phone">`."""

    input_type: str = "phone"
    class_: str = "field-phone form-control"


@dataclass
class ColorField(StringField):
    """A StringField, except renders an `<input type="color">`."""

    input_type: str = "color"
    class_: str = "field-color form-control form-control-color"
    list_template: str = "fields/list/color.html"
    detail_template: str = "fields/detail/color.html"


@dataclass
class PasswordField(StringField):
    """A StringField, except renders an `<input type="password">`."""

    input_type: str = "password"
    class_: str = "field-password form-control"


@dataclass
class UUIDField(StringField):
    """This field is used to represent a text content that stores a single UUID.

    [uuid][starlette_admin.validators.uuid] is used as the default validator
    when `validators` is empty, restricted to `version` when set, to ensure
    the value is a valid UUID. Pass your own `validators` to override it.

    Attributes:
        version: When set (1, 3, 4, or 5), also requires the UUID to be of
            that version.
    """

    class_: str = "field-uuid form-control"
    version: int | None = None
    copy_to_clipboard: bool | None = True

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.validators:
            self.validators = [uuid(version=self.version)]


@dataclass
class IPAddressField(StringField):
    """This field is used to represent a text content that stores a single IP address.

    [ip_address][starlette_admin.validators.ip_address] is used as the default
    validator when `validators` is empty, restricted to `ipv4`/`ipv6` when set,
    to ensure the value is a valid IP address. Pass your own `validators` to
    override it.

    Attributes:
        ipv4: If `True`, accepts IPv4 addresses.
        ipv6: If `True`, accepts IPv6 addresses.
    """

    class_: str = "field-ip-address form-control"
    ipv4: bool = True
    ipv6: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.validators:
            self.validators = [ip_address(ipv4=self.ipv4, ipv6=self.ipv6)]


@dataclass
class EnumField(StringField):
    """
    Enumeration Field.
    It takes a python `enum.Enum` class or a list of *(value, label)* pairs.
    It can also be a list of only values, in which case the value is used as the label.
    Example:
        ```python
        class Status(str, enum.Enum):
            NEW = "new"
            ONGOING = "ongoing"
            DONE = "done"

        class MyModel:
            status: Optional[Status] = None

        class MyModelView(ModelView):
            fields = [EnumField("status", enum=Status)]
        ```

        ```python
        class MyModel:
            language: str

        class MyModelView(ModelView):
            fields = [
                EnumField(
                    "language",
                    choices=[("cpp", "C++"), ("py", "Python"), ("text", "Plain Text")],
                )
            ]
        ```
    """

    multiple: bool = False
    enum: type[Enum] | None = None
    choices: Sequence[str] | Sequence[tuple[Any, str]] | None = None
    choices_loader: (
        Callable[[Request], Sequence[str] | Sequence[tuple[Any, str]]] | None
    ) = dc_field(default=None, compare=False)
    form_template: str = "fields/form/enum.html"
    class_: str = "form-control form-select"
    coerce: Callable[[Any], Any] = str
    select2: bool | None = None

    def __post_init__(self) -> None:
        if self.select2 is None:
            self.select2 = self.multiple
        if self.choices and not isinstance(self.choices[0], (list, tuple)):
            choices = cast(
                "list[tuple[str, str]]", list(zip(self.choices, self.choices))
            )
            self.choices = choices
            _log.debug(
                "EnumField %r: plain-value list coerced to (value, label) pairs (%d choices)",
                self.name,
                len(choices),
            )
        elif self.enum:
            self.choices = [(e.value, e.name.replace("_", " ")) for e in self.enum]
            self.coerce = int if issubclass(self.enum, IntEnum) else str
            _log.debug(
                "EnumField %r: built from enum %s (%d choices, coerce=%s)",
                self.name,
                self.enum.__name__,
                len(self.choices),
                self.coerce.__name__,
            )
        elif not self.choices and self.choices_loader is None:
            _log.error(
                "EnumField %r: no choices, enum, or choices_loader provided; field is unusable",
                self.name,
            )
            raise ValueError(
                "EnumField required a list of choices, enum class or a choices_loader for dynamic choices"
            )
        elif self.choices_loader is not None:
            _log.debug("EnumField %r: using dynamic choices_loader", self.name)
        super().__post_init__()

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        if self.multiple:
            raws = form_data.getlist(self.id)
            result: Any = list(map(self.coerce, raws))
            _log.debug(
                "EnumField.parse_form_data: field=%r multiple=True raw=%r -> %r",
                self.name,
                raws,
                result,
            )
        else:
            raw = form_data.get(self.id)
            result = self.coerce(raw) if raw else None
            _log.debug(
                "EnumField.parse_form_data: field=%r raw=%r -> %r",
                self.name,
                raw,
                result,
            )
        return result

    def _get_choices(self, request: Request) -> Any:
        return (
            self.choices
            if self.choices_loader is None
            else self.choices_loader(request)
        )

    def _get_label(self, value: Any, request: Request) -> Any:
        for v, label in self._get_choices(request):
            if value == v:
                return label
        _log.warning(
            "EnumField._get_label: field=%r value=%r not found in choices",
            self.name,
            value,
        )
        raise ValueError(f"Invalid choice value: {value}")

    async def serialize_value(self, request: Request, value: Any) -> Any:
        action = request.state.action
        _log.debug(
            "EnumField.serialize_value: field=%r action=%s value=%r",
            self.name,
            action,
            value,
        )
        if isinstance(value, Enum):
            value = value.value
        labels = [
            (
                self._get_label(v, request)
                if not (action.is_form() or action == RequestAction.EXPORT)
                else v
            )
            for v in (value if self.multiple else [value])
        ]
        result = labels if self.multiple else labels[0]
        _log.debug(
            "EnumField.serialize_value: field=%r -> %r",
            self.name,
            result,
        )
        return result

    async def get_create_default(self, request: Request) -> Any:
        """Coerce the configured default to raw choice value(s)."""
        value = await super().get_create_default(request)
        if isinstance(value, Enum):
            value = value.value
        if self.multiple and isinstance(value, (list, tuple)):
            return [self.coerce(v) for v in value]
        if value is not None:
            return self.coerce(value)
        return value

    def additional_css_links(self, request: Request) -> list[str]:
        if self.select2 and self._needs_form_assets(request):
            return [static_url(request, "css/vendor/select2.min.css", v="4.1.0")]
        return []

    def additional_js_links(self, request: Request) -> list[str]:
        if self.select2 and self._needs_form_assets(request):
            return [static_url(request, "js/vendor/select2.min.js", v="4.1.0")]
        return []


@dataclass
class TimeZoneField(EnumField):
    """This field is used to represent the name of a timezone (eg. Africa/Porto-Novo)"""

    def __post_init__(self) -> None:
        if self.choices is None:
            self.choices = [
                (self.coerce(x), x.replace("_", " ")) for x in common_timezones
            ]
        super().__post_init__()


@dataclass
class CountryField(EnumField):
    """This field is used to represent the name that corresponds to the country code stored in your database"""

    def __post_init__(self) -> None:
        try:
            import babel  # noqa
        except ImportError as err:  # pragma: no cover
            raise ImportError(  # pragma: no cover
                "'babel' package is required to use 'CountryField'. Install it with `pip install starlette-admin[i18n]`"
            ) from err
        self.choices_loader = lambda request: get_countries_list()
        super().__post_init__()


@dataclass
class CurrencyField(EnumField):
    """
    This field represents a value that stores the
    [3-letter ISO 4217](https://en.wikipedia.org/wiki/ISO_4217) currency code.
    """

    def __post_init__(self) -> None:
        try:
            import babel  # noqa
        except ImportError as err:  # pragma: no cover
            raise ImportError(  # pragma: no cover
                "'babel' package is required to use 'CurrencyField'. Install it with `pip install starlette-admin[i18n]`"
            ) from err
        self.choices_loader = lambda request: get_currencies_list()
        super().__post_init__()


@dataclass
class DateTimeField(NumberField):
    """
    This field represents a `datetime.datetime` object.

    Parameters:
        search_format: The moment.js format to use for searching. Use `None` for ISO format.
        output_format: The format for displaying the output.
    """

    input_type: str = "datetime-local"
    class_: str = "field-datetime form-control"
    output_format: str | None = None
    search_format: str | None = None
    form_alt_format: str | None = "F j, Y  H:i:S"

    def input_params(self) -> str:
        return html_params(
            {
                "type": self.input_type,
                "min": self.min,
                "max": self.max,
                "step": self.step,
                "data_alt_format": self.form_alt_format,
                "data_locale": get_locale(),
                "placeholder": self.placeholder,
                "required": self.required,
                "disabled": self.disabled,
                "readonly": self.read_only,
            }
        )

    async def parse_form_data(
        self, request: Request, form_data: FormData
    ) -> datetime | None:
        raw = form_data.get(self.id)
        _log.debug(
            "DateTimeField.parse_form_data: field=%r raw=%r",
            self.name,
            raw,
        )
        try:
            dt = datetime.fromisoformat(raw)  # type: ignore
        except (TypeError, ValueError):
            _log.warning(
                "DateTimeField.parse_form_data: field=%r cannot parse %r as ISO datetime; returning None",
                self.name,
                raw,
            )
            return None

        # Preserves pre-timezone conversion behavior.
        if not is_timezone_conversion_enabled():
            _log.debug(
                "DateTimeField.parse_form_data: field=%r tz conversion disabled -> %r",
                self.name,
                dt,
            )
            return dt

        database_tz = get_database_tzinfo()
        if dt.tzinfo is None:
            # Naive datetime (e.g. from a datetime-local form input), assumed to be in the user's timezone.
            user_tz = get_tzinfo()
            dt = dt.replace(tzinfo=user_tz)
        result = dt.astimezone(database_tz).replace(tzinfo=None)
        _log.debug(
            "DateTimeField.parse_form_data: field=%r tz-converted %r (db_tz=%s) -> %r",
            self.name,
            dt,
            database_tz,
            result,
        )
        return result

    async def serialize_value(self, request: Request, value: Any) -> str:
        assert isinstance(value, datetime), f"Expected datetime, got {type(value)}"
        action = request.state.action
        _log.debug(
            "DateTimeField.serialize_value: field=%r action=%s value=%r tzinfo=%s",
            self.name,
            action,
            value,
            value.tzinfo,
        )

        if action == RequestAction.EXPORT:
            if is_timezone_conversion_enabled():
                if value.tzinfo is None:
                    value = value.replace(tzinfo=get_database_tzinfo())
                return value.astimezone(UTC).isoformat()
            return value.isoformat()

        # Preserves pre-timezone conversion behavior.
        if not is_timezone_conversion_enabled():
            if not action.is_form():
                result = format_datetime(value, self.output_format)
                _log.debug(
                    "DateTimeField.serialize_value: field=%r (tz disabled, display) -> %r",
                    self.name,
                    result,
                )
                return result
            result = value.isoformat()
            _log.debug(
                "DateTimeField.serialize_value: field=%r (tz disabled, edit) -> %r",
                self.name,
                result,
            )
            return result

        user_tz = get_tzinfo()

        if value.tzinfo is None:
            # Native datetime from the database, assumed to be in the database's timezone.
            database_tz = get_database_tzinfo()
            value = value.replace(tzinfo=database_tz)
            _log.debug(
                "DateTimeField.serialize_value: field=%r naive datetime assumed db_tz=%s",
                self.name,
                database_tz,
            )

        if not action.is_form():
            result = format_datetime(value, self.output_format, user_tz)
            _log.debug(
                "DateTimeField.serialize_value: field=%r (display, user_tz=%s) -> %r",
                self.name,
                user_tz,
                result,
            )
            return result

        # For form actions, convert to the user's timezone and return as a naive datetime for `datetime-local` input.
        converted_value = value.astimezone(user_tz)
        result = converted_value.replace(tzinfo=None).isoformat()
        _log.debug(
            "DateTimeField.serialize_value: field=%r (edit, user_tz=%s) -> %r",
            self.name,
            user_tz,
            result,
        )
        return result

    def additional_css_links(self, request: Request) -> list[str]:
        if self._needs_form_assets(request):
            return [static_url(request, "css/vendor/flatpickr.min.css", v="4.6.13")]
        return []

    def additional_js_links(self, request: Request) -> list[str]:
        _links = [static_url(request, "js/vendor/flatpickr.min.js", v="4.6.13")]
        if get_locale() != "en":
            _links.append(
                static_url(request, f"i18n/flatpickr/{get_locale()}.js", v="4.6.13")
            )
        if self._needs_form_assets(request):
            return _links
        return []


@dataclass
class DateField(DateTimeField):
    """
    This field represents a `datetime.date` object.

    Parameters:
        search_format: The moment.js format to use for searching. Use `None` for ISO format.
        output_format: Sets the display output format.
    """

    input_type: str = "date"
    class_: str = "field-date form-control"
    output_format: str | None = None
    search_format: str = "YYYY-MM-DD"
    form_alt_format: str | None = "F j, Y"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        raw = form_data.get(self.id)
        try:
            result = date.fromisoformat(raw)  # type: ignore
            _log.debug(
                "DateField.parse_form_data: field=%r raw=%r -> %r",
                self.name,
                raw,
                result,
            )
            return result
        except (TypeError, ValueError):
            _log.warning(
                "DateField.parse_form_data: field=%r cannot parse %r as ISO date; returning None",
                self.name,
                raw,
            )
            return None

    async def serialize_value(self, request: Request, value: Any) -> str:
        assert isinstance(value, date), f"Expect date, got  {type(value)}"
        action = request.state.action
        if action == RequestAction.EXPORT:
            return value.isoformat()
        if not action.is_form():
            result = format_date(value, self.output_format)
            _log.debug(
                "DateField.serialize_value: field=%r action=%s -> %r",
                self.name,
                action,
                result,
            )
            return result
        result = value.isoformat()
        _log.debug(
            "DateField.serialize_value: field=%r action=EDIT -> %r",
            self.name,
            result,
        )
        return result


@dataclass
class TimeField(DateTimeField):
    """
    This field represents a `datetime.time` object.

    Parameters:
        search_format: The format to use for searching. Use `None` for ISO format.
        output_format: Sets the display output format.
    """

    input_type: str = "time"
    class_: str = "field-time form-control"
    output_format: str | None = None
    search_format: str = "HH:mm:ss"
    form_alt_format: str | None = "H:i:S"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        raw = form_data.get(self.id)
        try:
            result = time.fromisoformat(raw)  # type: ignore
            _log.debug(
                "TimeField.parse_form_data: field=%r raw=%r -> %r",
                self.name,
                raw,
                result,
            )
            return result
        except (TypeError, ValueError):
            _log.warning(
                "TimeField.parse_form_data: field=%r cannot parse %r as ISO time; returning None",
                self.name,
                raw,
            )
            return None

    async def serialize_value(self, request: Request, value: Any) -> str:
        assert isinstance(value, time), f"Expect time, got  {type(value)}"
        action = request.state.action
        if not action.is_form():
            result = format_time(value, self.output_format)
            _log.debug(
                "TimeField.serialize_value: field=%r action=%s -> %r",
                self.name,
                action,
                result,
            )
            return result
        result = value.isoformat()
        _log.debug(
            "TimeField.serialize_value: field=%r action=EDIT -> %r",
            self.name,
            result,
        )
        return result


@dataclass
class ArrowField(DateTimeField):
    """
    This field represents a `sqlalchemy_utils.types.arrow.ArrowType`.
    """

    def __post_init__(self) -> None:
        if not arrow:  # pragma: no cover
            raise ImportError("'arrow' package is required to use 'ArrowField'")
        super().__post_init__()

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        raw = form_data.get(self.id)
        _log.debug("ArrowField.parse_form_data: field=%r raw=%r", self.name, raw)
        # Preserves pre-timezone conversion behavior.
        if not is_timezone_conversion_enabled():
            try:
                result = arrow.get(raw)  # type: ignore
                _log.debug(
                    "ArrowField.parse_form_data: field=%r (tz disabled) -> %r",
                    self.name,
                    result,
                )
                return result
            except (TypeError, arrow.parser.ParserError):  # pragma: no cover
                _log.warning(
                    "ArrowField.parse_form_data: field=%r cannot parse %r; returning None",
                    self.name,
                    raw,
                )
                return None

        dt = await super().parse_form_data(request, form_data)
        if dt is None:
            return None
        result = arrow.get(dt)
        _log.debug(
            "ArrowField.parse_form_data: field=%r tz-converted -> %r",
            self.name,
            result,
        )
        return result

    async def serialize_value(self, request: Request, value: Any) -> str:
        assert isinstance(value, arrow.Arrow), f"Expected Arrow, got  {type(value)}"
        action = request.state.action
        _log.debug(
            "ArrowField.serialize_value: field=%r action=%s value=%r",
            self.name,
            action,
            value,
        )

        # Preserves pre-timezone conversion behavior.
        if not is_timezone_conversion_enabled():
            if not action.is_form():
                result = value.humanize(locale=get_locale())
                _log.debug(
                    "ArrowField.serialize_value: field=%r (tz disabled, display) -> %r",
                    self.name,
                    result,
                )
                return result
            result = value.isoformat()
            _log.debug(
                "ArrowField.serialize_value: field=%r (tz disabled, edit) -> %r",
                self.name,
                result,
            )
            return result

        if not action.is_form():
            user_tz = get_tzinfo()
            result = value.to(user_tz).humanize(locale=get_locale())
            _log.debug(
                "ArrowField.serialize_value: field=%r (display, user_tz=%s) -> %r",
                self.name,
                user_tz,
                result,
            )
            return result

        return await super().serialize_value(request, value.datetime)


@dataclass
class JSONField(BaseField):
    """
    This field renders a JSON editor and represents a Python `dict` object.
    Erroneous input is ignored and will not be accepted.

    You may optionally use the `validation_schema` property to provide a dictionary with
    a [JSONSchema](https://json-schema.org/) for client-side validation feedback.

    The read-only viewer (for list/detail views) can be configured with `viewer_collapsed`
    (renders collapsed on load), `viewer_with_quotes` (quotes object keys),
    `viewer_with_links` (renders string values that resemble URLs as clickable
    links), and `viewer_root_collapsable` (shows a toggle to collapse/expand the
    root value itself)."""

    height: str = "20em"
    modes: Sequence[str] | None = None
    validation_schema: dict[str, Any] | None = None
    list_template: str = "fields/list/json.html"
    form_template: str = "fields/form/json.html"
    detail_template: str = "fields/detail/json.html"

    viewer_collapsed: bool = True
    viewer_with_quotes: bool = True
    viewer_with_links: bool = False
    viewer_root_collapsable: bool = False

    def __post_init__(self) -> None:
        if self.modes is None:
            self.modes = ["view"] if self.read_only else ["tree", "code"]
        super().__post_init__()

    async def parse_form_data(
        self, request: Request, form_data: FormData
    ) -> dict[str, Any] | None:
        raw = form_data.get(self.id)
        _log.debug(
            "JSONField.parse_form_data: field=%r raw_len=%s",
            self.name,
            len(raw) if isinstance(raw, str) else 0,
        )
        if raw is None:
            return None
        try:
            result = json.loads(raw)  # type: ignore
            _log.debug(
                "JSONField.parse_form_data: field=%r parsed type=%s",
                self.name,
                type(result).__name__,
            )
            return result
        except JSONDecodeError as exc:
            _log.warning(
                "JSONField.parse_form_data: field=%r JSON decode error at pos %d; returning None",
                self.name,
                exc.pos,
            )
            return None

    def additional_css_links(self, request: Request) -> list[str]:
        if self._needs_form_assets(request):
            return [
                static_url(request, "css/vendor/jsoneditor.min.css", v="10.4.3"),
                static_url(request, "css/jsoneditor_overrides.css", v=1),
            ]
        return [static_url(request, "css/vendor/jquery.json-viewer.css", v="1.5.0")]

    def additional_js_links(self, request: Request) -> list[str]:
        if self._needs_form_assets(request):
            return [static_url(request, "js/vendor/jsoneditor.min.js", v="10.4.3")]
        return [static_url(request, "js/vendor/jquery.json-viewer.js", v="1.5.0")]


@dataclass
class FileField(BaseField):
    """
    Renders a file upload field.

    When a [storage][starlette_admin.storage.BaseStorage] is attached, uploads
    are saved through it by the admin. The database column only stores
    the JSON metadata dictionary of a [FileInfo][starlette_admin.storage.FileInfo].

    Without a storage, this field retains its legacy behavior: it represents a
    value that stores a Starlette `UploadFile` object. `parse_form_data`
    returns the raw `(upload(s), should_be_deleted)` tuple for the backend to
    process itself. For displaying values, this field expects three
    properties: `filename`, `content-type`, and `url`.

    Use `multiple=True` for multiple file uploads.
    When a user requests deletion on the editing page, the second part of the returned tuple is `True`.

    Parameters:
        accept: Comma-separated accepted file specifiers (e.g., `".pdf"`,
            `"image/*"`, `"image/png,.svg"`). Enforced server-side by `validate`
            and passed to the file input.
        multiple: Allows uploading (and storing) several files.
        storage: The storage backend to which uploads are delegated.
        upload_folder: The storage-relative folder where uploads for this field are saved.
        max_size: The maximum accepted upload size, in bytes (default: 50 MB).
            Set to `None` to disable the cap.
        validators: Additional validators executed after the built-in
            `accept`/`max_size` checks. Unlike other fields, each validator
            receives a single `UploadFile` as its value and runs once per
            uploaded file. `ImageField` automatically prepends
            [valid_image][starlette_admin.validators.valid_image] here.

    File fields are always excluded from import (`exclude_from_import` defaults
    to `True`): there is no way to reference an uploaded file's bytes from a
    CSV/Excel/JSON row, so the column is left for the backend to populate
    through the normal create/edit forms instead.
    """

    accept: str | None = None
    multiple: bool = False
    storage: BaseStorage | None = None
    upload_folder: str = ""
    max_size: int | None = DEFAULT_MAX_UPLOAD_SIZE
    exclude_from_import: bool | None = True
    list_template: str = "fields/list/file.html"
    form_template: str = "fields/form/file.html"
    detail_template: str = "fields/detail/file.html"

    async def parse_form_data(
        self, request: Request, form_data: FormData
    ) -> tuple[UploadFile | list[UploadFile] | None, bool]:
        should_be_deleted = form_data.get(f"_{self.id}-delete") == "on"
        _log.debug(
            "FileField.parse_form_data: field=%r multiple=%r should_be_deleted=%r",
            self.name,
            self.multiple,
            should_be_deleted,
        )
        if self.multiple:
            # `getlist` is typed to also allow plain str values (form fields
            # in general can be text), but this field only ever submits files.
            files = form_data.getlist(self.id)
            non_empty = [
                f
                for f in files
                if not is_empty_file(f.file)  # ty: ignore[unresolved-attribute]
            ]
            _log.debug(
                "FileField.parse_form_data: field=%r %d/%d files non-empty",
                self.name,
                len(non_empty),
                len(files),
            )
            return non_empty, should_be_deleted  # ty: ignore[invalid-return-type]
        file = form_data.get(self.id)
        result = (
            None
            if (file and is_empty_file(file.file))  # ty: ignore[unresolved-attribute]
            else file
        )
        _log.debug(
            "FileField.parse_form_data: field=%r file=%r (empty=%r)",
            self.name,
            getattr(file, "filename", file),
            result is None and file is not None,
        )
        return result, should_be_deleted  # ty: ignore[invalid-return-type]

    async def serialize_value(self, request: Request, value: Any) -> Any:
        _log.debug(
            "FileField.serialize_value: field=%r multiple=%r value_type=%s",
            self.name,
            self.multiple,
            type(value).__name__,
        )
        if self.multiple and isinstance(value, (list, tuple)):
            return [await self._serialize_file_value(request, v) for v in value]
        return await self._serialize_file_value(request, value)

    async def _serialize_file_value(self, request: Request, value: Any) -> Any:
        """Refreshes the public URL of a stored `FileInfo` dictionary on render. URLs (whether signed or admin-served) are never trusted from the database. Any other value shape (e.g., SQLAlchemy-file objects exposing `.url`) passes through unchanged."""
        if isinstance(value, FileInfo):
            value = value.to_dict()
        if isinstance(value, dict) and value.get("storage") and value.get("key"):
            storage_name = value["storage"]
            key = value["key"]
            try:
                storage = get_storage(storage_name)
            except UnknownStorageError:
                _log.warning(
                    "FileField._serialize_file_value: field=%r unknown storage %r for key=%r; skipping URL refresh",
                    self.name,
                    storage_name,
                    key,
                )
                return value
            url = await storage.url(request, key)
            result = {**value, "url": url}
            thumbnail = value.get("thumbnail")
            if isinstance(thumbnail, dict) and thumbnail.get("key"):
                result["thumbnail_url"] = await storage.url(request, thumbnail["key"])
            _log.debug(
                "FileField._serialize_file_value: field=%r storage=%r key=%r url refreshed",
                self.name,
                storage_name,
                key,
            )
            return result
        _log.debug(
            "FileField._serialize_file_value: field=%r value_type=%s passed through unchanged",
            self.name,
            type(value).__name__,
        )
        return value

    async def validate(
        self, request: Request, value: Any, form_values: dict[str, Any]
    ) -> None:
        """Validates each uploaded file in the parsed ``(upload(s), should_be_deleted)``
        tuple against `accept`, `max_size`, and the custom `validators`, raising
        `ValueError` upon the first failure encountered.

        The base `required` check does not apply: an empty submission on an
        edit form means "keep the current file", which this field cannot
        distinguish from a missing value.
        """
        uploads, _delete = value
        if uploads is None:
            return
        chain: list[Validator] = []
        if self.max_size is not None:
            chain.append(file_size(self.max_size))
        if self.accept is not None:
            chain.append(file_type(self.accept))
        chain.extend(self.validators)
        for upload in uploads if self.multiple else [uploads]:
            try:
                await self._run_validators(request, chain, upload, form_values)
            except ValueError as error:
                _log.warning(
                    "FileField %r: upload rejected: %s (filename=%r content_type=%r)",
                    self.name,
                    error,
                    upload.filename,
                    upload.content_type,
                )
                raise
            _log.debug(
                "FileField %r: upload accepted (filename=%r size=%r bytes)",
                self.name,
                upload.filename,
                upload.size,
            )

    def _enrich_file_info(self, info: "FileInfo", upload: UploadFile) -> "FileInfo":
        """A hook to complete the `FileInfo` returned by `BaseStorage.save` with
        field-specific metadata (e.g., image dimensions; see `ImageField`).
        """
        return info

    async def _post_store(self, info: "FileInfo", upload: UploadFile) -> "FileInfo":
        """An async hook, run once per upload right after `BaseStorage.save`,
        for field-specific work that itself needs storage access (via
        `self.storage`; e.g. generating and saving a thumbnail, see
        `ImageField`). Defaults to the synchronous `_enrich_file_info` hook.
        """
        return self._enrich_file_info(info, upload)

    def _isvalid_value(self, value: Any) -> bool:
        items = value if self.multiple else [value]
        return bool(items) and all(
            hasattr(v, "url") or (isinstance(v, dict) and v.get("url") is not None)
            for v in items
        )

    def input_params(self) -> str:
        return html_params(
            {
                "accept": self.accept,
                "disabled": self.disabled,
                "readonly": self.read_only,
                "multiple": self.multiple,
            }
        )


# Pillow's `Image.format` doesn't always match the conventional file extension
# (JPEG images report format "JPEG", not "JPG"); this maps the formats where
# they differ so thumbnail keys read naturally.
_IMAGE_FORMAT_EXTENSIONS = {"JPEG": "jpg"}


@dataclass
class ImageField(FileField):
    """
    A `FileField` with `accept="image/*"`. When a storage is attached and Pillow is
    installed, the image dimensions (`width`/`height`) are automatically added to the stored
    metadata.

    [valid_image][starlette_admin.validators.valid_image] is automatically prepended
    to `validators` to ensure every upload is a valid image before storage. Override
    `__post_init__` (or `validate`) to opt out of this behavior.

    Parameters:
        thumbnail_size: When set (and a storage is attached), a thumbnail bounded
            to `(width, height)` is generated with Pillow at save time and
            recorded in the stored metadata alongside the full image. Aspect
            ratio is preserved and the thumbnail is never upscaled. A failure
            to generate the thumbnail never fails the upload; the field simply
            falls back to the full image. Ignored when Pillow isn't installed
            or no storage is attached.

    The detail page renders every `ImageField` image inside an
    [fslightbox](https://fslightbox.com/) anchor, grouped into one gallery per
    field, so visitors can click through to a full-size, navigable view.
    """

    accept: str | None = "image/*"
    thumbnail_size: tuple[int, int] | None = None
    list_template: str = "fields/list/image.html"
    form_template: str = "fields/form/image.html"
    detail_template: str = "fields/detail/image.html"

    def __post_init__(self) -> None:
        super().__post_init__()
        self.validators = [valid_image(), *self.validators]
        _log.debug(
            "ImageField %r: initialized (accept=%r validators=%d)",
            self.name,
            self.accept,
            len(self.validators),
        )

    def _enrich_file_info(self, info: FileInfo, upload: UploadFile) -> FileInfo:
        from PIL import Image

        try:
            upload.file.seek(0)
            with Image.open(upload.file) as image:
                width, height = image.size
        except Exception:  # Not parseable as an image.
            return info
        finally:
            upload.file.seek(0)
        return replace(info, width=width, height=height)

    async def _post_store(self, info: FileInfo, upload: UploadFile) -> FileInfo:
        info = await super()._post_store(info, upload)
        if self.thumbnail_size is None:
            return info
        try:
            thumbnail = await self._save_thumbnail(info, upload)
        except Exception:
            _log.warning(
                "ImageField %r: thumbnail generation failed for key=%r; falling back"
                " to the full image",
                self.name,
                info.key,
                exc_info=True,
            )
            return info
        return replace(info, thumbnail=thumbnail)

    async def _save_thumbnail(
        self, info: FileInfo, upload: UploadFile
    ) -> dict[str, Any]:
        """Builds a thumbnail bounded to `thumbnail_size` from `upload` and
        saves it next to the main file, under a `.thumb` suffix inserted
        before the extension (e.g. `photos/cat.jpg` -> `photos/cat.thumb.jpg`).
        """
        from PIL import Image

        try:
            upload.file.seek(0)
            with Image.open(upload.file) as source:
                source_format = source.format or "PNG"
                thumbnail = source.copy()
        finally:
            upload.file.seek(0)
        thumbnail.thumbnail(not_none(self.thumbnail_size))
        if source_format in ("JPEG", "JPG") and thumbnail.mode in ("P", "RGBA"):
            thumbnail = thumbnail.convert("RGB")
        buffer = io.BytesIO()
        try:
            thumbnail.save(buffer, format=source_format)
        except (OSError, KeyError):
            source_format = "PNG"
            buffer = io.BytesIO()
            thumbnail.save(buffer, format=source_format)
        content = buffer.getvalue()
        ext = _IMAGE_FORMAT_EXTENSIONS.get(source_format, source_format.lower())
        stem = info.key.rsplit(".", 1)[0] if "." in info.key else info.key
        thumbnail_dest = f"{stem}.thumb.{ext}"
        thumbnail_upload = UploadFile(
            io.BytesIO(content),
            size=len(content),
            filename=thumbnail_dest.rsplit("/", 1)[-1],
            headers=Headers({"content-type": f"image/{ext}"}),
        )
        thumbnail_info = await not_none(self.storage).save(
            thumbnail_upload, thumbnail_dest
        )
        width, height = thumbnail.size
        return {
            "key": thumbnail_info.key,
            "width": width,
            "height": height,
            "size": thumbnail_info.size,
        }

    def additional_js_links(self, request: Request) -> list[str]:
        if request.state.action == RequestAction.DETAIL:
            return [static_url(request, "js/vendor/fslightbox.js", v="3.7.5")]
        return []


@dataclass
class RelationField(BaseField):
    """
    A field representing a relation between two data models.

    This field should not be used directly. Instead, use either the [HasOne][starlette_admin.fields.HasOne]
    or [HasMany][starlette_admin.fields.HasMany] fields to specify a relation
    between your models.

    !!! important

        It is important to add both models to your admin interface.

    Parameters:
        key: The key of the foreign ModelView.


    ??? Example

        ```py
        class Author:
            id: Optional[int]
            name: str
            books: List["Book"]

        class Book:
            id: Optional[int]
            title: str
            author: Optional["Author"]

        class AuthorView(ModelView):
            fields = [
                IntegerField("id"),
                StringField("name"),
                HasMany("books", key="book"),
            ]

        class BookView(ModelView):
            fields = [
                IntegerField("id"),
                StringField("title"),
                HasOne("author", key="author"),
            ]
        ...
        admin.add_view(AuthorView(Author, key="author"))
        admin.add_view(BookView(Book, key="book"))
        ...
        ```
    """

    key: str | None = None
    multiple: bool = False
    list_template: str = "fields/list/relation.html"
    form_template: str = "fields/form/relation.html"
    detail_template: str = "fields/detail/relation.html"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        if self.multiple:
            result: Any = form_data.getlist(self.id)
            _log.debug(
                "RelationField.parse_form_data: field=%r multiple=True -> %d pk(s) %r",
                self.name,
                len(result),
                result,
            )
            return result
        result = form_data.get(self.id)
        _log.debug(
            "RelationField.parse_form_data: field=%r single -> pk=%r",
            self.name,
            result,
        )
        return result

    async def serialize_value(self, request: Request, value: Any) -> Any:
        if self._view is None:
            _log.error(
                "RelationField %r has no _view; it must be used inside a BaseModelView",
                self.name,
            )
            raise RuntimeError(
                f"RelationField {self.name!r} has no _view; it must be used "
                "inside a BaseModelView (set during BaseModelView.__init__)"
            )
        foreign_view = self._view._find_foreign_view(not_none(self.key))
        action = request.state.action
        _log.debug(
            "RelationField.serialize_value: field=%r key=%r action=%s multiple=%r",
            self.name,
            self.key,
            action,
            self.multiple,
        )
        if self.multiple:
            if action.is_form():
                result: Any = [
                    await foreign_view.get_serialized_pk_value(request, v)
                    for v in value
                ]
                _log.debug(
                    "RelationField.serialize_value: field=%r form -> %d pk(s)",
                    self.name,
                    len(result),
                )
                return result
            if action == RequestAction.EXPORT:
                pks = [
                    str(await foreign_view.get_serialized_pk_value(request, v))
                    for v in value
                ]
                if (
                    getattr(
                        getattr(request.state, "export_type", None), "extension", None
                    )
                    == "json"
                ):
                    _log.debug(
                        "RelationField.serialize_value: field=%r EXPORT JSON -> %d pk(s)",
                        self.name,
                        len(pks),
                    )
                    return pks
                result = "\n".join(pks)
                _log.debug(
                    "RelationField.serialize_value: field=%r EXPORT text -> %r",
                    self.name,
                    result,
                )
                return result
            result = [
                await foreign_view.serialize(v, request, include_relationships=False)
                for v in value
            ]
            _log.debug(
                "RelationField.serialize_value: field=%r LIST -> %d serialized item(s)",
                self.name,
                len(result),
            )
            return result
        if action.is_form() or action == RequestAction.EXPORT:
            result = await foreign_view.get_serialized_pk_value(request, value)
            _log.debug(
                "RelationField.serialize_value: field=%r %s -> pk=%r",
                self.name,
                action,
                result,
            )
            return result
        result = await foreign_view.serialize(
            value, request, include_relationships=False
        )
        _log.debug(
            "RelationField.serialize_value: field=%r LIST single -> serialized",
            self.name,
        )
        return result

    async def parse_import_value(self, request: Request, value: Any) -> Any:
        _log.debug(
            "RelationField.parse_import_value: field=%r multiple=%r raw_type=%s raw=%r",
            self.name,
            self.multiple,
            type(value).__name__,
            value,
        )
        if self.multiple:
            if isinstance(value, str):
                pks = [v.strip() for v in value.split("\n") if v.strip()]
            elif isinstance(value, list):
                pks = [str(v) for v in value if v is not None]
            elif value is None:
                pks = []
            else:
                pks = [str(value)]
            _log.debug(
                "RelationField.parse_import_value: field=%r parsed %d pk(s)",
                self.name,
                len(pks),
            )
            form_data = FormData([(self.id, pk) for pk in pks])
        else:
            if value is None or value == "":
                _log.debug(
                    "RelationField.parse_import_value: field=%r empty value",
                    self.name,
                )
                form_data = FormData([])
            else:
                form_data = FormData([(self.id, str(value))])
        return await self.parse_form_data(request, form_data)

    def additional_css_links(self, request: Request) -> list[str]:
        if self._needs_form_assets(request):
            return [static_url(request, "css/vendor/select2.min.css", v="4.1.0")]
        return []

    def additional_js_links(self, request: Request) -> list[str]:
        if self._needs_form_assets(request):
            return [static_url(request, "js/vendor/select2.min.js", v="4.1.0")]
        return []


@dataclass
class HasOne(RelationField):
    """
    A field representing a "has-one" relation between two models.
    """


@dataclass
class HasMany(RelationField):
    """A field representing a "has-many" relationship between two models."""

    multiple: bool = True
    collection_class: type[Collection[Any]] | Callable[[], Collection[Any]] = list


@dataclass(init=False)
class CollectionField(BaseField):
    """
    This field represents a collection of other fields. It can be used to represent an embedded MongoDB document.

    !!! usage

    ```python
     CollectionField("config", fields=[StringField("key"), IntegerField("value", help_text="multiple of 5")]),
    ```

    Parameters:
        name: See [BaseField.name][starlette_admin.fields.BaseField].
        fields: The sub-fields that make up this collection.
        required: If `True`, at least one sub-field value is required.
        validators: Validators run against the parsed collection value (a `dict`).
        getter: See [BaseField.getter][starlette_admin.fields.BaseField].
        formatter: See [BaseField.formatter][starlette_admin.fields.BaseField].
        parser: See [BaseField.parser][starlette_admin.fields.BaseField]. Its
            callable receives the full `FormData` (for CREATE, EDIT,
            INLINE_EDIT) or the raw import cell value (for IMPORT), matching
            what [parse_form_data][starlette_admin.fields.CollectionField.parse_form_data]
            itself receives, since a collection's sub-fields are keyed by
            dotted id (`self.id.<subfield>`) rather than living under a
            single `self.id` key.
    """

    fields: Sequence[BaseField] = dc_field(default_factory=list)
    list_template: str = "fields/list/collection.html"
    form_template: str = "fields/form/collection.html"
    detail_template: str = "fields/detail/collection.html"

    def __init__(
        self,
        name: str,
        fields: Sequence[BaseField],
        required: bool = False,
        validators: list[Validator] | None = None,
        getter: Getter | None = None,
        formatter: dict[RequestAction, Formatter] | None = None,
        parser: dict[RequestAction, Parser] | None = None,
    ) -> None:
        self.name = name
        self.fields = fields
        self.required = required
        self.validators = validators or []
        self.getter = getter
        self.formatter = formatter
        self.parser = parser
        super().__post_init__()
        self._propagate_id()
        _log.debug(
            "CollectionField %r: initialized with %d sub-field(s): %s",
            self.name,
            len(self.fields),
            [f.name for f in self.fields],
        )

    async def parse_input(self, request: Request, raw: Any) -> Any:
        """Overrides [BaseField.parse_input][starlette_admin.fields.BaseField.parse_input]
        because a collection's sub-fields are keyed by dotted id
        (`self.id.<subfield>`) rather than living under a single `self.id`
        key, so the base implementation's `raw.get(self.id)` extraction does
        not apply. For CREATE, EDIT, and INLINE_EDIT, when `self.parser` has
        an entry for the current action, the full `FormData` is passed to it
        unchanged, mirroring what
        [parse_form_data][starlette_admin.fields.CollectionField.parse_form_data]
        itself receives.
        """
        action = request.state.action
        parser = (self.parser or {}).get(action)
        if action == RequestAction.IMPORT:
            if parser is not None:
                return await maybe_async(parser(request, raw))
            return await self.parse_import_value(request, raw)
        if parser is not None:
            return await maybe_async(parser(request, raw))
        return await self.parse_form_data(request, raw)

    def get_fields_list(
        self, request: Request, *, action: RequestAction | None = None
    ) -> Sequence[BaseField]:
        view = self._view
        if view is None:  # pragma: no cover
            raise RuntimeError(
                f"CollectionField {self.name!r} has no _view; it must be used "
                "inside a BaseModelView (set during BaseModelView.__init__)"
            )
        return [
            f for f in self.fields if view.can_access_field(request, f, action=action)
        ]

    def _propagate_id(self) -> None:
        """Updates field IDs by adding their own ID as a prefix (e.g., `category.name`)."""
        for field in self.fields:
            field.id = self.id + ("." if self.id else "") + field.name
            if isinstance(field, type(self)):
                field._propagate_id()

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        _log.debug(
            "CollectionField.parse_form_data: field=%r parsing %d sub-field(s)",
            self.name,
            len(self.fields),
        )
        value = {}
        for field in self.get_fields_list(request):
            if field.read_only:
                continue
            value[field.name] = await field.parse_form_data(request, form_data)
        _log.debug(
            "CollectionField.parse_form_data: field=%r -> keys=%s",
            self.name,
            list(value.keys()),
        )
        return value

    async def serialize_value(self, request: Request, value: Any) -> Any:
        _log.debug(
            "CollectionField.serialize_value: field=%r action=%s value_type=%s",
            self.name,
            request.state.action,
            type(value).__name__,
        )
        serialized_value: dict[str, Any] = {}
        for field in self.get_fields_list(request):
            name = field.name
            serialized_value[name] = None
            if hasattr(value, name) or (isinstance(value, dict) and name in value):
                field_value = (
                    getattr(value, name) if hasattr(value, name) else value[name]
                )
                if field_value is not None:
                    serialized_value[name] = await field.serialize_value(
                        request, field_value
                    )
                else:
                    _log.debug(
                        "CollectionField.serialize_value: field=%r sub-field=%r is None; skipping",
                        self.name,
                        name,
                    )
            else:
                _log.debug(
                    "CollectionField.serialize_value: field=%r sub-field=%r not found on value; defaulting to None",
                    self.name,
                    name,
                )
        return serialized_value

    async def validate(
        self, request: Request, value: Any, form_values: dict[str, Any]
    ) -> None:
        """Extends [BaseField.validate][starlette_admin.fields.BaseField.validate]
        by also running each sub-field's own `validate` (its `required` check
        and `validators`) against its corresponding entry in `value`, after
        this field's own `validators` have passed. Sub-field failures are
        collected into a single `ValueError` carrying a `dict` keyed by
        sub-field name, matching the shape the form templates already know
        how to render.
        """
        await super().validate(request, value, form_values)
        if is_empty_value(value):
            return
        errors: dict[str, Any] = {}
        for field in self.get_fields_list(request):
            if field.read_only:
                continue
            name = field.name
            if isinstance(value, dict):
                field_value = value.get(name)
            else:
                field_value = getattr(value, name, None)
            try:
                await field.validate(request, field_value, form_values)
            except ValueError as exc:
                errors[field.name] = field_error_payload(exc)
        if errors:
            raise ValueError(errors)

    def additional_css_links(self, request: Request) -> list[str]:
        _links = []
        for f in self.get_fields_list(request):
            _links.extend(f.additional_css_links(request))
        return _links

    def additional_js_links(self, request: Request) -> list[str]:
        _links = []
        for f in self.get_fields_list(request):
            _links.extend(f.additional_js_links(request))
        return _links


@dataclass(init=False)
class ListField(BaseField):
    """
    Encapsulate an ordered list of multiple instances of the same field type,
    keeping data as a list.

    !!! usage

        ```python
        class MyModel:
            id: Optional[int]
            values: List[str]

        class ModelView(BaseModelView):
            fields = [IntegerField("id"), ListField(StringField("values")]
        ```

    Parameters:
        field: The field type repeated for each item in the list.
        required: If `True`, at least one item is required.
        validators: Validators run against the parsed list value.
        getter: See [BaseField.getter][starlette_admin.fields.BaseField].
        formatter: See [BaseField.formatter][starlette_admin.fields.BaseField].
        parser: See [BaseField.parser][starlette_admin.fields.BaseField]. Its
            callable receives the full `FormData` (for CREATE, EDIT,
            INLINE_EDIT) or the raw import cell value (for IMPORT), matching
            what [parse_form_data][starlette_admin.fields.ListField.parse_form_data]
            and [parse_import_value][starlette_admin.fields.BaseField.parse_import_value]
            themselves receive.
    """

    form_template: str = "fields/form/list.html"
    list_template: str = "fields/list/list.html"
    detail_template: str = "fields/detail/list.html"
    field: BaseField = dc_field(default_factory=lambda: BaseField(""))

    def __init__(
        self,
        field: BaseField,
        required: bool = False,
        validators: list[Validator] | None = None,
        getter: Getter | None = None,
        formatter: dict[RequestAction, Formatter] | None = None,
        parser: dict[RequestAction, Parser] | None = None,
    ) -> None:
        self.field = field
        self.name = field.name
        self.required = required
        self.validators = validators or []
        self.getter = getter
        self.formatter = formatter
        self.parser = parser
        self.__post_init__()

    def __post_init__(self) -> None:
        super().__post_init__()
        self.field.id = ""
        if isinstance(self.field, CollectionField):
            self.field._propagate_id()

    async def parse_input(self, request: Request, raw: Any) -> Any:
        """Overrides [BaseField.parse_input][starlette_admin.fields.BaseField.parse_input]
        because a list's items are keyed by index (`self.id.0`, `self.id.1`, ...)
        rather than living under a single `self.id` key, so the base
        implementation's `raw.get(self.id)` / `raw.getlist(self.id)` extraction
        does not apply. For CREATE, EDIT, and INLINE_EDIT, when `self.parser`
        has an entry for the current action, the full `FormData` is passed to
        it unchanged, mirroring what [parse_form_data][starlette_admin.fields.ListField.parse_form_data]
        itself receives.
        """
        action = request.state.action
        parser = (self.parser or {}).get(action)
        if action == RequestAction.IMPORT:
            if parser is not None:
                return await maybe_async(parser(request, raw))
            return await self.parse_import_value(request, raw)
        if parser is not None:
            return await maybe_async(parser(request, raw))
        return await self.parse_form_data(request, raw)

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        indices = self._extra_indices(form_data)
        _log.debug(
            "ListField.parse_form_data: field=%r found %d index(es) %s",
            self.name,
            len(indices),
            indices,
        )
        value = []
        for index in indices:
            self.field.id = f"{self.id}.{index}"
            if isinstance(self.field, CollectionField):
                self.field._propagate_id()
            item = await self.field.parse_form_data(request, form_data)
            _log.debug(
                "ListField.parse_form_data: field=%r index=%d -> %r",
                self.name,
                index,
                item,
            )
            value.append(item)
        _log.debug(
            "ListField.parse_form_data: field=%r result has %d item(s)",
            self.name,
            len(value),
        )
        return value

    async def serialize_value(self, request: Request, value: Any) -> Any:
        action = request.state.action
        _log.debug(
            "ListField.serialize_value: field=%r action=%s items=%d",
            self.name,
            action,
            len(value) if hasattr(value, "__len__") else -1,
        )
        serialized_value = []
        for idx, item in enumerate(value):
            serialized_item_value = None
            if item is not None:
                serialized_item_value = await self.field.serialize_value(request, item)
            else:
                _log.debug(
                    "ListField.serialize_value: field=%r item[%d] is None; keeping None",
                    self.name,
                    idx,
                )
            serialized_value.append(serialized_item_value)
        if action == RequestAction.EXPORT:
            if (
                getattr(getattr(request.state, "export_type", None), "extension", None)
                == "json"
            ):
                _log.debug(
                    "ListField.serialize_value: field=%r export JSON -> %d item(s)",
                    self.name,
                    len(serialized_value),
                )
                return serialized_value
            result = "\n".join(str(v) for v in serialized_value if v is not None)
            _log.debug(
                "ListField.serialize_value: field=%r export text -> %r",
                self.name,
                result,
            )
            return result
        return serialized_value

    async def parse_import_value(self, request: Request, value: Any) -> list[Any]:
        _log.debug(
            "ListField.parse_import_value: field=%r raw_type=%s raw=%r",
            self.name,
            type(value).__name__,
            value,
        )
        if isinstance(value, str):
            raw_items: list[Any] = [v for v in value.split("\n") if v]
        elif isinstance(value, list):
            raw_items = value
        else:
            raw_items = []
        _log.debug(
            "ListField.parse_import_value: field=%r split into %d item(s)",
            self.name,
            len(raw_items),
        )
        result = []
        for item in raw_items:
            result.append(await self.field.parse_import_value(request, item))
        return result

    async def validate(
        self, request: Request, value: Any, form_values: dict[str, Any]
    ) -> None:
        """Extends [BaseField.validate][starlette_admin.fields.BaseField.validate]
        by also running the inner `field`'s own `validate` (its `required`
        check and `validators`) against each item in `value`, after this
        field's own `validators` have passed. Item failures are collected
        into a single `ValueError` carrying a `dict` keyed by item index,
        matching the shape the form templates already know how to render.
        """
        await super().validate(request, value, form_values)
        if is_empty_value(value):
            return
        errors: dict[int, Any] = {}
        for index, item in enumerate(value):
            self._field_at(index)
            try:
                await self.field.validate(request, item, form_values)
            except ValueError as exc:
                errors[index] = field_error_payload(exc)
        if errors:
            raise ValueError(errors)

    def _extra_indices(self, form_data: FormData) -> list[int]:
        """
        Return list of all indices.  For example, if field id is `foo` and
        form_data contains following keys ['foo.0.bar', 'foo.1.baz'], then the indices are [0,1].
        Note that some numbers can be skipped. For example, you may have [0,1,3,8]
        as indices.
        """
        indices = set()
        for name in form_data:
            if name.startswith(self.id):
                idx = name[len(self.id) + 1 :].split(".", maxsplit=1)[0]
                if idx.isdigit():
                    indices.add(int(idx))
        return sorted(indices)

    def _field_at(self, idx: int | None = None) -> BaseField:
        if idx is not None:
            self.field.id = self.id + "." + str(idx)
        else:
            """To generate template string to be used in javascript"""
            self.field.id = ""
        if isinstance(self.field, CollectionField):
            self.field._propagate_id()
        return self.field

    def additional_css_links(self, request: Request) -> list[str]:
        return self.field.additional_css_links(request)

    def additional_js_links(self, request: Request) -> list[str]:
        return self.field.additional_js_links(request)


@dataclass
class ComputedField(StringField):
    """
    A read-only virtual field whose value is derived from the model object at
    display time.  No database column is required.

    Pass a ``getter`` for inline use:

    ```python
    ComputedField("full_name", getter=lambda request, obj: f"{obj.first_name} {obj.last_name}")
    ```

    Or subclass and override :meth:`parse_obj` for reusable fields:

    ```python
    class FullNameField(ComputedField):
        async def parse_obj(self, request: Request, obj: Any) -> str:
            return f"{obj.first_name} {obj.last_name}"
    ```

    The field is excluded from create forms by default (there is no object yet)
    and is always read-only.  It can still appear on edit forms as a plain-text
    display so the user sees the current computed value.
    """

    read_only: bool = True
    searchable: bool = False
    orderable: bool = False
    exclude_from_create: bool = True
    form_template: str = "fields/form/computed.html"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        return None


@dataclass
class SlugField(StringField):
    """
    A text field that is auto-populated (client-side) from another field as the
    user types, editable but pre-filled with a URL-safe slug.

    ```python
    SlugField("slug", populate_from="title")
    ```

    The ``populate_from`` parameter must be the *name* of another field on the
    same form.  A small piece of JavaScript watches that source field and fills
    this field whenever it is empty (or still matches the auto-generated value).
    Once the user manually edits the slug field the auto-fill stops, so an
    intentional override is never clobbered.
    """

    populate_from: str | None = None
    class_: str = "form-control"
    form_template: str = "fields/form/slug.html"

    def __post_init__(self) -> None:
        if not self.populate_from:
            raise ValueError(
                f"SlugField {self.name!r}: 'populate_from' must be set to the name "
                "of another field on the same form"
            )
        super().__post_init__()
        if not self.validators:
            self.validators = [slug()]
