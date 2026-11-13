from typing import cast
from unittest.mock import Mock

from sqlalchemy.orm import InstrumentedAttribute
from starlette_admin.contrib.sqla.helpers import extract_column_python_type


def test_extract_column_python_type_falls_back_to_str_for_object_type() -> None:
    attr = Mock()
    attr.type.python_type = object
    assert extract_column_python_type(cast("InstrumentedAttribute", attr)) is str
