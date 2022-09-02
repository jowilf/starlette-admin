from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

from starlette_admin.helpers import html_params


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

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BooleanField(BaseField):
    search_builder_type: Optional[str] = "bool"
    render_function_key: str = "boolean"
    form_template: str = "forms/boolean.html"
    display_template: str = "displays/boolean.html"


@dataclass
class StringField(BaseField):
    search_builder_type: Optional[str] = "string"
    input_type = "text"
    class_ = "field-string form-control"
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


@dataclass
class NumberField(StringField):
    search_builder_type: str = "num"
    input_type = "number"
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
    class_ = "field-integer form-control"


@dataclass
class DecimalField(NumberField):
    step = "any"
    class_ = "field-decimal form-control"


@dataclass
class TextAreaField(StringField):
    rows: int = 6
    maxlength: Optional[int] = None
    minlength: Optional[int] = None
    class_ = "field-textarea form-control"

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


@dataclass
class EmailField(StringField):
    """Email field. Add highlight to displays value.
    The field itself doesn't validate data
    """

    input_type = "email"
    render_function_key = "email"
    class_ = "field-email form-control"


@dataclass
class PhoneField(StringField):
    """<input type='phone'>"""

    input_type = "phone"
    class_ = "field-phone form-control"


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
    choices: List[Dict[str, str]] = field(default_factory=list)
    form_template: str = "forms/enum.html"

    @classmethod
    def from_enum(
        cls,
        name: str,
        enum_type: Type[Enum],
        multiple: bool = False,
        **kwargs: Dict[str, Any]
    ) -> "EnumField":
        choices = list(map(lambda e: dict(name=e.name, value=e.value), enum_type))  # type: ignore
        return cls(name, choices=choices, multiple=multiple, **kwargs)

    @classmethod
    def from_choices(
        cls,
        name: str,
        choices: List[Dict[str, str]],
        multiple: bool = False,
        **kwargs: Dict[str, Any]
    ) -> "EnumField":
        return cls(name, choices=choices, multiple=multiple, **kwargs)


@dataclass
class DateTimeField(NumberField):
    """
    Parameters:
        search_format: moment.js format to send for searching. Use None for iso Format
        output_format: display output format
    """

    input_type = "datetime"
    class_ = "field-datetime form-control"
    search_builder_type: Optional[str] = "moment-MMMM D, YYYY HH:mm:ss"
    output_format: str = "%B %d, %Y %H:%M:%S"
    search_format: Optional[str] = None


@dataclass
class DateField(DateTimeField):
    """
    Parameters:
        search_format: moment.js format to send for searching. Use None for iso Format
        output_format: Set display output format
    """

    input_type = "date"
    class_ = "field-date form-control"
    output_format: str = "%B %d, %Y"
    search_format: Optional[str] = "YYYY-MM-DD"
    search_builder_type: Optional[str] = "moment-MMMM D, YYYY"


@dataclass
class TimeField(DateTimeField):
    """
    Parameters:
        search_format: Format to send for search. Use None for iso Format
        output_format: Set display output format
    """

    input_type = "time"
    class_ = "field-time form-control"
    search_builder_type: Optional[str] = "moment-HH:mm:ss"
    output_format: str = "%H:%M:%S"
    search_format: Optional[str] = "HH:mm:ss"


@dataclass
class JSONField(BaseField):
    """JsonField - return Dict[Any,Any]"""

    render_function_key: str = "json"
    form_template: str = "forms/json.html"
    display_template: str = "displays/json.html"


@dataclass
class FileField(BaseField):
    accept: Optional[str] = None
    multiple: bool = False
    render_function_key = "file"
    form_template = "forms/file.html"
    display_template = "displays/file.html"


@dataclass
class ImageField(FileField):
    accept = "image/*"
    render_function_key = "image"
    display_template = "displays/image.html"


@dataclass
class RelationField(BaseField):
    identity: Optional[str] = None
    multiple: bool = False
    render_function_key = "relation"
    form_template = "forms/relation.html"
    display_template = "displays/relation.html"


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

    multiple = True
