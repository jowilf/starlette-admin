"""CodSpeed performance benchmarks for starlette-admin.

These benchmarks focus on pure-CPU, deterministic code paths that do not
require a database, network access or an event loop. They cover the most
frequently exercised helpers and field-processing utilities used when
rendering admin pages and converting models into form fields.
"""

import datetime
import decimal
import enum
from typing import List, Optional

from starlette_admin._types import RequestAction
from starlette_admin.converters import StandardModelConverter
from starlette_admin.fields import (
    BaseField,
    BooleanField,
    DateTimeField,
    EnumField,
    IntegerField,
    StringField,
)
from starlette_admin.helpers import (
    extract_fields,
    get_file_icon,
    html_params,
    prettify_class_name,
    slugify_class_name,
)


class Status(str, enum.Enum):
    NEW = "new"
    ONGOING = "ongoing"
    DONE = "done"


class SampleModel:
    """A representative model with a mix of annotations to convert."""

    id: int
    name: str
    description: Optional[str]
    price: decimal.Decimal
    ratio: float
    is_active: bool
    created_at: datetime.datetime
    birthday: datetime.date
    tags: List[str]
    status: Status


def _build_fields(count: int) -> List[BaseField]:
    fields: List[BaseField] = []
    for i in range(count):
        fields.append(StringField(f"name_{i}"))
        fields.append(IntegerField(f"count_{i}", exclude_from_list=(i % 2 == 0)))
        fields.append(BooleanField(f"flag_{i}", exclude_from_detail=(i % 3 == 0)))
    return fields


def test_prettify_class_name(benchmark) -> None:
    benchmark(prettify_class_name, "SomeVeryLongModelViewClassName")


def test_slugify_class_name(benchmark) -> None:
    benchmark(slugify_class_name, "SomeVeryLongModelViewClassName")


def test_get_file_icon(benchmark) -> None:
    mime_types = [
        "image/png",
        "application/pdf",
        "application/vnd.ms-excel",
        "text/csv",
        "application/zip",
        "unknown/thing",
    ]

    def run() -> None:
        for mime_type in mime_types:
            get_file_icon(mime_type)

    benchmark(run)


def test_html_params(benchmark) -> None:
    params = {
        "type": "text",
        "minlength": None,
        "maxlength": 255,
        "placeholder": "Enter a value <here>",
        "required": True,
        "disabled": False,
        "readonly": False,
        "class_": "form-control",
    }
    benchmark(html_params, params)


def test_string_field_input_params(benchmark) -> None:
    field = StringField("title", maxlength=255, placeholder="Title", required=True)
    benchmark(field.input_params)


def test_extract_fields(benchmark) -> None:
    fields = _build_fields(40)
    benchmark(extract_fields, fields, RequestAction.LIST)


def test_field_dict_serialization(benchmark) -> None:
    field = DateTimeField("created_at", help_text="Creation timestamp", required=True)
    benchmark(field.dict)


def test_field_construction(benchmark) -> None:
    def run() -> None:
        StringField("name", maxlength=120, placeholder="Name", required=True)
        IntegerField("count", min=0, max=100)
        BooleanField("active")
        EnumField("status", enum=Status)

    benchmark(run)


def test_convert_fields_list(benchmark) -> None:
    converter = StandardModelConverter()
    field_names = list(SampleModel.__annotations__.keys())
    benchmark(
        lambda: converter.convert_fields_list(fields=field_names, model=SampleModel)
    )


def test_get_converter_lookup(benchmark) -> None:
    converter = StandardModelConverter()
    types = [str, int, float, bool, datetime.datetime, datetime.date, dict]
    benchmark(lambda: [converter.get_converter(t) for t in types])
