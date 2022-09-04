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
    Base class for field
    Parameters:
        name: Field name, same as attribute name in your model
        label: Field label
        type: Field type, unique key used to define the field
        search_builder_type: datatable columns.searchBuilderType, For more information
            [click here](https://datatables.net/reference/option/columns.searchBuilderType)
        required: Indicate if the fields required
        is_array: Indicate if the fields is array of values
        exclude_from_list: Control field visibility in list page
        exclude_from_detail: Control field visibility in detail page
        exclude_from_create: Control field visibility in create page
        exclude_from_edit: Control field visibility in edit page
        searchable: Indicate if the fields is searchable
        orderable: Indicate if the fields is orderable
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

    async def serialize_value(self, request: Request, value: Any, action: str):
        return value

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BooleanField(BaseField):
    search_builder_type: Optional[str] = "bool"
    render_function_key: str = "boolean"
    form_template: str = "forms/boolean.html"
    display_template: str = "displays/boolean.html"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        return form_data.get(self.name) == "on"

    async def serialize_value(self, request: Request, value: Any, action: str):
        return bool(value)


@dataclass
class StringField(BaseField):
    search_builder_type: Optional[str] = "string"
    input_type: str = "text"
    class_: str = "field-string form-control"
    error_class = "is-invalid"
    placeholder: Optional[str] = None
    help_text: Optional[str] = None

    def input_params(self):
        return html_params(
            dict(
                type=self.input_type,
                placeholder=self.placeholder,
                required=self.required,
            )
        )

    async def serialize_value(self, request: Request, value: Any, action: str):
        return str(value)


@dataclass
class NumberField(StringField):
    search_builder_type: str = "num"
    input_type: str = "number"
    max: Optional[int] = None
    min: Optional[int] = None
    step: Union[str, int, None] = None

    def input_params(self):
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
    class_: str = "field-integer form-control"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        try:
            return int(form_data.get(self.name))
        except (ValueError, TypeError):
            return None

    async def serialize_value(self, request: Request, value: Any, action: str):
        return int(value)


@dataclass
class DecimalField(NumberField):
    step: str = "any"
    class_: str = "field-decimal form-control"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        try:
            return decimal.Decimal(form_data.get(self.name))
        except (decimal.InvalidOperation, ValueError):
            return None

    async def serialize_value(self, request: Request, value: Any, action: str):
        return str(value)


@dataclass
class FloatField(StringField):
    class_: str = "field-float form-control"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        try:
            return float(form_data.get(self.name))
        except ValueError:
            return None

    async def serialize_value(self, request: Request, value: Any, action: str):
        return float(value)


@dataclass
class TextAreaField(StringField):
    rows: int = 6
    maxlength: Optional[int] = None
    minlength: Optional[int] = None
    class_: str = "field-textarea form-control"

    form_template: str = "forms/textarea.html"

    def input_params(self):
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
class TagsField(BaseField):
    """Use select2 tags for form
    Will return List[str]
    """

    form_template: str = "forms/tags.html"
    form_js = "js/field/forms/tags.js"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        return form_data.getlist(self.name)


@dataclass
class EmailField(StringField):
    """Email field. Add highlight to displays value.
    The field itself doesn't validate data
    """

    input_type: str = "email"
    render_function_key = "email"
    class_: str = "field-email form-control"


@dataclass
class PhoneField(StringField):
    """<input type='phone'>"""

    input_type: str = "phone"
    class_: str = "field-phone form-control"


@dataclass
class EnumField(StringField):
    """Enum field.
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
    """

    multiple: bool = False
    choices: Iterable[Tuple[str, str]] = field(default_factory=dict)
    form_template: str = "forms/enum.html"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        if self.multiple:
            return form_data.getlist(self.name)
        return form_data.get(self.name)

    def _get_label(self, value) -> str:
        if isinstance(value, Enum):
            return value.name
        for v, l in self.choices:
            if value == v:
                return l
        raise ValueError(f"Invalid choice value: {value}")

    async def serialize_value(self, request: Request, value: Any, action: str):
        labels = [self._get_label(v) for v in (value if self.multiple else [value])]
        return labels if self.multiple else labels[0]

    @classmethod
    def from_enum(
        cls,
        name: str,
        enum_type: Type[Enum],
        multiple: bool = False,
        **kwargs: Dict[str, Any],
    ) -> "EnumField":
        choices = list(map(lambda e: (e.value, e.name), enum_type))  # type: ignore
        return cls(name, choices=choices, multiple=multiple, **kwargs)

    @classmethod
    def from_choices(
        cls,
        name: str,
        choices: Union[List[Tuple[str, str]], List[str]],
        multiple: bool = False,
        **kwargs: Dict[str, Any],
    ) -> "EnumField":
        if len(choices) > 0 and not isinstance(choices[0], (list, tuple)):
            choices = zip(choices, choices)
        return cls(name, choices=choices, multiple=multiple, **kwargs)


@dataclass
class DateTimeField(NumberField):
    """
    Parameters:
        search_format: moment.js format to send for searching. Use None for iso Format
        output_format: display output format
    """

    input_type: str = "datetime-local"
    class_: str = "field-datetime form-control"
    search_builder_type: Optional[str] = "moment-MMMM D, YYYY HH:mm:ss"
    output_format: str = "%B %d, %Y %H:%M:%S"
    search_format: Optional[str] = None

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        try:
            return datetime.fromisoformat(form_data.get(self.name))
        except (TypeError, ValueError):
            return None

    async def serialize_value(self, request: Request, value: Any, action: str):
        assert isinstance(
            value, (datetime, date, time)
        ), f"Expect datetime, got  {type(value)}"
        if action != "EDIT":
            return value.strftime(self.output_format)
        return value.isoformat()


@dataclass
class DateField(DateTimeField):
    """
    Parameters:
        search_format: moment.js format to send for searching. Use None for iso Format
        output_format: Set display output format
    """

    input_type: str = "date"
    class_: str = "field-date form-control"
    output_format: str = "%B %d, %Y"
    search_format: Optional[str] = "YYYY-MM-DD"
    search_builder_type: Optional[str] = "moment-MMMM D, YYYY"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        try:
            return date.fromisoformat(form_data.get(self.name))
        except (TypeError, ValueError):
            return None


@dataclass
class TimeField(DateTimeField):
    """
    Parameters:
        search_format: Format to send for search. Use None for iso Format
        output_format: Set display output format
    """

    input_type: str = "time"
    class_: str = "field-time form-control"
    search_builder_type: Optional[str] = "moment-HH:mm:ss"
    output_format: str = "%H:%M:%S"
    search_format: Optional[str] = "HH:mm:ss"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        try:
            return time.fromisoformat(form_data.get(self.name))
        except (TypeError, ValueError):
            return None


@dataclass
class JSONField(BaseField):
    """JsonField - return Dict[Any,Any]"""

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
            # raise FormValidationError({self.name: "Invalid JSON value"})
            return None


@dataclass
class FileField(BaseField):
    multiple: bool = False
    render_function_key = "file"
    form_template: str = "forms/file.html"
    display_template: str = "displays/file.html"

    async def parse_form_data(
        self, request: Request, form_data: FormData
    ) -> Union[UploadFile, List[UploadFile], None]:
        if self.multiple:
            files = form_data.getlist(self.name)
            return [f for f in files if not is_empty_file(f.file)]
        file = form_data.get(self.name)
        return None if is_empty_file(file.file) else file


@dataclass
class ImageField(FileField):
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


@dataclass
class HasOne(RelationField):
    """
    Parameters:
        identity: Foreign ModelView identity
    """

    pass


@dataclass
class HasMany(RelationField):
    """
    Parameters:
        identity: Foreign ModelView identity
    """

    multiple: bool = True
