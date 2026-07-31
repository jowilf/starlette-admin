"""Unit tests for `starlette_admin.helpers`."""

import io
from unittest.mock import MagicMock

import pytest
from markupsafe import Markup
from pydantic import BaseModel, ValidationError
from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from starlette_admin.helpers import (
    _as_url_callable,
    get_file_icon,
    html_safe_json,
    is_empty_file,
    pydantic_error_to_form_validation_errors,
    safe_url,
)

# ── _as_url_callable ──────────────────────────────────────────────────────────


def _mock_request() -> Request:
    return MagicMock(spec=Request)


def test_as_url_callable_with_string():
    fn = _as_url_callable("/static/logo.png")
    assert fn(_mock_request()) == "/static/logo.png"


def test_as_url_callable_with_none():
    fn = _as_url_callable(None)
    assert fn(_mock_request()) is None


def test_as_url_callable_with_callable():
    cb = lambda req: f"/logo/{req.state.tenant}"  # noqa: E731
    fn = _as_url_callable(cb)
    assert fn is cb


def test_as_url_callable_callable_receives_request():
    received = []
    req = _mock_request()

    def cb(r: Request) -> str:
        received.append(r)
        return "/logo.png"

    fn = _as_url_callable(cb)
    result = fn(req)
    assert result == "/logo.png"
    assert received == [req]


# ── is_empty_file ─────────────────────────────────────────────────────────────


def test_is_empty_file_with_empty_buffer():
    buf = io.BytesIO(b"")
    assert is_empty_file(buf) is True


def test_is_empty_file_with_content():
    buf = io.BytesIO(b"hello")
    assert is_empty_file(buf) is False


def test_is_empty_file_preserves_position():
    buf = io.BytesIO(b"data")
    buf.seek(2)
    is_empty_file(buf)
    assert buf.tell() == 2


# ── get_file_icon ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "mime_type,expected_icon",
    [
        ("image/png", "fa-solid fa-fw fa-file-image"),
        ("image/jpeg", "fa-solid fa-fw fa-file-image"),
        ("audio/mpeg", "fa-solid fa-fw fa-file-audio"),
        ("video/mp4", "fa-solid fa-fw fa-file-video"),
        ("application/pdf", "fa-solid fa-fw fa-file-pdf"),
        ("application/msword", "fa-solid fa-fw fa-file-word"),
        ("application/vnd.ms-excel", "fa-solid fa-fw fa-file-excel"),
        ("application/vnd.ms-powerpoint", "fa-solid fa-fw fa-file-powerpoint"),
        ("text/plain", "fa-solid fa-fw fa-file-text"),
        ("text/html", "fa-solid fa-fw fa-file-code"),
        ("text/csv", "fa-solid fa-fw fa-file-csv"),
        ("application/json", "fa-solid fa-fw fa-file-code"),
        ("application/gzip", "fa-solid fa-fw fa-file-archive"),
        ("application/zip", "fa-solid fa-fw fa-file-archive"),
        ("application/octet-stream", "fa-solid fa-fw fa-file"),
        ("", "fa-solid fa-fw fa-file"),
    ],
)
def test_get_file_icon(mime_type, expected_icon):
    assert get_file_icon(mime_type) == expected_icon


# ── pydantic_error_to_form_validation_errors ─────────────────────────────────


# ── safe_url ──────────────────────────────────────────────────────────────────


def test_safe_url_disallowed_scheme_returns_empty():
    assert safe_url("javascript:alert(1)") == ""


def test_safe_url_allowed_scheme_returns_url():
    assert safe_url("https://example.com") == "https://example.com"


def test_safe_url_relative_url_passes_through():
    assert safe_url("/static/logo.png") == "/static/logo.png"


def test_safe_url_str_raises_returns_empty():
    class BadStr:
        def __str__(self):
            raise ValueError("bad")

    assert safe_url(BadStr()) == ""


def test_safe_url_custom_allowed_schemes():
    assert safe_url("ftp://example.com", allowed_schemes={"ftp"}) == "ftp://example.com"
    assert safe_url("https://example.com", allowed_schemes={"ftp"}) == ""


# ── pydantic_error_to_form_validation_errors ─────────────────────────────────


def test_pydantic_error_to_form_validation_errors_flat():
    class Model(BaseModel):
        name: str
        age: int

    with pytest.raises(ValidationError) as exc_info:
        Model(name=123, age="not-an-int")  # type: ignore

    result = pydantic_error_to_form_validation_errors(exc_info.value)
    assert isinstance(result, FormValidationError)
    assert "age" in result.errors


def test_pydantic_error_to_form_validation_errors_nested():
    class Inner(BaseModel):
        value: int

    class Outer(BaseModel):
        inner: Inner

    with pytest.raises(ValidationError) as exc_info:
        Outer(inner={"value": "bad"})  # type: ignore

    result = pydantic_error_to_form_validation_errors(exc_info.value)
    assert isinstance(result, FormValidationError)
    assert "inner" in result.errors


def test_pydantic_error_to_form_validation_errors_with_key_map():
    class Model(BaseModel):
        company_id: int

    with pytest.raises(ValidationError) as exc_info:
        Model(company_id="not-an-int")  # type: ignore

    result = pydantic_error_to_form_validation_errors(
        exc_info.value, key_map={"company_id": "company"}
    )
    assert isinstance(result, FormValidationError)
    assert "company" in result.errors
    assert "company_id" not in result.errors


def test_pydantic_error_to_form_validation_errors_key_map_no_match():
    class Model(BaseModel):
        age: int

    with pytest.raises(ValidationError) as exc_info:
        Model(age="not-an-int")  # type: ignore

    result = pydantic_error_to_form_validation_errors(
        exc_info.value, key_map={"company_id": "company"}
    )
    assert isinstance(result, FormValidationError)
    assert "age" in result.errors


# ── html_safe_json ────────────────────────────────────────────────────────────


def test_html_safe_json_returns_markup():
    assert isinstance(html_safe_json("hello"), Markup)


def test_html_safe_json_plain_string():
    assert html_safe_json("hello") == '"hello"'


def test_html_safe_json_escapes_lt():
    result = html_safe_json("<tag>")
    assert "<" not in result
    assert "\\u003c" in result


def test_html_safe_json_escapes_gt():
    result = html_safe_json("<tag>")
    assert ">" not in result
    assert "\\u003e" in result


def test_html_safe_json_escapes_ampersand():
    result = html_safe_json("a&b")
    assert "&" not in result
    assert "\\u0026" in result


def test_html_safe_json_escapes_single_quote():
    result = html_safe_json("it's")
    assert "'" not in result
    assert "\\u0027" in result


def test_html_safe_json_closing_script_tag():
    # The primary XSS vector: a value containing </script> must not break out
    # of the enclosing <script> block when embedded via | tojson | safe.
    result = html_safe_json("</script><script>alert(1)</script>")
    assert "</script>" not in result
    assert "<script>" not in result
    assert "\\u003c/script\\u003e" in result


def test_html_safe_json_bool():
    assert html_safe_json(True) == "true"
    assert html_safe_json(False) == "false"


def test_html_safe_json_integer():
    assert html_safe_json(42) == "42"


def test_html_safe_json_none():
    assert html_safe_json(None) == "null"


def test_html_safe_json_list():
    assert html_safe_json([1, 2, 3]) == "[1, 2, 3]"


def test_html_safe_json_dict():
    result = html_safe_json({"key": "value"})
    assert '"key"' in result
    assert '"value"' in result


def test_html_safe_json_non_serializable_uses_str_fallback():
    class Custom:
        def __str__(self):
            return "custom-repr"

    result = html_safe_json(Custom())
    assert "custom-repr" in result


# ── FormValidationError constructor validation ────────────────────────────────


def test_form_validation_error_errors_must_be_dict():
    with pytest.raises(TypeError, match="errors must be a dict"):
        FormValidationError(["not", "a", "dict"])  # type: ignore[arg-type]
