"""Unit tests for starlette_admin.tools.iter encode/decode."""

from starlette_admin.tools import iterdecode, iterencode


def test_encode_single():
    assert iterencode(["hello"]) == "hello"


def test_encode_multiple():
    assert iterencode(["a", "b", "c"]) == "a,b,c"


def test_encode_with_separator_in_value():
    assert iterencode(["a,b"]) == "a.,b"


def test_encode_with_escape_char():
    assert iterencode(["a.b"]) == "a..b"


def test_decode_single():
    assert iterdecode("hello") == ("hello",)


def test_decode_multiple():
    assert iterdecode("a,b,c") == ("a", "b", "c")


def test_encode_decode_roundtrip():
    original = ["foo", "bar,baz", "qux.quux"]
    encoded = iterencode(original)
    decoded = iterdecode(encoded)
    assert list(decoded) == original


def test_decode_escaped_separator():
    assert iterdecode("a.,b") == ("a,b",)


def test_decode_escaped_escape_char():
    assert iterdecode("a..b") == ("a.b",)
