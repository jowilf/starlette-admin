import datetime
import re
from typing import Optional, Union

import pytest
from starlette_admin import DateField, DateTimeField, TimeField
from starlette_admin.converters import StandardModelConverter
from starlette_admin.exceptions import NotSupportedAnnotation


class Model:
    datetime: datetime.datetime
    date: datetime.date
    time: Optional[datetime.time]


class UnsupportedModel:
    code: Union[str, int]


@pytest.fixture()
def converter() -> StandardModelConverter:
    return StandardModelConverter()


def test_standard_model_converter(converter: StandardModelConverter):
    assert converter.convert_fields_list(
        fields=["datetime", "date", "time"], model=Model
    ) == [
        DateTimeField("datetime", required=True),
        DateField("date", required=True),
        TimeField("time"),
    ]


def test_not_supported_annotation(converter: StandardModelConverter):
    with pytest.raises(
        NotSupportedAnnotation, match=re.escape("Cannot convert typing.Union[str, int]")
    ):
        converter.convert_fields_list(fields=["code"], model=UnsupportedModel)
