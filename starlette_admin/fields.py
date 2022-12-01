import decimal
import json
from dataclasses import asdict, dataclass
from dataclasses import field as dc_field
from datetime import date, datetime, time
from enum import Enum, IntEnum
from json import JSONDecodeError
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Type, Union

from starlette.datastructures import FormData, UploadFile
from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.helpers import extract_fields, html_params, is_empty_file


@dataclass
class BaseField:
    """
    Base class for fields
    Parameters:
        name: Field name, same as attribute name in your model
        label: Field label
        help_text: Hint message to display in forms
        type: Field type, unique key used to define the field
        id: Unique id, used to represent field instance
        search_builder_type: datatable columns.searchBuilderType, For more information
            [click here](https://datatables.net/reference/option/columns.searchBuilderType)
        required: Indicate if the fields is required
        exclude_from_list: Control field visibility in list page
        exclude_from_detail: Control field visibility in detail page
        exclude_from_create: Control field visibility in create page
        exclude_from_edit: Control field visibility in edit page
        searchable: Indicate if the fields is searchable
        orderable: Indicate if the fields is orderable
        render_function_key: Render function key inside the global `render` variable in javascript
        form_template: template for rendering this field in creation and edit page
        display_template: template for displaying this field in detail page
    """

    name: str
    label: Optional[str] = None
    type: Optional[str] = None
    help_text: Optional[str] = None
    id: str = ""
    search_builder_type: Optional[str] = "default"
    required: Optional[bool] = False
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False
    exclude_from_create: Optional[bool] = False
    exclude_from_edit: Optional[bool] = False
    searchable: Optional[bool] = True
    orderable: Optional[bool] = True
    render_function_key: str = "text"
    form_template: str = "forms/input.html"
    label_template: str = "forms/_label.html"
    display_template: str = "displays/text.html"
    error_class = "is-invalid"

    def __post_init__(self) -> None:
        if self.label is None:
            self.label = self.name.replace("_", " ").capitalize()
        if self.type is None:
            self.type = type(self).__name__
        self.id = self.name

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        return form_data.get(self.id)

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return value

    def additional_css_links(self, request: Request) -> List[str]:
        return []

    def additional_js_links(self, request: Request) -> List[str]:
        return []

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BooleanField(BaseField):
    """This field displays the `true/false` value of a boolean property."""

    search_builder_type: Optional[str] = "bool"
    render_function_key: str = "boolean"
    form_template: str = "forms/boolean.html"
    display_template: str = "displays/boolean.html"

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> bool:
        return form_data.get(self.id) == "on"

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> bool:
        return bool(value)


@dataclass
class StringField(BaseField):
    """This field is used to represent any kind of short text content."""

    search_builder_type: Optional[str] = "string"
    input_type: str = "text"
    class_: str = "field-string form-control"
    placeholder: Optional[str] = None

    def input_params(self) -> str:
        return html_params(
            {
                "type": self.input_type,
                "placeholder": self.placeholder,
                "required": self.required,
            }
        )

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return str(value)


@dataclass
class TextAreaField(StringField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    maxlength: Optional[int] = None
    minlength: Optional[int] = None
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"

    def input_params(self) -> str:
        return html_params(
            {
                "rows": self.rows,
                "minlength": self.minlength,
                "maxlength": self.maxlength,
                "placeholder": self.placeholder,
                "required": self.required,
            }
        )


@dataclass
class NumberField(StringField):
    """This field is used to represent the value of properties
    that store numbers of any type (integers or decimals).
    Should not be used directly. use [IntegerField][starlette_admin.fields.IntegerField]
    or [DecimalField][starlette_admin.fields.DecimalField]
    """

    search_builder_type: str = "num"
    input_type: str = "number"
    max: Optional[int] = None
    min: Optional[int] = None
    step: Union[str, int, None] = None

    def input_params(self) -> str:
        return html_params(
            {
                "type": self.input_type,
                "min": self.min,
                "max": self.max,
                "step": self.step,
                "placeholder": self.placeholder,
                "required": self.required,
            }
        )


@dataclass
class IntegerField(NumberField):
    """
    This field is used to represent the value of properties that store integer numbers.
    Erroneous input is ignored and will not be accepted as a value."""

    class_: str = "field-integer form-control"

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Optional[int]:
        try:
            return int(form_data.get(self.id))  # type: ignore
        except (ValueError, TypeError):
            return None

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return int(value)


@dataclass
class DecimalField(NumberField):
    """
    This field is used to represent the value of properties that store decimal numbers.
    Erroneous input is ignored and will not be accepted as a value.
    """

    step: str = "any"
    class_: str = "field-decimal form-control"

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Optional[decimal.Decimal]:
        try:
            return decimal.Decimal(form_data.get(self.id))  # type: ignore
        except (decimal.InvalidOperation, ValueError):
            return None

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> str:
        return str(value)


@dataclass
class FloatField(StringField):
    """
    A text field, except all input is coerced to an float.
     Erroneous input is ignored and will not be accepted as a value.
    """

    class_: str = "field-float form-control"

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Optional[float]:
        try:
            return float(form_data.get(self.id))  # type: ignore
        except ValueError:
            return None

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> float:
        return float(value)


@dataclass
class TagsField(BaseField):
    """
    This field is used to represent the value of properties that store a list of
    string values. Render as `select2` tags input.
    """

    form_template: str = "forms/tags.html"
    form_js: str = "js/field/forms/tags.js"
    class_: str = "field-tags form-control form-select"

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> List[str]:
        return form_data.getlist(self.id)  # type: ignore

    def additional_css_links(self, request: Request) -> List[str]:
        return [
            request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics", path="css/select2.min.css"
            )
        ]

    def additional_js_links(self, request: Request) -> List[str]:
        return [
            request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics",
                path="js/vendor/select2.min.js",
            )
        ]


@dataclass
class EmailField(StringField):
    """This field is used to represent a text content
    that stores a single email address."""

    input_type: str = "email"
    render_function_key: str = "email"
    class_: str = "field-email form-control"
    display_template: str = "displays/email.html"


@dataclass
class URLField(StringField):
    """This field is used to represent a text content that stores a single URL."""

    input_type: str = "url"
    render_function_key: str = "url"
    class_: str = "field-url form-control"
    display_template: str = "displays/url.html"


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


@dataclass
class PasswordField(StringField):
    """A StringField, except renders an `<input type="password">`."""

    input_type: str = "password"
    class_: str = "field-password form-control"


@dataclass
class EnumField(StringField):
    """
    Enumeration Field.
    It take a python `enum.Enum` class or a list of *(value, label)* pairs.
    It can also be a list of only values, in which case the value is used as the label.
    Example:
        ```Python
        class Status(str, enum.Enum):
            NEW = "new"
            ONGOING = "ongoing"
            DONE = "done"

        class MyModel:
            status: Optional[Status] = None

        class MyModelView(ModelView):
            fields = [EnumField.from_enum("status", Status)]
        ```

        ```Python
        class MyModel:
            language: str

        class MyModelView(ModelView):
            fields = [EnumField.from_choices("language", [('cpp', 'C++'), ('py', 'Python'), ('text', 'Plain Text')])]
        ```
    """

    multiple: bool = False
    choices: Iterable[Tuple[str, str]] = dc_field(default_factory=dict)
    form_template: str = "forms/enum.html"
    class_: str = "field-enum form-control form-select"
    coerce: type = str

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        return (
            list(map(self.coerce, form_data.getlist(self.id)))
            if self.multiple
            else (
                self.coerce(form_data.get(self.id)) if form_data.get(self.id) else None
            )
        )

    def _get_label(self, value: Any) -> Any:
        if isinstance(value, Enum):
            return value.name
        for v, label in self.choices:
            if value == v:
                return label
        raise ValueError(f"Invalid choice value: {value}")

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        labels = [
            (self._get_label(v) if action != RequestAction.EDIT else v)
            for v in (value if self.multiple else [value])
        ]
        return labels if self.multiple else labels[0]

    def additional_css_links(self, request: Request) -> List[str]:
        return [
            request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics", path="css/select2.min.css"
            )
        ]

    def additional_js_links(self, request: Request) -> List[str]:
        return [
            request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics",
                path="js/vendor/select2.min.js",
            )
        ]

    @classmethod
    def from_enum(
        cls,
        name: str,
        enum_type: Type[Enum],
        multiple: bool = False,
        **kwargs: Dict[str, Any],
    ) -> "EnumField":
        choices = [(e.value, e.name.replace("_", " ")) for e in enum_type]
        coerce = int if issubclass(enum_type, IntEnum) else str
        return cls(name, choices=choices, multiple=multiple, coerce=coerce, **kwargs)  # type: ignore

    @classmethod
    def from_choices(
        cls,
        name: str,
        choices: Union[List[Tuple[str, str]], List[str], Tuple],
        multiple: bool = False,
        **kwargs: Dict[str, Any],
    ) -> "EnumField":
        if len(choices) > 0 and not isinstance(choices[0], (list, tuple)):
            choices = list(zip(choices, choices))
        return cls(name, choices=choices, multiple=multiple, **kwargs)  # type: ignore


@dataclass
class DateTimeField(NumberField):
    """
    This field is used to represent a value that stores a python datetime.datetime object
    Parameters:
        search_format: moment.js format to send for searching. Use None for iso Format
        output_format: display output format
    """

    input_type: str = "datetime-local"
    class_: str = "field-datetime form-control"
    search_builder_type: str = "moment-MMMM D, YYYY HH:mm:ss"
    output_format: str = "%B %d, %Y %H:%M:%S"
    search_format: Optional[str] = None
    form_alt_format: Optional[str] = "F j, Y  H:i:S"

    def input_params(self) -> str:
        return html_params(
            {
                "type": self.input_type,
                "min": self.min,
                "max": self.max,
                "step": self.step,
                "data_alt_format": self.form_alt_format,
                "placeholder": self.placeholder,
                "required": self.required,
            }
        )

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        try:
            return datetime.fromisoformat(form_data.get(self.id))  # type: ignore
        except (TypeError, ValueError):
            return None

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> str:
        assert isinstance(
            value, (datetime, date, time)
        ), f"Expect datetime, got  {type(value)}"
        if action != RequestAction.EDIT:
            return value.strftime(self.output_format)
        return value.isoformat()

    def additional_css_links(self, request: Request) -> List[str]:
        return [
            request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics", path="css/flatpickr.min.css"
            )
        ]

    def additional_js_links(self, request: Request) -> List[str]:
        return [
            request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics",
                path="js/vendor/flatpickr.min.js",
            )
        ]


@dataclass
class DateField(DateTimeField):
    """
    This field is used to represent a value that stores a python datetime.date object
    Parameters:
        search_format: moment.js format to send for searching. Use None for iso Format
        output_format: Set display output format
    """

    input_type: str = "date"
    class_: str = "field-date form-control"
    output_format: str = "%B %d, %Y"
    search_format: str = "YYYY-MM-DD"
    search_builder_type: str = "moment-MMMM D, YYYY"
    form_alt_format: Optional[str] = "F j, Y"

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        try:
            return date.fromisoformat(form_data.get(self.id))  # type: ignore
        except (TypeError, ValueError):
            return None


@dataclass
class TimeField(DateTimeField):
    """
    This field is used to represent a value that stores a python datetime.time object
    Parameters:
        search_format: Format to send for search. Use None for iso Format
        output_format: Set display output format
    """

    input_type: str = "time"
    class_: str = "field-time form-control"
    search_builder_type: str = "moment-HH:mm:ss"
    output_format: str = "%H:%M:%S"
    search_format: str = "HH:mm:ss"
    form_alt_format: Optional[str] = "H:i:S"

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        try:
            return time.fromisoformat(form_data.get(self.id))  # type: ignore
        except (TypeError, ValueError):
            return None


@dataclass
class JSONField(BaseField):
    """
    This field render jsoneditor and represent a value that stores python dict object.
    Erroneous input is ignored and will not be accepted as a value."""

    render_function_key: str = "json"
    form_template: str = "forms/json.html"
    display_template: str = "displays/json.html"

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Optional[Dict[str, Any]]:
        try:
            value = form_data.get(self.id)
            return json.loads(value) if value is not None else None  # type: ignore
        except JSONDecodeError:
            return None

    def additional_css_links(self, request: Request) -> List[str]:
        return [
            request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics", path="css/jsoneditor.min.css"
            )
        ]

    def additional_js_links(self, request: Request) -> List[str]:
        return [
            request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics",
                path="js/vendor/jsoneditor.min.js",
            )
        ]


@dataclass
class FileField(BaseField):
    """
    Renders a file upload field.
    This field is used to represent a value that stores starlette UploadFile object.
    For displaying value, this field wait for three properties which is `filename`,
    `content-type` and `url`. Use `multiple=True` for multiple file upload
    When user ask for delete on editing page, the second part of the returned tuple is True.
    """

    multiple: bool = False
    render_function_key: str = "file"
    form_template: str = "forms/file.html"
    display_template: str = "displays/file.html"

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Tuple[Union[UploadFile, List[UploadFile], None], bool]:
        should_be_deleted = form_data.get(f"_{self.id}-delete") == "on"
        if self.multiple:
            files = form_data.getlist(self.id)
            return [f for f in files if not is_empty_file(f.file)], should_be_deleted  # type: ignore
        file = form_data.get(self.id)
        return (None if (file and is_empty_file(file.file)) else file), should_be_deleted  # type: ignore

    def _isvalid_value(self, value: Any) -> bool:
        return value is not None and all(
            [
                (
                    hasattr(v, "url")
                    or (isinstance(v, dict) and v.get("url", None) is not None)
                )
                for v in (value if self.multiple else [value])
            ]
        )


@dataclass
class ImageField(FileField):
    """
    FileField with `accept="image/*"`.
    """

    render_function_key: str = "image"
    form_template: str = "forms/image.html"
    display_template: str = "displays/image.html"


@dataclass
class RelationField(BaseField):
    identity: Optional[str] = None
    multiple: bool = False
    render_function_key: str = "relation"
    form_template: str = "forms/relation.html"
    display_template: str = "displays/relation.html"

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        if self.multiple:
            return form_data.getlist(self.id)
        return form_data.get(self.id)

    def additional_css_links(self, request: Request) -> List[str]:
        return [
            request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics", path="css/select2.min.css"
            )
        ]

    def additional_js_links(self, request: Request) -> List[str]:
        return [
            request.url_for(
                f"{request.app.state.ROUTE_NAME}:statics",
                path="js/vendor/select2.min.js",
            )
        ]


@dataclass
class HasOne(RelationField):
    """
    Parameters:
        identity: Foreign ModelView identity
    """


@dataclass
class HasMany(RelationField):
    """
    Parameters:
        identity: Foreign ModelView identity
    """

    multiple: bool = True


@dataclass(init=False)
class CollectionField(BaseField):
    """
    This field represents a collection of others fields. Can be used to represent embedded mongodb document.
    !!!usage
    ```python
     CollectionField("config", fields=[StringField("key"), IntegerField("value", help_text="multiple of 5")]),
    ```
    """

    fields: Sequence[BaseField] = dc_field(default_factory=list)
    render_function_key: str = "json"
    form_template: str = "forms/collection.html"
    display_template: str = "displays/collection.html"

    def __init__(
        self, name: str, fields: Sequence[BaseField], required: bool = False
    ) -> None:
        self.name = name
        self.fields = fields
        self.required = required
        super().__post_init__()
        self._propagate_id()

    def _extract_fields(
        self, action: RequestAction = RequestAction.LIST
    ) -> Sequence[BaseField]:
        return extract_fields(self.fields, action)

    def _propagate_id(self) -> None:
        """Will update fields id by adding his id as prefix (ex: category.name)"""
        for field in self.fields:
            field.id = self.id + ("." if self.id else "") + field.name
            if isinstance(field, type(self)):
                field._propagate_id()

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        value = {}
        for field in self.fields:
            if (action == RequestAction.EDIT and field.exclude_from_edit) or (
                action == RequestAction.CREATE and field.exclude_from_create
            ):
                continue
            value[field.name] = await field.parse_form_data(request, form_data, action)
        return value

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        serialized_value: Dict[str, Any] = {}
        for field in self.fields:
            name = field.name
            serialized_value[name] = None
            if hasattr(value, name) or (isinstance(value, dict) and name in value):
                field_value = (
                    getattr(value, name) if hasattr(value, name) else value[name]
                )
                if field_value is not None:
                    serialized_value[name] = await field.serialize_value(
                        request, field_value, action
                    )
        return serialized_value

    def additional_css_links(self, request: Request) -> List[str]:
        _links = []
        for f in self.fields:
            _links.extend(f.additional_css_links(request))
        return _links

    def additional_js_links(self, request: Request) -> List[str]:
        _links = []
        for f in self.fields:
            _links.extend(f.additional_js_links(request))
        return _links


@dataclass(init=False)
class ListField(BaseField):
    """
    Encapsulate an ordered list of multiple instances of the same field type,
    keeping data as a list.

    !!!usage
        ```python
        class MyModel:
            id: Optional[int]
            values: List[str]

        class ModelView(BaseModelView):
            fields = [IntegerField("id"), ListField(StringField("values")]
        ```
    """

    form_template: str = "forms/list.html"
    display_template: str = "displays/list.html"
    search_builder_type: str = "array"
    field: BaseField = dc_field(default_factory=lambda: BaseField(""))

    def __init__(self, field: BaseField, required: bool = False) -> None:
        self.field = field
        self.name = field.name
        self.required = required
        self.__post_init__()

    def __post_init__(self) -> None:
        super().__post_init__()
        self.field.id = ""
        if isinstance(self.field, CollectionField):
            self.field._propagate_id()

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        indices = self._extra_indices(form_data)
        value = []
        for index in indices:
            self.field.id = "{}.{}".format(self.id, index)
            if isinstance(self.field, CollectionField):
                self.field._propagate_id()
            value.append(await self.field.parse_form_data(request, form_data, action))
        return value

    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        serialized_value = []
        for item in value:
            serialized_item_value = None
            if item is not None:
                serialized_item_value = await self.field.serialize_value(
                    request, item, action
                )
            serialized_value.append(serialized_item_value)
        return serialized_value

    def _extra_indices(self, form_data: FormData) -> List[int]:
        """
        Return list of all indices.  For example, if field id is `foo` and
        form_data contains following keys ['foo.0.bar', 'foo.1.baz'], then the indices are [0,1].
        Note that some numbers can be skipped. For example, you may have [0,1,3,8]
        as indices.
        """
        indices = set()
        for k in form_data:
            if k.startswith(self.id):
                k = k[len(self.id) + 1 :].split(".", maxsplit=1)[0]
                if k.isdigit():
                    indices.add(int(k))
        return sorted(indices)

    def _field_at(self, idx: Optional[int] = None) -> BaseField:
        if idx is not None:
            self.field.id = self.id + "." + str(idx)
        else:
            """To generate template string to be used in javascript"""
            self.field.id = ""
        if isinstance(self.field, CollectionField):
            self.field._propagate_id()
        return self.field

    def additional_css_links(self, request: Request) -> List[str]:
        return self.field.additional_css_links(request)

    def additional_js_links(self, request: Request) -> List[str]:
        return self.field.additional_js_links(request)
