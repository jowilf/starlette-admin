import decimal
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time
from enum import Enum
from json import JSONDecodeError
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type, Union

from starlette.datastructures import FormData, UploadFile
from starlette.requests import Request
from starlette_admin.helpers import html_params, is_empty_file


@dataclass
class BaseField:
    """
    Base class for fields
    Parameters:
        name: Field name, same as attribute name in your model
        label: Field label
        type: Field type, unique key used to define the field
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
    display_template: str = "displays/text.html"

    def __post_init__(self) -> None:
        if self.label is None:
            self.label = self.name.replace("_", " ").capitalize()
        if self.type is None:
            self.type = type(self).__name__

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        return form_data.get(self.name)

    async def serialize_value(self, request: Request, value: Any, action: str) -> Any:
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

    async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
        return form_data.get(self.name) == "on"

    async def serialize_value(self, request: Request, value: Any, action: str) -> bool:
        return bool(value)


@dataclass
class StringField(BaseField):
    """This field is used to represent any kind of short text content."""

    search_builder_type: Optional[str] = "string"
    input_type: str = "text"
    class_: str = "field-string form-control"
    error_class = "is-invalid"
    placeholder: Optional[str] = None
    help_text: Optional[str] = None

    def input_params(self) -> str:
        return html_params(
            dict(
                type=self.input_type,
                placeholder=self.placeholder,
                required=self.required,
            )
        )

    async def serialize_value(self, request: Request, value: Any, action: str) -> Any:
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
            dict(
                rows=self.rows,
                minlength=self.minlength,
                maxlength=self.maxlength,
                placeholder=self.placeholder,
                required=self.required,
            )
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
            dict(
                type=self.input_type,
                min=self.min,
                max=self.max,
                step=self.step,
                placeholder=self.placeholder,
                required=self.required,
            )
        )


@dataclass
class IntegerField(NumberField):
    """
    This field is used to represent the value of properties that store integer numbers.
    Erroneous input is ignored and will not be accepted as a value."""

    class_: str = "field-integer form-control"

    async def parse_form_data(
        self, request: Request, form_data: FormData
    ) -> Optional[int]:
        try:
            return int(form_data.get(self.name))
        except (ValueError, TypeError):
            return None

    async def serialize_value(self, request: Request, value: Any, action: str) -> Any:
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
        self, request: Request, form_data: FormData
    ) -> Optional[decimal.Decimal]:
        try:
            return decimal.Decimal(form_data.get(self.name))
        except (decimal.InvalidOperation, ValueError):
            return None

    async def serialize_value(self, request: Request, value: Any, action: str) -> str:
        return str(value)


@dataclass
class FloatField(StringField):
    """
    A text field, except all input is coerced to an float.
     Erroneous input is ignored and will not be accepted as a value.
    """

    class_: str = "field-float form-control"

    async def parse_form_data(
        self, request: Request, form_data: FormData
    ) -> Optional[float]:
        try:
            return float(form_data.get(self.name))
        except ValueError:
            return None

    async def serialize_value(self, request: Request, value: Any, action: str) -> float:
        return float(value)


@dataclass
class TagsField(BaseField):
    """
    This field is used to represent the value of properties that store a list of
    string values. Render as `select2` tags input.
    """

    form_template: str = "forms/tags.html"
    form_js = "js/field/forms/tags.js"

    async def parse_form_data(self, request: Request, form_data: FormData) -> List[str]:
        return form_data.getlist(self.name)

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
    choices: Iterable[Tuple[str, str]] = field(default_factory=dict)
    form_template: str = "forms/enum.html"
    coerce: type = str

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        return (
            list(map(self.coerce, form_data.getlist(self.name)))
            if self.multiple
            else self.coerce(form_data.get(self.name))
        )

    def _get_label(self, value: Any) -> Any:
        if isinstance(value, Enum):
            return value.name
        for v, l in self.choices:
            if value == v:
                return self.coerce(l)
        raise ValueError(f"Invalid choice value: {value}")

    async def serialize_value(self, request: Request, value: Any, action: str) -> Any:
        labels = [self._get_label(v) for v in (value if self.multiple else [value])]
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
        choices = list(map(lambda e: (e.value, e.name), enum_type))  # type: ignore
        return cls(name, choices=choices, multiple=multiple, **kwargs)  # type: ignore

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
            dict(
                type=self.input_type,
                min=self.min,
                max=self.max,
                step=self.step,
                data_alt_format=self.form_alt_format,
                placeholder=self.placeholder,
                required=self.required,
            )
        )

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        try:
            return datetime.fromisoformat(form_data.get(self.name))
        except (TypeError, ValueError):
            return None

    async def serialize_value(self, request: Request, value: Any, action: str) -> str:
        assert isinstance(
            value, (datetime, date, time)
        ), f"Expect datetime, got  {type(value)}"
        if action != "EDIT":
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

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        try:
            return date.fromisoformat(form_data.get(self.name))
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

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        try:
            return time.fromisoformat(form_data.get(self.name))
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
        self, request: Request, form_data: FormData
    ) -> Optional[Dict[str, Any]]:
        try:
            value = form_data.get(self.name)
            return json.loads(value) if value is not None else None
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
    """

    multiple: bool = False
    render_function_key: str = "file"
    form_template: str = "forms/file.html"
    display_template: str = "displays/file.html"

    async def parse_form_data(
        self, request: Request, form_data: FormData
    ) -> Union[UploadFile, List[UploadFile], None]:
        if self.multiple:
            files = form_data.getlist(self.name)
            return [f for f in files if not is_empty_file(f.file)]
        file = form_data.get(self.name)
        return None if (file and is_empty_file(file.file)) else file

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

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        if self.multiple:
            return form_data.getlist(self.name)
        return form_data.get(self.name)

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
