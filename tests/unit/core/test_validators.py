"""Unit tests for starlette_admin.validators."""

import datetime
import io
import re
from unittest.mock import MagicMock

import pytest
from starlette_admin.validators import (
    any_of,
    color,
    date_range,
    disallow,
    email,
    file_size,
    file_type,
    image_size,
    ip_address,
    items,
    length,
    mac_address,
    none_of,
    number_gt,
    number_lt,
    number_range,
    regexp,
    slug,
    url,
    uuid,
    valid_image,
)


def _make_field(name: str = "field"):
    # Mock() treats `name` as a constructor keyword, so set it as an attribute
    mock = MagicMock()
    mock.name = name
    return mock


def _make_upload(
    content: bytes = b"data", filename: str = "f.txt", content_type: str = "text/plain"
):
    mock = MagicMock()
    mock.file = io.BytesIO(content)
    mock.filename = filename
    mock.content_type = content_type
    mock.size = len(content)
    return mock


# ── length ───────────────────────────────────────────────────────────────────


def test_length_requires_min_or_max():
    with pytest.raises(AssertionError):
        length()


def test_length_min_only_rejects_short_value():
    validate = length(min=3)
    with pytest.raises(ValueError, match="at least 3 characters"):
        validate(None, _make_field(), "ab")


def test_length_max_only_rejects_long_value():
    validate = length(max=3)
    with pytest.raises(ValueError, match="at most 3 characters"):
        validate(None, _make_field(), "abcd")


def test_length_both_bounds_rejects_out_of_range():
    validate = length(min=2, max=4)
    with pytest.raises(ValueError, match="between 2 and 4 characters"):
        validate(None, _make_field(), "a")


def test_length_custom_message():
    validate = length(min=2, message="too short")
    with pytest.raises(ValueError, match="too short"):
        validate(None, _make_field(), "a")


def test_length_accepts_value_in_range():
    validate = length(min=2, max=4)
    assert validate(None, _make_field(), "abc") is None


# ── number_range ─────────────────────────────────────────────────────────────


def test_number_range_requires_min_or_max():
    with pytest.raises(AssertionError):
        number_range()


def test_number_range_min_only_rejects_low_value():
    validate = number_range(min=10)
    with pytest.raises(ValueError, match="at least 10"):
        validate(None, _make_field(), 5)


def test_number_range_max_only_rejects_high_value():
    validate = number_range(max=10)
    with pytest.raises(ValueError, match="at most 10"):
        validate(None, _make_field(), 15)


def test_number_range_both_bounds_rejects_out_of_range():
    validate = number_range(min=1, max=10)
    with pytest.raises(ValueError, match="between 1 and 10"):
        validate(None, _make_field(), 20)


def test_number_range_custom_message():
    validate = number_range(min=1, message="out of range")
    with pytest.raises(ValueError, match="out of range"):
        validate(None, _make_field(), 0)


def test_number_range_accepts_value_in_range():
    validate = number_range(min=1, max=10)
    assert validate(None, _make_field(), 5) is None


# ── number_gt / number_lt ────────────────────────────────────────────────────


def test_number_gt_rejects_lower_value():
    validate = number_gt(min=10)
    with pytest.raises(ValueError, match="greater than 10"):
        validate(None, _make_field(), 5)


def test_number_gt_rejects_equal_value():
    validate = number_gt(min=10)
    with pytest.raises(ValueError, match="greater than 10"):
        validate(None, _make_field(), 10)


def test_number_gt_custom_message():
    validate = number_gt(min=10, message="too low")
    with pytest.raises(ValueError, match="too low"):
        validate(None, _make_field(), 10)


def test_number_gt_accepts_greater_value():
    validate = number_gt(min=10)
    assert validate(None, _make_field(), 11) is None


def test_number_lt_rejects_higher_value():
    validate = number_lt(max=10)
    with pytest.raises(ValueError, match="less than 10"):
        validate(None, _make_field(), 15)


def test_number_lt_rejects_equal_value():
    validate = number_lt(max=10)
    with pytest.raises(ValueError, match="less than 10"):
        validate(None, _make_field(), 10)


def test_number_lt_custom_message():
    validate = number_lt(max=10, message="too high")
    with pytest.raises(ValueError, match="too high"):
        validate(None, _make_field(), 10)


def test_number_lt_accepts_lower_value():
    validate = number_lt(max=10)
    assert validate(None, _make_field(), 9) is None


# ── date_range ───────────────────────────────────────────────────────────────


def test_date_range_requires_min_or_max():
    with pytest.raises(AssertionError):
        date_range()


def test_date_range_min_only_rejects_earlier_value():
    validate = date_range(min=datetime.date(2024, 1, 1))
    with pytest.raises(ValueError, match="not before 2024-01-01"):
        validate(None, _make_field(), datetime.date(2023, 12, 31))


def test_date_range_max_only_rejects_later_value():
    validate = date_range(max=datetime.date(2024, 1, 1))
    with pytest.raises(ValueError, match="not after 2024-01-01"):
        validate(None, _make_field(), datetime.date(2024, 1, 2))


def test_date_range_both_bounds_rejects_out_of_range():
    validate = date_range(min=datetime.date(2024, 1, 1), max=datetime.date(2024, 6, 1))
    with pytest.raises(ValueError, match="between 2024-01-01 and 2024-06-01"):
        validate(None, _make_field(), datetime.date(2024, 7, 1))


def test_date_range_accepts_callable_bound():
    validate = date_range(min=datetime.date.today)
    with pytest.raises(ValueError, match="not before"):
        validate(None, _make_field(), datetime.date(2000, 1, 1))
    assert validate(None, _make_field(), datetime.date.today()) is None


def test_date_range_custom_message():
    validate = date_range(min=datetime.date(2024, 1, 1), message="too early")
    with pytest.raises(ValueError, match="too early"):
        validate(None, _make_field(), datetime.date(2023, 1, 1))


def test_date_range_accepts_value_in_range():
    validate = date_range(min=datetime.date(2024, 1, 1), max=datetime.date(2024, 6, 1))
    assert validate(None, _make_field(), datetime.date(2024, 3, 1)) is None


# ── regexp ───────────────────────────────────────────────────────────────────


def test_regexp_rejects_non_matching_value():
    validate = regexp(r"^[0-9]+$")
    with pytest.raises(ValueError, match="Invalid input"):
        validate(None, _make_field(), "abc")


def test_regexp_accepts_precompiled_pattern():
    validate = regexp(re.compile(r"^[a-z]+$"))
    assert validate(None, _make_field(), "abc") is None


def test_regexp_custom_message():
    validate = regexp(r"^[0-9]+$", message="digits only")
    with pytest.raises(ValueError, match="digits only"):
        validate(None, _make_field(), "abc")


def test_regexp_accepts_matching_value():
    validate = regexp(r"^[0-9]+$")
    assert validate(None, _make_field(), "123") is None


# ── disallow ─────────────────────────────────────────────────────────────────


def test_disallow_rejects_matching_value():
    validate = disallow(r"<[^>]+>")
    with pytest.raises(ValueError, match="Invalid input"):
        validate(None, _make_field(), "hello <b>world</b>")


def test_disallow_accepts_precompiled_pattern():
    validate = disallow(re.compile(r"[0-9]"))
    with pytest.raises(ValueError, match="Invalid input"):
        validate(None, _make_field(), "abc1")


def test_disallow_custom_message():
    validate = disallow(r"<[^>]+>", message="no html")
    with pytest.raises(ValueError, match="no html"):
        validate(None, _make_field(), "<script>")


def test_disallow_accepts_non_matching_value():
    validate = disallow(r"<[^>]+>")
    assert validate(None, _make_field(), "hello world") is None


# ── mac_address ──────────────────────────────────────────────────────────────


def test_mac_address_rejects_invalid_value():
    validate = mac_address()
    with pytest.raises(ValueError, match="Invalid MAC address"):
        validate(None, _make_field(), "not-a-mac")


def test_mac_address_rejects_mixed_separators():
    validate = mac_address()
    with pytest.raises(ValueError, match="Invalid MAC address"):
        validate(None, _make_field(), "01:23-45:67-89:ab")


def test_mac_address_custom_message():
    validate = mac_address(message="bad mac")
    with pytest.raises(ValueError, match="bad mac"):
        validate(None, _make_field(), "not-a-mac")


def test_mac_address_accepts_colon_separated_value():
    validate = mac_address()
    assert validate(None, _make_field(), "01:23:45:67:89:AB") is None


def test_mac_address_accepts_hyphen_separated_value():
    validate = mac_address()
    assert validate(None, _make_field(), "01-23-45-67-89-ab") is None


# ── slug ─────────────────────────────────────────────────────────────────────


def test_slug_rejects_invalid_value():
    validate = slug()
    with pytest.raises(ValueError, match="Invalid slug"):
        validate(None, _make_field(), "Hello World")


def test_slug_rejects_leading_hyphen():
    validate = slug()
    with pytest.raises(ValueError, match="Invalid slug"):
        validate(None, _make_field(), "-hello")


def test_slug_rejects_underscore_by_default():
    validate = slug()
    with pytest.raises(ValueError, match="Invalid slug"):
        validate(None, _make_field(), "hello_world")


def test_slug_accepts_underscore_when_allowed():
    validate = slug(allow_underscores=True)
    assert validate(None, _make_field(), "hello_world-2") is None


def test_slug_custom_message():
    validate = slug(message="bad slug")
    with pytest.raises(ValueError, match="bad slug"):
        validate(None, _make_field(), "Hello")


def test_slug_accepts_valid_value():
    validate = slug()
    assert validate(None, _make_field(), "hello-world-2") is None


# ── color ────────────────────────────────────────────────────────────────────


def test_color_rejects_unknown_format():
    with pytest.raises(AssertionError):
        color(formats=("cmyk",))


def test_color_rejects_invalid_value():
    validate = color()
    with pytest.raises(ValueError, match="Invalid color"):
        validate(None, _make_field(), "not-a-color")


def test_color_rejects_format_not_enabled():
    validate = color()
    with pytest.raises(ValueError, match="Invalid color"):
        validate(None, _make_field(), "rgb(255, 0, 0)")


def test_color_accepts_hex_values():
    validate = color()
    for value in ("#fff", "#ffff", "#a1b2c3", "#A1B2C3D4"):
        assert validate(None, _make_field(), value) is None


def test_color_accepts_rgb_values():
    validate = color(formats=("rgb",))
    assert validate(None, _make_field(), "rgb(255, 0, 0)") is None
    assert validate(None, _make_field(), "rgba(0, 128, 255, 0.5)") is None


def test_color_rejects_rgb_component_over_255():
    validate = color(formats=("rgb",))
    with pytest.raises(ValueError, match="Invalid color"):
        validate(None, _make_field(), "rgb(256, 0, 0)")


def test_color_accepts_hsl_values():
    validate = color(formats=("hsl",))
    assert validate(None, _make_field(), "hsl(120, 50%, 50%)") is None
    assert validate(None, _make_field(), "hsla(120, 50%, 50%, 0.3)") is None


def test_color_custom_message():
    validate = color(message="bad color")
    with pytest.raises(ValueError, match="bad color"):
        validate(None, _make_field(), "red")


# ── email ────────────────────────────────────────────────────────────────────


def test_email_rejects_invalid_address():
    validate = email()
    with pytest.raises(ValueError, match="Invalid email address"):
        validate(None, _make_field(), "not-an-email")


def test_email_custom_message():
    validate = email(message="bad email")
    with pytest.raises(ValueError, match="bad email"):
        validate(None, _make_field(), "not-an-email")


def test_email_accepts_valid_address():
    validate = email()
    assert validate(None, _make_field(), "user@example.com") is None


# ── url ──────────────────────────────────────────────────────────────────────


def test_url_rejects_invalid_url():
    validate = url()
    with pytest.raises(ValueError, match="Invalid URL"):
        validate(None, _make_field(), "not a url")


def test_url_custom_message():
    validate = url(message="bad url")
    with pytest.raises(ValueError, match="bad url"):
        validate(None, _make_field(), "not a url")


def test_url_accepts_valid_url():
    validate = url()
    assert validate(None, _make_field(), "https://example.com/path") is None


def test_url_rejects_url_without_host():
    validate = url()
    with pytest.raises(ValueError, match="Invalid URL"):
        validate(None, _make_field(), "http://")


def test_url_accepts_default_schemes():
    validate = url()
    assert validate(None, _make_field(), "ftp://example.com") is None
    assert validate(None, _make_field(), "ftps://example.com") is None


def test_url_rejects_disallowed_scheme():
    validate = url()
    with pytest.raises(ValueError, match="Invalid URL"):
        validate(None, _make_field(), "gopher://example.com")


def test_url_accepts_custom_schemes():
    validate = url(schemes=["gopher"])
    assert validate(None, _make_field(), "gopher://example.com") is None


def test_url_accepts_any_scheme_when_schemes_is_none():
    validate = url(schemes=None)
    assert validate(None, _make_field(), "gopher://example.com") is None


def test_url_accepts_localhost():
    validate = url()
    assert validate(None, _make_field(), "http://localhost:8000/path") is None


def test_url_accepts_ipv4_host():
    validate = url()
    assert validate(None, _make_field(), "http://192.168.0.1") is None


def test_url_accepts_ipv6_host():
    validate = url()
    assert validate(None, _make_field(), "http://[::1]:8080") is None


def test_url_rejects_host_without_valid_tld():
    validate = url()
    with pytest.raises(ValueError, match="Invalid URL"):
        validate(None, _make_field(), "http://example.c")


def test_url_accepts_internationalized_domain():
    validate = url()
    assert validate(None, _make_field(), "http://éxample.com") is None


def test_url_rejects_value_over_max_length():
    validate = url(max_length=10)
    with pytest.raises(ValueError, match="Invalid URL"):
        validate(None, _make_field(), "https://example.com/path")


def test_url_rejects_control_characters():
    validate = url()
    with pytest.raises(ValueError, match="Invalid URL"):
        validate(None, _make_field(), "https://example.com/\npath")


def test_url_rejects_host_without_dot():
    validate = url()
    with pytest.raises(ValueError, match="Invalid URL"):
        validate(None, _make_field(), "http://invalidhost")


def test_url_rejects_host_with_label_too_long_for_idna():
    validate = url()
    with pytest.raises(ValueError, match="Invalid URL"):
        validate(None, _make_field(), f"http://{'a' * 64}.com")


def test_url_rejects_malformed_ipv6_host():
    validate = url()
    with pytest.raises(ValueError, match="Invalid URL"):
        validate(None, _make_field(), "http://[::1:80/")


# ── uuid ─────────────────────────────────────────────────────────────────────


def test_uuid_rejects_invalid_value():
    validate = uuid()
    with pytest.raises(ValueError, match="Invalid UUID"):
        validate(None, _make_field(), "not-a-uuid")


def test_uuid_rejects_invalid_version():
    with pytest.raises(AssertionError):
        uuid(version=2)


def test_uuid_rejects_mismatched_version():
    validate = uuid(version=4)
    with pytest.raises(ValueError, match="expected version 4"):
        validate(None, _make_field(), "6fa459ea-ee8a-3ca4-894e-db77e160355e")


def test_uuid_custom_message():
    validate = uuid(message="bad uuid")
    with pytest.raises(ValueError, match="bad uuid"):
        validate(None, _make_field(), "not-a-uuid")


def test_uuid_accepts_valid_value():
    validate = uuid()
    assert validate(None, _make_field(), "6fa459ea-ee8a-4ca4-894e-db77e160355e") is None


def test_uuid_accepts_matching_version():
    validate = uuid(version=3)
    assert validate(None, _make_field(), "6fa459ea-ee8a-3ca4-894e-db77e160355e") is None


# ── ip_address ───────────────────────────────────────────────────────────────


def test_ip_address_rejects_invalid_value():
    validate = ip_address()
    with pytest.raises(ValueError, match="Invalid IP address"):
        validate(None, _make_field(), "not-an-ip")


def test_ip_address_rejects_when_both_families_disabled():
    with pytest.raises(AssertionError):
        ip_address(ipv4=False, ipv6=False)


def test_ip_address_rejects_ipv6_by_default():
    validate = ip_address()
    with pytest.raises(ValueError, match="Invalid IPv6 address"):
        validate(None, _make_field(), "::1")


def test_ip_address_rejects_ipv4_when_disabled():
    validate = ip_address(ipv4=False, ipv6=True)
    with pytest.raises(ValueError, match="Invalid IPv4 address"):
        validate(None, _make_field(), "192.168.0.1")


def test_ip_address_custom_message():
    validate = ip_address(message="bad ip")
    with pytest.raises(ValueError, match="bad ip"):
        validate(None, _make_field(), "not-an-ip")


def test_ip_address_accepts_valid_ipv4():
    validate = ip_address()
    assert validate(None, _make_field(), "192.168.0.1") is None


def test_ip_address_accepts_valid_ipv6():
    validate = ip_address(ipv6=True)
    assert validate(None, _make_field(), "::1") is None


def test_ip_address_accepts_both_when_enabled():
    validate = ip_address(ipv4=True, ipv6=True)
    assert validate(None, _make_field(), "192.168.0.1") is None
    assert validate(None, _make_field(), "::1") is None


# ── any_of ───────────────────────────────────────────────────────────────────


def test_any_of_rejects_value_not_in_collection():
    validate = any_of(["a", "b"])
    with pytest.raises(ValueError, match="must be one of: a, b"):
        validate(None, _make_field(), "c")


def test_any_of_custom_message():
    validate = any_of(["a", "b"], message="not allowed")
    with pytest.raises(ValueError, match="not allowed"):
        validate(None, _make_field(), "c")


def test_any_of_accepts_value_in_collection():
    validate = any_of(["a", "b"])
    assert validate(None, _make_field(), "a") is None


# ── none_of ──────────────────────────────────────────────────────────────────


def test_none_of_rejects_value_in_collection():
    validate = none_of(["a", "b"])
    with pytest.raises(ValueError, match="can't be any of: a, b"):
        validate(None, _make_field(), "a")


def test_none_of_custom_message():
    validate = none_of(["a", "b"], message="reserved value")
    with pytest.raises(ValueError, match="reserved value"):
        validate(None, _make_field(), "a")


def test_none_of_accepts_value_not_in_collection():
    validate = none_of(["a", "b"])
    assert validate(None, _make_field(), "c") is None


# ── items ────────────────────────────────────────────────────────────────────


def test_items_requires_at_least_one_validator():
    with pytest.raises(AssertionError):
        items()


async def test_items_rejects_first_failing_element():
    validate = items(length(min=3))
    with pytest.raises(ValueError, match="at least 3 characters"):
        await validate(None, _make_field(), ["abc", "ab"])


async def test_items_runs_multiple_validators_per_element():
    validate = items(length(min=2), regexp(r"^[a-z]+$"))
    with pytest.raises(ValueError, match="Invalid input"):
        await validate(None, _make_field(), ["ab", "C3"])


async def test_items_awaits_async_validators():
    async def reject_bar(request, field, value):
        if value == "bar":
            raise ValueError("no bar")

    validate = items(reject_bar)
    with pytest.raises(ValueError, match="no bar"):
        await validate(None, _make_field(), ["foo", "bar"])


async def test_items_accepts_all_valid_elements():
    validate = items(length(min=2))
    assert await validate(None, _make_field(), ["ab", "abc"]) is None


# ── file_size ────────────────────────────────────────────────────────────────


def test_file_size_rejects_upload_over_limit():
    validate = file_size(max_size=5)
    upload = _make_upload(b"toolarge")
    with pytest.raises(ValueError, match="File is too large"):
        validate(None, _make_field(), upload)


def test_file_size_custom_message():
    validate = file_size(max_size=5, message="too big")
    upload = _make_upload(b"toolarge")
    with pytest.raises(ValueError, match="too big"):
        validate(None, _make_field(), upload)


def test_file_size_accepts_upload_within_limit():
    validate = file_size(max_size=100)
    upload = _make_upload(b"small")
    assert validate(None, _make_field(), upload) is None


# ── file_type ────────────────────────────────────────────────────────────────


def test_file_type_rejects_unmatched_extension():
    validate = file_type(".pdf")
    upload = _make_upload(filename="doc.txt", content_type="text/plain")
    with pytest.raises(ValueError, match="File type is not allowed"):
        validate(None, _make_field(), upload)


def test_file_type_accepts_matching_extension():
    validate = file_type(".pdf")
    upload = _make_upload(filename="doc.pdf", content_type="application/pdf")
    assert validate(None, _make_field(), upload) is None


def test_file_type_accepts_matching_wildcard_content_type():
    validate = file_type("image/*")
    upload = _make_upload(filename="photo.png", content_type="image/png")
    assert validate(None, _make_field(), upload) is None


def test_file_type_accepts_exact_content_type():
    validate = file_type("application/pdf")
    upload = _make_upload(filename="doc.pdf", content_type="application/pdf")
    assert validate(None, _make_field(), upload) is None


def test_file_type_custom_message():
    validate = file_type(".pdf", message="pdf only")
    upload = _make_upload(filename="doc.txt", content_type="text/plain")
    with pytest.raises(ValueError, match="pdf only"):
        validate(None, _make_field(), upload)


# ── valid_image ──────────────────────────────────────────────────────────────


def test_valid_image_rejects_non_image_content():
    validate = valid_image()
    upload = _make_upload(b"not an image")
    with pytest.raises(ValueError, match="Upload a valid image file"):
        validate(None, _make_field(), upload)


def test_valid_image_custom_message():
    validate = valid_image(message="bad image")
    upload = _make_upload(b"not an image")
    with pytest.raises(ValueError, match="bad image"):
        validate(None, _make_field(), upload)


def test_valid_image_accepts_real_image():
    validate = valid_image()
    upload = _make_image_upload()
    assert validate(None, _make_field(), upload) is None
    assert upload.file.tell() == 0


# ── image_size ───────────────────────────────────────────────────────────────


def _make_image_upload(width: int = 10, height: int = 10):
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height)).save(buffer, format="PNG")
    return _make_upload(buffer.getvalue(), filename="img.png", content_type="image/png")


def test_image_size_requires_at_least_one_bound():
    with pytest.raises(AssertionError):
        image_size()


def test_image_size_rejects_non_image_content():
    validate = image_size(min_width=1)
    upload = _make_upload(b"not an image")
    with pytest.raises(ValueError, match="Upload a valid image file"):
        validate(None, _make_field(), upload)


def test_image_size_rejects_width_below_min():
    validate = image_size(min_width=20)
    with pytest.raises(ValueError, match="width must be at least 20"):
        validate(None, _make_field(), _make_image_upload(width=10))


def test_image_size_rejects_width_above_max():
    validate = image_size(max_width=5)
    with pytest.raises(ValueError, match="width must be at most 5"):
        validate(None, _make_field(), _make_image_upload(width=10))


def test_image_size_rejects_height_below_min():
    validate = image_size(min_height=20)
    with pytest.raises(ValueError, match="height must be at least 20"):
        validate(None, _make_field(), _make_image_upload(height=10))


def test_image_size_rejects_height_above_max():
    validate = image_size(max_height=5)
    with pytest.raises(ValueError, match="height must be at most 5"):
        validate(None, _make_field(), _make_image_upload(height=10))


def test_image_size_custom_message():
    validate = image_size(min_width=20, message="wrong size")
    with pytest.raises(ValueError, match="wrong size"):
        validate(None, _make_field(), _make_image_upload(width=10))


def test_image_size_resets_file_position():
    validate = image_size(min_width=1)
    upload = _make_image_upload()
    assert validate(None, _make_field(), upload) is None
    assert upload.file.tell() == 0


def test_image_size_accepts_image_within_bounds():
    validate = image_size(min_width=5, min_height=5, max_width=20, max_height=20)
    assert validate(None, _make_field(), _make_image_upload(10, 10)) is None
