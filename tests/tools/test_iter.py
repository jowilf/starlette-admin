import pytest
from starlette_admin.tools import iterdecode, iterencode


@pytest.mark.parametrize(
    "input_iterable, expected_output",
    [
        (["value1", "value2", "value3"], "value1,value2,value3"),
        (
            ["value.nested,1", "value,2", "value.3", "value4"],
            "value..nested.,1,value.,2,value..3,value4",
        ),
    ],
)
def test_iterencode(input_iterable, expected_output):
    result = iterencode(input_iterable)
    assert result == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        ("value1,value2,value3", ["value1", "value2", "value3"]),
        (
            "value..nested.,1,value.,2,value..3,value4",
            ["value.nested,1", "value,2", "value.3", "value4"],
        ),
    ],
)
def test_iterdecode(input_value, expected_output):
    result = iterdecode(input_value)
    assert result == tuple(expected_output)


@pytest.mark.parametrize(
    "data",
    [
        ["value1", "value2", "value3"],
        ["value.nested,1", "value,2", "value.3", "value4"],
    ],
)
def test_iterencode_iterdecode_inverse(data):
    encoded_data = iterencode(data)
    decoded_data = iterdecode(encoded_data)
    assert decoded_data == tuple(data)
