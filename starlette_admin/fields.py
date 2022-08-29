from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type


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
    is_array: Optional[bool] = False
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False
    exclude_from_create: Optional[bool] = False
    exclude_from_edit: Optional[bool] = False
    searchable: Optional[bool] = True
    orderable: Optional[bool] = True

    def __post_init__(self) -> None:
        if self.label is None:
            self.label = self.name.replace("_", " ").capitalize()

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BooleanField(BaseField):
    type: str = "bool"
    search_builder_type: Optional[str] = "bool"


@dataclass
class NumberField(BaseField):
    type: str = "num"
    search_builder_type: str = "num"


@dataclass
class IntegerField(NumberField):
    pass


@dataclass
class DecimalField(NumberField):
    decimal: bool = True


@dataclass
class StringField(BaseField):
    type: str = "text"
    input_type = "text"
    search_builder_type: Optional[str] = "string"


@dataclass
class TextAreaField(StringField):
    multiline: bool = True


@dataclass
class TagsField(StringField):
    """Use select2 tags for form"""

    type: str = "tags"
    is_array: Optional[bool] = True


@dataclass
class EmailField(StringField):
    """Email field. Add highlight to displays value.
    The field itself doesn't validate data
    """

    type: str = "email"


@dataclass
class PhoneField(StringField):
    """<input type='phone'>"""

    input_type = "phone"


@dataclass
class EnumField(BaseField):
    """Enum field.
    Example:
        ```Python
        class Status(str, enum.Enum):
            NEW = "new"
            ONGOING = "ongoing"
            DONE = "done"

        field = EnumField.from_enum("field_name", Status)
        ```
    """

    type: str = "enum"
    search_builder_type: Optional[str] = "string"
    values: List[Dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_enum(
        cls,
        name: str,
        enum_type: Type[Enum],
        is_array: bool = False,
        searchable: bool = True,
        search_builder_type: Optional[str] = "string",
    ) -> "EnumField":
        values = list(map(lambda e: dict(name=e.name, value=e.value), enum_type))  # type: ignore
        return cls(
            name,
            values=values,
            is_array=is_array,
            searchable=searchable,
            search_builder_type=search_builder_type,
        )


@dataclass
class DateTimeField(BaseField):
    """
    Parameters:
        search_format: Format to send for search. Use None for iso Format
        output_format: Set display output format
    """

    type: str = "datetime"
    output_format: str = "%B %d, %Y %H:%M:%S"
    search_format: Optional[str] = None
    search_builder_type: Optional[str] = "moment-MMMM D, YYYY HH:mm:ss"


@dataclass
class DateField(BaseField):
    """
    Parameters:
        search_format: Format to send for search. Use None for iso Format
        output_format: Set display output format
    """

    type: str = "date"
    output_format: str = "%B %d, %Y"
    search_format: Optional[str] = "YYYY-MM-DD"
    search_builder_type: Optional[str] = "moment-MMMM D, YYYY"


@dataclass
class TimeField(BaseField):
    """
    Parameters:
        search_format: Format to send for search. Use None for iso Format
        output_format: Set display output format
    """

    type: str = "time"
    output_format: str = "%H:%M:%S"
    search_format: Optional[str] = "HH:mm:ss"
    search_builder_type: Optional[str] = "moment-HH:mm:ss"


@dataclass
class JSONField(BaseField):
    type: str = "json"


@dataclass
class FileField(BaseField):
    type: str = "file"


@dataclass
class ImageField(FileField):
    type: str = "image"


@dataclass
class RelationField(BaseField):
    type: str = "relation"
    identity: Optional[str] = None


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

    many: bool = True
    is_array: Optional[bool] = True
