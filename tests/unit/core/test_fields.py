"""Unit tests for starlette_admin.fields."""

import datetime
import decimal
import re
from decimal import Decimal
from unittest.mock import MagicMock

import arrow
import pytest
from starlette_admin import BooleanField, IntegerField, StringField
from starlette_admin.fields import (
    ArrowField,
    CollectionField,
    ComputedField,
    CountryField,
    CurrencyField,
    DateField,
    DateTimeField,
    DecimalField,
    EmailField,
    FileField,
    FloatField,
    ImageField,
    IPAddressField,
    JSONField,
    ListField,
    SlugField,
    TagsField,
    TimeField,
    TimeZoneField,
    URLField,
    UUIDField,
)
from starlette_admin.helpers import to_form_entry
from starlette_admin.types import RequestAction


def make_request(action: RequestAction) -> MagicMock:
    request = MagicMock()
    request.state.action = action
    return request


# ── BaseField helpers ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_create_default_async_callable():
    """get_create_default awaits the result when the callable returns a coroutine."""

    async def async_default():
        return "async-value"

    field = StringField("name", default=async_default)
    result = await field.get_create_default(MagicMock())
    assert result == "async-value"


@pytest.mark.asyncio
async def test_get_create_default_callable_no_args():
    """get_create_default invokes a zero-argument callable."""
    field = StringField("name", default=lambda: "static")
    result = await field.get_create_default(MagicMock())
    assert result == "static"


@pytest.mark.asyncio
async def test_get_create_default_callable_signature_fails():
    """get_create_default falls back to no-arg call when inspect.signature raises."""
    # Built-in functions whose signature cannot be inspected by inspect.signature
    # raise ValueError. We simulate this with a callable whose __signature__
    # property raises ValueError, exercising get_create_default's fallback path.
    import inspect as _inspect

    class _NoSig:
        def __call__(self):
            return "no-sig-value"

        @property
        def __signature__(self):
            raise ValueError("no sig")

    field = StringField("name", default=_NoSig())
    with MagicMock() as req:
        # Verify inspect.signature would actually raise for this object
        try:
            _inspect.signature(field.default)
            sig_raises = False
        except ValueError:
            sig_raises = True
        assert sig_raises, "expected inspect.signature to raise"
        result = await field.get_create_default(req)
    assert result == "no-sig-value"


def test_base_field_dict():
    field = IntegerField("count")
    d = field.dict()
    assert isinstance(d, dict)
    assert d["name"] == "count"


def test_base_field_input_params_returns_string():
    field = StringField("title")
    result = field.input_params()
    assert isinstance(result, str)


def test_base_field_input_params_disabled():
    field = StringField("title", disabled=True)
    assert "disabled" in field.input_params()


# ── BaseField.validate / validators chain ───────────────────────────────────


@pytest.mark.asyncio
async def test_validate_required_raises_on_empty_value():
    field = StringField("title", required=True)
    with pytest.raises(ValueError, match=re.escape("This field is required.")):
        await field.validate(MagicMock(), "")


@pytest.mark.asyncio
async def test_validate_skips_validators_on_empty_optional_value():
    calls = []

    def _record(request, field, value):
        calls.append(value)

    field = StringField("title", validators=[_record])
    await field.validate(MagicMock(), "")
    assert calls == []


@pytest.mark.asyncio
async def test_validate_runs_sync_validators_in_order_and_stops_at_first_error():
    calls = []

    def _first(request, field, value):
        calls.append("first")

    def _second(request, field, value):
        calls.append("second")
        raise ValueError("rejected")

    def _third(request, field, value):
        calls.append("third")

    field = StringField("title", validators=[_first, _second, _third])
    with pytest.raises(ValueError, match="rejected"):
        await field.validate(MagicMock(), "value")
    assert calls == ["first", "second"]


@pytest.mark.asyncio
async def test_validate_awaits_async_validators():
    calls = []

    async def _async_validator(request, field, value):
        calls.append(value)

    field = StringField("title", validators=[_async_validator])
    await field.validate(MagicMock(), "value")
    assert calls == ["value"]


# ── BooleanField ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_boolean_field_parse_form_data_on():
    field = BooleanField("active")
    result = await field.parse_form_data(
        MagicMock(), MagicMock(**{"get.return_value": "on"})
    )
    assert result is True


@pytest.mark.asyncio
async def test_boolean_field_parse_form_data_off():
    field = BooleanField("active")
    result = await field.parse_form_data(
        MagicMock(), MagicMock(**{"get.return_value": None})
    )
    assert result is False


@pytest.mark.asyncio
async def test_boolean_field_serialize_value():
    field = BooleanField("active")
    assert await field.serialize_value(MagicMock(), 1) is True
    assert await field.serialize_value(MagicMock(), 0) is False
    assert await field.serialize_value(MagicMock(), True) is True


# ── DecimalField ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decimal_field_parse_form_data_valid():
    field = DecimalField("amount")
    form = MagicMock(**{"get.return_value": "3.14"})
    result = await field.parse_form_data(MagicMock(), form)
    assert result == decimal.Decimal("3.14")


@pytest.mark.asyncio
async def test_decimal_field_parse_form_data_invalid():
    field = DecimalField("amount")
    form = MagicMock(**{"get.return_value": "not-a-number"})
    result = await field.parse_form_data(MagicMock(), form)
    assert result is None


@pytest.mark.asyncio
async def test_decimal_field_serialize_value():
    field = DecimalField("amount")
    result = await field.serialize_value(MagicMock(), decimal.Decimal("9.99"))
    assert result == "9.99"


# ── DateField ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_date_field_parse_form_data_invalid():
    field = DateField("birthday")
    form = MagicMock(**{"get.return_value": "not-a-date"})
    result = await field.parse_form_data(MagicMock(), form)
    assert result is None


@pytest.mark.asyncio
async def test_date_field_parse_form_data_none():
    field = DateField("birthday")
    form = MagicMock(**{"get.return_value": None})
    result = await field.parse_form_data(MagicMock(), form)
    assert result is None


# ── TimeField ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_time_field_parse_form_data_invalid():
    field = TimeField("alarm")
    form = MagicMock(**{"get.return_value": "not-a-time"})
    result = await field.parse_form_data(MagicMock(), form)
    assert result is None


@pytest.mark.asyncio
async def test_time_field_parse_form_data_none():
    field = TimeField("alarm")
    form = MagicMock(**{"get.return_value": None})
    result = await field.parse_form_data(MagicMock(), form)
    assert result is None


# ── TimeZoneField ─────────────────────────────────────────────────────────────


def test_timezone_field_auto_choices():
    field = TimeZoneField("tz")
    assert field.choices is not None
    assert len(field.choices) > 0
    # Each choice is (value, label)
    assert all(len(c) == 2 for c in field.choices)


def test_timezone_field_explicit_choices():
    choices = [("UTC", "UTC"), ("US/Eastern", "US Eastern")]
    field = TimeZoneField("tz", choices=choices)
    assert field.choices == choices


def test_country_field_instantiation():
    field = CountryField("country")
    assert field.choices_loader is not None
    result = field.choices_loader(None)
    assert isinstance(result, list)
    assert len(result) > 0


def test_currency_field_instantiation():
    field = CurrencyField("currency")
    assert field.choices_loader is not None
    result = field.choices_loader(None)
    assert isinstance(result, list)
    assert len(result) > 0


# ── FileField ─────────────────────────────────────────────────────────────────


def test_file_field_input_params():
    field = FileField("avatar", accept="image/*", multiple=False)
    params = field.input_params()
    assert "image/*" in params


def test_file_field_input_params_multiple():
    field = FileField("photos", multiple=True)
    params = field.input_params()
    assert "multiple" in params


def test_file_field_isvalid_value_none():
    field = FileField("avatar")
    assert field._isvalid_value(None) is False


def test_file_field_isvalid_value_with_url_attr():
    class FakeFile:
        url = "https://example.com/file.jpg"

    field = FileField("avatar")
    assert field._isvalid_value(FakeFile()) is True


def test_file_field_isvalid_value_dict_with_url():
    field = FileField("avatar")
    assert field._isvalid_value({"url": "https://example.com/img.png"}) is True


def test_file_field_isvalid_value_dict_without_url():
    field = FileField("avatar")
    assert field._isvalid_value({"name": "file.jpg"}) is False


# ── DateTimeField ─────────────────────────────────────────────────────────────


def test_datetime_field_input_params():
    field = DateTimeField("created_at")
    params = field.input_params()
    assert "datetime-local" in params


@pytest.mark.asyncio
async def test_datetime_field_parse_form_data_valid():
    field = DateTimeField("created_at")
    form = MagicMock(**{"get.return_value": "2024-03-15T10:30:00"})
    result = await field.parse_form_data(MagicMock(), form)
    assert isinstance(result, datetime.datetime)
    assert result == datetime.datetime(2024, 3, 15, 10, 30, 0)


@pytest.mark.asyncio
async def test_datetime_field_parse_form_data_invalid():
    field = DateTimeField("created_at")
    form = MagicMock(**{"get.return_value": "not-a-datetime"})
    result = await field.parse_form_data(MagicMock(), form)
    assert result is None


@pytest.mark.asyncio
async def test_datetime_field_parse_form_data_no_tz():
    """parse_form_data returns raw naive datetime when tz conversion is disabled."""
    from starlette_admin.i18n import _timezone_conversion_enabled

    _timezone_conversion_enabled.set(False)

    field = DateTimeField("created_at")
    form = MagicMock(**{"get.return_value": "2024-03-15T10:30:00"})
    result = await field.parse_form_data(MagicMock(), form)
    assert result == datetime.datetime(2024, 3, 15, 10, 30, 0)
    assert result.tzinfo is None


@pytest.mark.asyncio
async def test_datetime_field_serialize_no_tz():
    """serialize_value without timezone conversion (default)."""
    from starlette_admin.i18n import _timezone_conversion_enabled

    _timezone_conversion_enabled.set(False)

    field = DateTimeField("created_at")
    dt = datetime.datetime(2024, 3, 15, 10, 30, 0)
    result = await field.serialize_value(make_request(RequestAction.LIST), dt)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_datetime_field_serialize_edit_no_tz():
    """serialize_value EDIT action without timezone conversion."""
    from starlette_admin.i18n import _timezone_conversion_enabled

    _timezone_conversion_enabled.set(False)

    field = DateTimeField("created_at")
    dt = datetime.datetime(2024, 3, 15, 10, 30, 0)
    result = await field.serialize_value(make_request(RequestAction.EDIT), dt)
    assert result == dt.isoformat()


@pytest.mark.asyncio
async def test_datetime_field_serialize_with_tz():
    """serialize_value with timezone conversion enabled."""
    from starlette_admin.i18n import set_database_timezone, set_timezone

    set_timezone("UTC")
    set_database_timezone("UTC")

    field = DateTimeField("created_at")
    dt = datetime.datetime(2024, 3, 15, 10, 30, 0)
    result = await field.serialize_value(make_request(RequestAction.LIST), dt)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_datetime_field_serialize_edit_with_tz():
    """serialize_value EDIT action with timezone conversion returns naive isoformat."""
    from starlette_admin.i18n import set_database_timezone, set_timezone

    set_timezone("UTC")
    set_database_timezone("UTC")

    field = DateTimeField("created_at")
    dt = datetime.datetime(2024, 3, 15, 10, 30, 0)
    result = await field.serialize_value(make_request(RequestAction.EDIT), dt)
    assert "2024-03-15" in result
    assert "T" in result


@pytest.mark.asyncio
async def test_datetime_field_parse_with_tz_conversion():
    """parse_form_data with timezone conversion enabled."""
    from starlette_admin.i18n import set_database_timezone, set_timezone

    set_timezone("UTC")
    set_database_timezone("UTC")

    field = DateTimeField("created_at")
    form = MagicMock(**{"get.return_value": "2024-03-15T10:30:00"})
    result = await field.parse_form_data(MagicMock(), form)
    assert isinstance(result, datetime.datetime)


@pytest.mark.asyncio
async def test_datetime_field_serialize_export_no_tz():
    """serialize_value EXPORT action without timezone conversion returns plain ISO."""
    field = DateTimeField("created_at")
    dt = datetime.datetime(2024, 3, 15, 10, 30, 0)
    result = await field.serialize_value(make_request(RequestAction.EXPORT), dt)
    assert result == "2024-03-15T10:30:00"


@pytest.mark.asyncio
async def test_datetime_field_serialize_export_with_tz():
    """serialize_value EXPORT action with timezone conversion enabled converts to UTC ISO."""
    from starlette_admin.i18n import (
        _timezone_conversion_enabled,
        set_database_timezone,
        set_timezone,
    )

    original = _timezone_conversion_enabled.get()
    try:
        set_timezone("America/New_York")
        set_database_timezone("UTC")
        field = DateTimeField("created_at")
        dt = datetime.datetime(2024, 3, 15, 10, 30, 0)
        result = await field.serialize_value(make_request(RequestAction.EXPORT), dt)
        assert result == "2024-03-15T10:30:00+00:00"
    finally:
        _timezone_conversion_enabled.set(original)


@pytest.mark.asyncio
async def test_datetime_field_serialize_export_with_tz_aware_value():
    """serialize_value EXPORT with timezone conversion and tz-aware datetime."""
    from starlette_admin.i18n import (
        _timezone_conversion_enabled,
        set_database_timezone,
        set_timezone,
    )

    original = _timezone_conversion_enabled.get()
    try:
        set_timezone("America/New_York")
        set_database_timezone("America/New_York")
        field = DateTimeField("created_at")
        tz = datetime.timezone(datetime.timedelta(hours=-5))
        dt = datetime.datetime(2024, 3, 15, 10, 30, 0, tzinfo=tz)
        result = await field.serialize_value(make_request(RequestAction.EXPORT), dt)
        assert result == "2024-03-15T15:30:00+00:00"
    finally:
        _timezone_conversion_enabled.set(original)


# ── DateField serialization ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_date_field_serialize_list():
    """serialize_value for LIST action formats the date."""
    field = DateField("birthday")
    d = datetime.date(2024, 3, 15)
    result = await field.serialize_value(make_request(RequestAction.LIST), d)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_date_field_serialize_edit():
    """serialize_value for EDIT returns ISO format."""
    field = DateField("birthday")
    d = datetime.date(2024, 3, 15)
    result = await field.serialize_value(make_request(RequestAction.EDIT), d)
    assert result == "2024-03-15"


@pytest.mark.asyncio
async def test_date_field_serialize_export():
    """serialize_value for EXPORT returns ISO format."""
    field = DateField("birthday")
    d = datetime.date(2024, 3, 15)
    result = await field.serialize_value(make_request(RequestAction.EXPORT), d)
    assert result == "2024-03-15"


# ── TimeField serialization ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_time_field_serialize_list():
    """serialize_value for LIST action formats the time."""
    field = TimeField("alarm")
    t = datetime.time(10, 30, 0)
    result = await field.serialize_value(make_request(RequestAction.LIST), t)
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_time_field_serialize_edit():
    """serialize_value for EDIT returns ISO format."""
    field = TimeField("alarm")
    t = datetime.time(10, 30, 0)
    result = await field.serialize_value(make_request(RequestAction.EDIT), t)
    assert result == "10:30:00"


# ── ArrowField ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_arrow_field_parse_form_data_no_tz():
    """ArrowField parse when timezone conversion is disabled."""
    from starlette_admin.i18n import _timezone_conversion_enabled

    _timezone_conversion_enabled.set(False)

    field = ArrowField("published_at")
    form = MagicMock(**{"get.return_value": "2024-03-15T10:30:00"})
    result = await field.parse_form_data(MagicMock(), form)
    assert isinstance(result, arrow.Arrow)


@pytest.mark.asyncio
async def test_arrow_field_parse_form_data_with_tz():
    """ArrowField parse when timezone conversion is enabled."""
    from starlette_admin.i18n import set_database_timezone, set_timezone

    set_timezone("UTC")
    set_database_timezone("UTC")

    field = ArrowField("published_at")
    form = MagicMock(**{"get.return_value": "2024-03-15T10:30:00"})
    result = await field.parse_form_data(MagicMock(), form)
    assert isinstance(result, arrow.Arrow)


@pytest.mark.asyncio
async def test_arrow_field_serialize_no_tz():
    """ArrowField serialize without timezone conversion."""
    from starlette_admin.i18n import _timezone_conversion_enabled

    _timezone_conversion_enabled.set(False)

    field = ArrowField("published_at")
    val = arrow.Arrow(2024, 3, 15, 10, 30, 0)
    result = await field.serialize_value(make_request(RequestAction.LIST), val)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_arrow_field_serialize_no_tz_edit():
    """ArrowField EDIT without timezone conversion returns isoformat."""
    from starlette_admin.i18n import _timezone_conversion_enabled

    _timezone_conversion_enabled.set(False)

    field = ArrowField("published_at")
    val = arrow.Arrow(2024, 3, 15, 10, 30, 0)
    result = await field.serialize_value(make_request(RequestAction.EDIT), val)
    assert "2024-03-15" in result


@pytest.mark.asyncio
async def test_arrow_field_serialize_with_tz():
    """ArrowField serialize with timezone conversion."""
    from starlette_admin.i18n import set_database_timezone, set_timezone

    set_timezone("UTC")
    set_database_timezone("UTC")

    field = ArrowField("published_at")
    val = arrow.Arrow(2024, 3, 15, 10, 30, 0)
    result = await field.serialize_value(make_request(RequestAction.LIST), val)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_arrow_field_serialize_edit_with_tz():
    """ArrowField EDIT with timezone conversion."""
    from starlette_admin.i18n import set_database_timezone, set_timezone

    set_timezone("UTC")
    set_database_timezone("UTC")

    field = ArrowField("published_at")
    val = arrow.Arrow(2024, 3, 15, 10, 30, 0)
    result = await field.serialize_value(make_request(RequestAction.EDIT), val)
    assert "2024-03-15" in result


@pytest.mark.asyncio
async def test_arrow_field_parse_form_data_none():
    """ArrowField returns None when the underlying DateTimeField finds no value."""
    from starlette_admin.i18n import (
        _timezone_conversion_enabled,
        set_database_timezone,
        set_timezone,
    )

    _timezone_conversion_enabled.set(True)
    set_timezone("UTC")
    set_database_timezone("UTC")

    field = ArrowField("published_at")
    form = MagicMock(**{"get.return_value": None})
    result = await field.parse_form_data(MagicMock(), form)
    assert result is None


# ── FileField parse_form_data ─────────────────────────────────────────────────


def _make_upload_file(content: bytes):
    """Create a minimal UploadFile-like mock with a .file attribute."""
    import io

    file_obj = io.BytesIO(content)
    mock = MagicMock()
    mock.file = file_obj
    return mock


@pytest.mark.asyncio
async def test_file_field_parse_single_empty():
    """FileField single file: empty upload returns (None, False)."""
    field = FileField("avatar")

    fake_upload = _make_upload_file(b"")  # empty file

    form = MagicMock()
    form.get.side_effect = lambda key, default=None: (
        fake_upload if key == field.id else default
    )

    result, delete = await field.parse_form_data(MagicMock(), form)
    assert result is None
    assert delete is False


@pytest.mark.asyncio
async def test_file_field_parse_delete_flag():
    """FileField: _avatar-delete=on sets should_be_deleted=True."""
    field = FileField("avatar")

    fake_upload = _make_upload_file(b"some content")

    form = MagicMock()
    form.get.side_effect = lambda key, default=None: (
        "on"
        if key == f"_{field.id}-delete"
        else fake_upload
        if key == field.id
        else default
    )

    _result, delete = await field.parse_form_data(MagicMock(), form)
    assert delete is True


@pytest.mark.asyncio
async def test_file_field_parse_with_content():
    """FileField single file: non-empty upload returns (upload, False)."""
    field = FileField("avatar")

    fake_upload = _make_upload_file(b"image data")

    form = MagicMock()
    form.get.side_effect = lambda key, default=None: (
        fake_upload if key == field.id else default
    )

    result, delete = await field.parse_form_data(MagicMock(), form)
    assert result is fake_upload
    assert delete is False


@pytest.mark.asyncio
async def test_file_field_parse_multiple():
    """FileField multiple=True returns list of non-empty uploads."""
    field = FileField("photos", multiple=True)

    empty_upload = _make_upload_file(b"")
    good_upload = _make_upload_file(b"photo data")

    form = MagicMock()
    form.get.return_value = None  # for _photos-delete
    form.getlist.return_value = [empty_upload, good_upload]

    result, _delete = await field.parse_form_data(MagicMock(), form)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] is good_upload


def test_datetime_field_additional_css_links():
    """additional_css_links returns non-empty list for form actions."""
    field = DateTimeField("created_at")
    request = _make_form_request()

    links = field.additional_css_links(request)
    assert isinstance(links, list)
    assert len(links) > 0


def test_datetime_field_additional_css_links_list_action():
    """additional_css_links returns empty list for non-form action."""
    field = DateTimeField("created_at")
    links = field.additional_css_links(make_request(RequestAction.LIST))
    assert links == []


def test_datetime_field_additional_js_links_form():
    """additional_js_links returns links for form actions."""
    field = DateTimeField("created_at")
    request = _make_form_request()

    links = field.additional_js_links(request)
    assert isinstance(links, list)
    assert len(links) > 0


def test_base_field_input_params_via_boolean():
    """BooleanField uses BaseField.input_params() (no override)."""
    field = BooleanField("active")
    params = field.input_params()
    assert isinstance(params, str)


# ── URLField serialize_value ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_url_field_serialize_value_list_strips_disallowed_scheme():
    field = URLField("website")
    result = await field.serialize_value(
        make_request(RequestAction.LIST), "javascript:alert(1)"
    )
    assert result == ""


@pytest.mark.asyncio
async def test_url_field_serialize_value_detail_keeps_allowed_scheme():
    field = URLField("website")
    result = await field.serialize_value(
        make_request(RequestAction.DETAIL), "https://example.com"
    )
    assert result == "https://example.com"


@pytest.mark.asyncio
async def test_url_field_serialize_value_edit_skips_safe_url_check():
    """Only LIST and DETAIL views sanitize values; EDIT views render the raw value directly into the input."""
    field = URLField("website")
    result = await field.serialize_value(
        make_request(RequestAction.EDIT), "javascript:alert(1)"
    )
    assert result == "javascript:alert(1)"


@pytest.mark.asyncio
async def test_url_field_serialize_value_allowed_schemes_none_skips_check():
    field = URLField("website", allowed_schemes=None)
    result = await field.serialize_value(
        make_request(RequestAction.LIST), "javascript:alert(1)"
    )
    assert result == "javascript:alert(1)"


@pytest.mark.asyncio
async def test_url_field_serialize_value_custom_allowed_schemes():
    field = URLField("website", allowed_schemes={"ftp"})
    allowed = await field.serialize_value(
        make_request(RequestAction.LIST), "ftp://example.com"
    )
    disallowed = await field.serialize_value(
        make_request(RequestAction.LIST), "https://example.com"
    )
    assert allowed == "ftp://example.com"
    assert disallowed == ""


@pytest.mark.asyncio
async def test_url_field_rejects_invalid_value_by_default():
    field = URLField("website")
    with pytest.raises(ValueError, match="Invalid URL"):
        await field.validate(MagicMock(), "not-a-url")


@pytest.mark.asyncio
async def test_url_field_accepts_valid_value_by_default():
    field = URLField("website")
    await field.validate(MagicMock(), "https://example.com")


@pytest.mark.asyncio
async def test_url_field_custom_validators_override_default():
    """Passing `validators` explicitly opts out of the default `url()` validator."""
    calls = []

    def _record(request, field, value):
        calls.append(value)

    field = URLField("website", validators=[_record])
    await field.validate(MagicMock(), "not-a-url")
    assert calls == ["not-a-url"]


# ── EmailField ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_email_field_rejects_invalid_value_by_default():
    field = EmailField("email")
    with pytest.raises(ValueError, match="Invalid email address"):
        await field.validate(MagicMock(), "not-an-email")


@pytest.mark.asyncio
async def test_email_field_accepts_valid_value_by_default():
    field = EmailField("email")
    await field.validate(MagicMock(), "user@example.com")


@pytest.mark.asyncio
async def test_email_field_custom_validators_override_default():
    calls = []

    def _record(request, field, value):
        calls.append(value)

    field = EmailField("email", validators=[_record])
    await field.validate(MagicMock(), "not-an-email")
    assert calls == ["not-an-email"]


# ── UUIDField ────────────────────────────────────────────────────────────────


def test_uuid_field_defaults_copy_to_clipboard_to_true():
    field = UUIDField("uuid")
    assert field.copy_to_clipboard is True


@pytest.mark.asyncio
async def test_uuid_field_rejects_invalid_value_by_default():
    field = UUIDField("uuid")
    with pytest.raises(ValueError, match="Invalid UUID"):
        await field.validate(MagicMock(), "not-a-uuid")


@pytest.mark.asyncio
async def test_uuid_field_accepts_valid_value_by_default():
    field = UUIDField("uuid")
    await field.validate(MagicMock(), "6fa459ea-ee8a-4ca4-894e-db77e160355e")


@pytest.mark.asyncio
async def test_uuid_field_enforces_version():
    field = UUIDField("uuid", version=4)
    with pytest.raises(ValueError, match="expected version 4"):
        await field.validate(MagicMock(), "6fa459ea-ee8a-3ca4-894e-db77e160355e")


@pytest.mark.asyncio
async def test_uuid_field_custom_validators_override_default():
    """Passing `validators` explicitly opts out of the default `uuid()` validator."""
    calls = []

    def _record(request, field, value):
        calls.append(value)

    field = UUIDField("uuid", validators=[_record])
    await field.validate(MagicMock(), "not-a-uuid")
    assert calls == ["not-a-uuid"]


# ── IPAddressField ───────────────────────────────────────────────────────────


def test_ip_address_field_defaults_copy_to_clipboard_to_false():
    field = IPAddressField("ip")
    assert field.copy_to_clipboard is False


@pytest.mark.asyncio
async def test_ip_address_field_rejects_invalid_value_by_default():
    field = IPAddressField("ip")
    with pytest.raises(ValueError, match="Invalid IP address"):
        await field.validate(MagicMock(), "not-an-ip")


@pytest.mark.asyncio
async def test_ip_address_field_accepts_ipv4_by_default():
    field = IPAddressField("ip")
    await field.validate(MagicMock(), "192.168.0.1")


@pytest.mark.asyncio
async def test_ip_address_field_rejects_ipv6_by_default():
    field = IPAddressField("ip")
    with pytest.raises(ValueError, match="Invalid IPv6 address"):
        await field.validate(MagicMock(), "::1")


@pytest.mark.asyncio
async def test_ip_address_field_accepts_ipv6_when_enabled():
    field = IPAddressField("ip", ipv6=True)
    await field.validate(MagicMock(), "::1")


@pytest.mark.asyncio
async def test_ip_address_field_custom_validators_override_default():
    """Passing `validators` explicitly opts out of the default `ip_address()` validator."""
    calls = []

    def _record(request, field, value):
        calls.append(value)

    field = IPAddressField("ip", validators=[_record])
    await field.validate(MagicMock(), "not-an-ip")
    assert calls == ["not-an-ip"]


@pytest.mark.asyncio
async def test_tags_field_serialize_value_export_returns_flat_string():
    """TagsField flattens its list into a newline-separated string for EXPORT operations."""
    field = TagsField("tags")
    assert (
        await field.serialize_value(make_request(RequestAction.EXPORT), ["a", "b", "c"])
        == "a\nb\nc"
    )
    assert await field.serialize_value(make_request(RequestAction.EXPORT), None) == ""


@pytest.mark.asyncio
async def test_tags_field_serialize_value_non_export_returns_list():
    """TagsField retains its list value for actions other than export."""
    field = TagsField("tags")
    value = ["a", "b"]
    assert await field.serialize_value(make_request(RequestAction.LIST), value) is value


@pytest.mark.asyncio
async def test_list_field_serialize_value_export_returns_flat_string():
    """ListField flattens its serialized items into a newline-separated string for EXPORT operations."""
    field = ListField(StringField("values"))
    assert (
        await field.serialize_value(make_request(RequestAction.EXPORT), ["a", "b", "c"])
        == "a\nb\nc"
    )
    assert (
        await field.serialize_value(
            make_request(RequestAction.EXPORT), [None, "a", None]
        )
        == "a"
    )


@pytest.mark.asyncio
async def test_list_field_serialize_value_non_export_returns_list():
    """ListField retains its serialized list value for actions other than export."""
    field = ListField(StringField("values"))
    result = await field.serialize_value(make_request(RequestAction.LIST), ["a", "b"])
    assert result == ["a", "b"]


@pytest.mark.asyncio
async def test_list_field_serialize_value_export_json_returns_list():
    """ListField retains its serialized list value for JSON export."""
    from starlette_admin.export import JsonExporter

    request = make_request(RequestAction.EXPORT)
    request.state.export_type = JsonExporter()
    field = ListField(StringField("values"))
    assert await field.serialize_value(request, ["a", "b"]) == ["a", "b"]


@pytest.mark.asyncio
async def test_list_field_parse_import_value_from_list():
    """ListField parses a list of raw values using its inner field."""
    from starlette_admin.importers.base import ImportContext

    field = ListField(StringField("values"))
    ctx = ImportContext(
        fields=[field],
        content=b"",
        view=MagicMock(),
        request=MagicMock(),
    )
    result = await field.parse_import_value(["a", "b"], ctx)
    assert result == ["a", "b"]


@pytest.mark.asyncio
async def test_list_field_parse_import_value_from_string():
    """ListField splits a newline-separated string into individual items."""
    from starlette_admin.importers.base import ImportContext

    field = ListField(StringField("values"))
    ctx = ImportContext(
        fields=[field],
        content=b"",
        view=MagicMock(),
        request=MagicMock(),
    )
    result = await field.parse_import_value("a\nb\n", ctx)
    assert result == ["a", "b"]


@pytest.mark.asyncio
async def test_list_field_parse_import_value_fallback():
    """ListField returns an empty list when encountering unsupported value types."""
    from starlette_admin.importers.base import ImportContext

    field = ListField(StringField("values"))
    ctx = ImportContext(
        fields=[field],
        content=b"",
        view=MagicMock(),
        request=MagicMock(),
    )
    assert await field.parse_import_value(None, ctx) == []
    assert await field.parse_import_value(123, ctx) == []


# ── BaseField.parse_import_value ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_base_field_parse_import_value_list():
    """BaseField processes a list import value as multiple form entries."""
    from starlette_admin.importers.base import ImportContext

    field = StringField("name")
    ctx = ImportContext(
        fields=[field],
        content=b"",
        view=MagicMock(),
        request=MagicMock(),
    )
    assert await field.parse_import_value(["a", "b"], ctx) == "b"


@pytest.mark.asyncio
async def test_base_field_parse_import_value_none():
    """BaseField processes a None import value as an empty form."""
    from starlette_admin.importers.base import ImportContext

    field = StringField("name")
    ctx = ImportContext(
        fields=[field],
        content=b"",
        view=MagicMock(),
        request=MagicMock(),
    )
    assert await field.parse_import_value(None, ctx) is None


# ── BaseField.parse_value ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_parse_value_none_yields_none():
    field = StringField("name")
    assert await field.parse_value(MagicMock(), None) is None


@pytest.mark.asyncio
async def test_parse_value_bool_round_trips():
    field = BooleanField("active")
    assert await field.parse_value(MagicMock(), True) is True
    assert await field.parse_value(MagicMock(), False) is False


@pytest.mark.asyncio
async def test_parse_value_list_round_trips_each_item():
    field = TagsField("tags")
    assert await field.parse_value(MagicMock(), ["a", "b"]) == ["a", "b"]


@pytest.mark.asyncio
async def test_parse_value_dict_uses_json_dumps_not_repr():
    """Regression: a dict/list serialized value must round-trip through
    `json.dumps`, not Python `repr`, so `JSONField.parse_form_data`
    (which calls `json.loads`) can parse it back."""
    field = JSONField("config")
    request = MagicMock()
    result = await field.parse_value(request, {"a": 1, "nested": [1, 2]})
    assert result == {"a": 1, "nested": [1, 2]}


@pytest.mark.asyncio
async def test_parse_import_value_delegates_to_parse_value():
    """`parse_import_value` keeps its public signature but delegates to the
    `parse_value` round-trip primitive."""
    from starlette_admin.importers.base import ImportContext

    field = JSONField("config")
    ctx = ImportContext(
        fields=[field], content=b"", view=MagicMock(), request=MagicMock()
    )
    assert await field.parse_import_value({"a": 1}, ctx) == {"a": 1}


# ── Numeric field parse_import_value validation ────────────────────────────────


@pytest.mark.asyncio
async def test_integer_field_parse_import_value_invalid():
    field = IntegerField("count")
    ctx = MagicMock()
    with pytest.raises(ValueError, match="Invalid integer value"):
        await field.parse_import_value("not-a-number", ctx)


@pytest.mark.asyncio
async def test_decimal_field_parse_import_value_invalid():
    field = DecimalField("amount")
    ctx = MagicMock()
    with pytest.raises(ValueError, match="Invalid decimal value"):
        await field.parse_import_value("not-a-number", ctx)


@pytest.mark.asyncio
async def test_decimal_field_parse_import_value_valid():
    field = DecimalField("amount")
    ctx = MagicMock()
    result = await field.parse_import_value("3.14", ctx)
    assert result == decimal.Decimal("3.14")


@pytest.mark.asyncio
async def test_float_field_parse_import_value_empty():
    field = FloatField("score")
    ctx = MagicMock()
    assert await field.parse_import_value(None, ctx) is None
    assert await field.parse_import_value("", ctx) is None


# ── TagsField export and import operations ─────────────────────────────────────


@pytest.mark.asyncio
async def test_tags_field_serialize_value_export_json_non_list():
    """TagsField serializes a scalar value as a single-item list for JSON export."""
    from starlette_admin.export import JsonExporter

    request = make_request(RequestAction.EXPORT)
    request.state.export_type = JsonExporter()
    field = TagsField("tags")
    assert await field.serialize_value(request, "single") == ["single"]
    assert await field.serialize_value(request, None) == []


@pytest.mark.asyncio
async def test_tags_field_parse_import_value_from_list():
    """TagsField parses a list of raw tag values."""
    from starlette_admin.importers.base import ImportContext

    field = TagsField("tags")
    ctx = ImportContext(
        fields=[field],
        content=b"",
        view=MagicMock(),
        request=MagicMock(),
    )
    assert await field.parse_import_value(["a", "b"], ctx) == ["a", "b"]


@pytest.mark.asyncio
async def test_tags_field_parse_import_value_from_string():
    """TagsField splits a newline-separated string into individual tag values."""
    from starlette_admin.importers.base import ImportContext

    field = TagsField("tags")
    ctx = ImportContext(
        fields=[field],
        content=b"",
        view=MagicMock(),
        request=MagicMock(),
    )
    assert await field.parse_import_value("a\nb\n", ctx) == ["a", "b"]


@pytest.mark.asyncio
async def test_tags_field_parse_import_value_from_non_string():
    """TagsField coerces non-string import values into strings."""
    from starlette_admin.importers.base import ImportContext

    field = TagsField("tags")
    ctx = ImportContext(
        fields=[field],
        content=b"",
        view=MagicMock(),
        request=MagicMock(),
    )
    assert await field.parse_import_value(123, ctx) == []


# ── FileField upload validation / import exclusion ─────────────────────────────


@pytest.mark.asyncio
async def test_file_field_validate_upload_custom_validator():
    """Custom validators execute after `accept` and `max_size` checks, and can cause the upload to fail."""

    def _reject(request, field, upload):
        raise ValueError("nope")

    field = FileField("doc", validators=[_reject])
    with pytest.raises(ValueError, match="nope"):
        await field.validate(None, (_make_upload_file(b"data"), False))


def test_file_field_excluded_from_import_by_default():
    """FileField (and ImageField) are always excluded from import: there's no
    way to reference an uploaded file's bytes from a CSV/Excel/JSON row."""
    field = FileField("doc")
    assert field.exclude_from_import is True


# ── ImageField validation ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_image_field_rejects_invalid_image():
    """ImageField rejects uploads that are not valid images."""
    upload = _make_upload_file(b"not an image")
    field = ImageField("photo")
    with pytest.raises(ValueError, match="Upload a valid image file"):
        await field.validate(None, (upload, False))


# ── RelationField serialization without a view ─────────────────────────────────


# ── IntegerField and DecimalField parse_import_value early-return paths ────────


@pytest.mark.asyncio
async def test_integer_field_parse_import_value_none():
    from starlette_admin.importers.base import ImportContext

    field = IntegerField("count")
    ctx = ImportContext(fields=[], content=b"", view=MagicMock(), request=MagicMock())
    assert await field.parse_import_value(None, ctx) is None


@pytest.mark.asyncio
async def test_integer_field_parse_import_value_empty_string():
    from starlette_admin.importers.base import ImportContext

    field = IntegerField("count")
    ctx = ImportContext(fields=[], content=b"", view=MagicMock(), request=MagicMock())
    assert await field.parse_import_value("", ctx) is None


@pytest.mark.asyncio
async def test_decimal_field_parse_import_value_none():
    from starlette_admin.importers.base import ImportContext

    field = DecimalField("price")
    ctx = ImportContext(fields=[], content=b"", view=MagicMock(), request=MagicMock())
    assert await field.parse_import_value(None, ctx) is None


@pytest.mark.asyncio
async def test_decimal_field_parse_import_value_empty_string():
    from starlette_admin.importers.base import ImportContext

    field = DecimalField("price")
    ctx = ImportContext(fields=[], content=b"", view=MagicMock(), request=MagicMock())
    assert await field.parse_import_value("", ctx) is None


# ── TagsField parse_import_value non-iterable fallback ─────────────────────────


@pytest.mark.asyncio
async def test_tags_field_parse_import_value_non_str_non_list():
    from starlette_admin.importers.base import ImportContext

    field = TagsField("labels")
    request = MagicMock()
    ctx = ImportContext(fields=[], content=b"", view=MagicMock(), request=request)
    result = await field.parse_import_value(42, ctx)
    assert result == []


# ── RelationField serialize_value for export (multiple=True) ───────────────────


@pytest.mark.asyncio
async def test_relation_field_serialize_export_multiple_non_json():
    from unittest.mock import AsyncMock

    from starlette_admin.export import CsvExporter
    from starlette_admin.fields import HasMany
    from starlette_admin.types import RequestAction

    field = HasMany("tags", key="tag")
    foreign_view = MagicMock()
    foreign_view.get_serialized_pk_value = AsyncMock(side_effect=lambda req, v: v)
    view_mock = MagicMock()
    view_mock._find_foreign_view.return_value = foreign_view
    field._view = view_mock

    request = MagicMock()
    request.state.action = RequestAction.EXPORT
    request.state.export_type = CsvExporter()

    result = await field.serialize_value(request, [1, 2, 3])
    assert result == "1\n2\n3"


@pytest.mark.asyncio
async def test_relation_field_serialize_export_multiple_json():
    from unittest.mock import AsyncMock

    from starlette_admin.export import JsonExporter
    from starlette_admin.fields import HasMany
    from starlette_admin.types import RequestAction

    field = HasMany("tags", key="tag")
    foreign_view = MagicMock()
    foreign_view.get_serialized_pk_value = AsyncMock(side_effect=lambda req, v: v)
    view_mock = MagicMock()
    view_mock._find_foreign_view.return_value = foreign_view
    field._view = view_mock

    request = MagicMock()
    request.state.action = RequestAction.EXPORT
    request.state.export_type = JsonExporter()

    result = await field.serialize_value(request, [10, 20])
    assert result == ["10", "20"]


# ── RelationField parse_import_value (all branches) ────────────────────────────


def _make_import_ctx():
    from starlette_admin.importers.base import ImportContext

    return ImportContext(fields=[], content=b"", view=MagicMock(), request=MagicMock())


@pytest.mark.asyncio
async def test_relation_field_parse_import_value_multiple_str():
    from starlette_admin.fields import HasMany

    field = HasMany("tags", key="tag")
    ctx = _make_import_ctx()
    result = await field.parse_import_value("1\n2\n3", ctx)
    assert result == ["1", "2", "3"]


@pytest.mark.asyncio
async def test_relation_field_parse_import_value_multiple_list():
    from starlette_admin.fields import HasMany

    field = HasMany("tags", key="tag")
    ctx = _make_import_ctx()
    result = await field.parse_import_value([10, 20, None], ctx)
    assert result == ["10", "20"]


@pytest.mark.asyncio
async def test_relation_field_parse_import_value_multiple_none():
    from starlette_admin.fields import HasMany

    field = HasMany("tags", key="tag")
    ctx = _make_import_ctx()
    result = await field.parse_import_value(None, ctx)
    assert result == []


@pytest.mark.asyncio
async def test_relation_field_parse_import_value_multiple_other():
    from starlette_admin.fields import HasMany

    field = HasMany("tags", key="tag")
    ctx = _make_import_ctx()
    result = await field.parse_import_value(99, ctx)
    assert result == ["99"]


@pytest.mark.asyncio
async def test_relation_field_parse_import_value_single_none():
    from starlette_admin.fields import HasOne

    field = HasOne("author", key="user")
    ctx = _make_import_ctx()
    result = await field.parse_import_value(None, ctx)
    assert result is None


@pytest.mark.asyncio
async def test_relation_field_parse_import_value_single_empty():
    from starlette_admin.fields import HasOne

    field = HasOne("author", key="user")
    ctx = _make_import_ctx()
    result = await field.parse_import_value("", ctx)
    assert result is None


@pytest.mark.asyncio
async def test_relation_field_parse_import_value_single_value():
    from starlette_admin.fields import HasOne

    field = HasOne("author", key="user")
    ctx = _make_import_ctx()
    result = await field.parse_import_value("42", ctx)
    assert result == "42"


# ── RelationField serialization without a view (single) ────────────────────────


@pytest.mark.asyncio
async def test_relation_field_serialize_without_view_raises():
    """A `RelationField` raises a `RuntimeError` when it is used outside the context of a `BaseModelView`."""
    from starlette_admin.fields import HasOne

    field = HasOne("author", key="user")
    with pytest.raises(RuntimeError, match="has no _view"):
        await field.serialize_value(MagicMock(), MagicMock())


# ── JSONField parse_form_data ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_json_field_parse_form_data_none():
    field = JSONField("data")
    form = MagicMock(**{"get.return_value": None})
    result = await field.parse_form_data(MagicMock(), form)
    assert result is None


# ── CollectionField serialize_value ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_collection_field_serialize_value_missing_subfield():
    field = CollectionField(
        "config", fields=[StringField("key"), IntegerField("value")]
    )
    field._view = MagicMock()
    field._view.can_access_field.return_value = True
    request = make_request(RequestAction.LIST)
    result = await field.serialize_value(request, {"key": "k"})
    assert result == {"key": "k", "value": None}


# ── ComputedField ──────────────────────────────────────────────────────────────


class _FullName(ComputedField):
    def compute(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"


def test_computed_field_defaults():
    field = _FullName("full_name")
    assert field.read_only is True
    assert field.searchable is False
    assert field.orderable is False
    assert field.exclude_from_create is True


@pytest.mark.asyncio
async def test_computed_field_parse_obj():
    field = _FullName("full_name")
    obj = MagicMock(first_name="Ada", last_name="Lovelace")
    result = await field.parse_obj(MagicMock(), obj)
    assert result == "Ada Lovelace"


@pytest.mark.asyncio
async def test_computed_field_parse_form_data_returns_none():
    field = _FullName("full_name")
    result = await field.parse_form_data(MagicMock(), MagicMock())
    assert result is None


@pytest.mark.asyncio
async def test_computed_field_serialize_value_none():
    field = _FullName("full_name")
    result = await field.serialize_value(MagicMock(), None)
    assert result is None


@pytest.mark.asyncio
async def test_computed_field_serialize_value_str():
    field = _FullName("full_name")
    result = await field.serialize_value(MagicMock(), "Ada Lovelace")
    assert result == "Ada Lovelace"


def test_computed_field_compute_not_implemented():
    field = ComputedField("computed")
    with pytest.raises(NotImplementedError):
        field.compute(object())


def test_computed_field_fn_lambda():
    obj = MagicMock(first_name="Ada", last_name="Lovelace")
    field = ComputedField("full_name", fn=lambda o: f"{o.first_name} {o.last_name}")
    assert field.compute(obj) == "Ada Lovelace"


@pytest.mark.asyncio
async def test_computed_field_fn_parse_obj():
    obj = MagicMock(first_name="Ada", last_name="Lovelace")
    field = ComputedField("full_name", fn=lambda o: f"{o.first_name} {o.last_name}")
    result = await field.parse_obj(MagicMock(), obj)
    assert result == "Ada Lovelace"


# ── SlugField ──────────────────────────────────────────────────────────────────


def test_slug_field_is_string_field():
    field = SlugField("slug", populate_from="title")
    assert isinstance(field, StringField)


def test_slug_field_populate_from():
    field = SlugField("slug", populate_from="title")
    assert field.populate_from == "title"


def test_slug_field_defaults():
    field = SlugField("slug", populate_from="title")
    assert field.populate_from == "title"
    assert "field-slug" in field.class_
    assert field.form_template == "fields/form/slug.html"


def test_slug_field_requires_populate_from():
    with pytest.raises(ValueError, match="populate_from"):
        SlugField("slug")


@pytest.mark.asyncio
async def test_slug_field_parse_form_data():
    field = SlugField("slug", populate_from="title")
    form = MagicMock(**{"get.return_value": "my-slug"})
    result = await field.parse_form_data(MagicMock(), form)
    assert result == "my-slug"


# ── IntegerField parse_import_value ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_integer_field_parse_import_value_valid():
    """The `parse_import_value` method returns an integer and executes the debug log branch."""
    field = IntegerField("count")
    result = await field.parse_import_value("42", MagicMock())
    assert result == 42


# ── EnumField additional_css_links / additional_js_links (Select2 integration) ──


def _make_form_request() -> MagicMock:
    """Returns a mock `Request` object where its `action.is_form()` method evaluates to `True`."""
    from starlette_admin.types import RequestAction

    url_obj = MagicMock()
    url_obj.__str__ = lambda _self: "http://test/admin/static/x"
    url_obj.include_query_params.return_value = url_obj

    request = MagicMock()
    request.state.action = RequestAction.CREATE
    request.app.state.ROUTE_NAME = "admin"
    request.url_for.return_value = url_obj
    return request


def test_enum_field_additional_css_links_with_select2():
    """The `additional_css_links` method returns a URL list when `select2` is `True` and the action represents a form."""
    from starlette_admin.fields import EnumField

    field = EnumField("status", choices=[("a", "A")], select2=True)
    request = _make_form_request()
    links = field.additional_css_links(request)
    assert len(links) == 1


def test_enum_field_additional_js_links_with_select2():
    """The `additional_js_links` method returns a URL list when `select2` is `True` and the action represents a form."""
    from starlette_admin.fields import EnumField

    field = EnumField("status", choices=[("a", "A")], select2=True)
    request = _make_form_request()
    links = field.additional_js_links(request)
    assert len(links) == 1


class TestToFormEntry:
    def test_bool_true(self):
        assert to_form_entry(True) == "true"

    def test_bool_false(self):
        assert to_form_entry(False) == "false"

    def test_string(self):
        assert to_form_entry("hello") == "hello"

    def test_integer(self):
        assert to_form_entry(42) == "42"

    def test_float(self):
        assert to_form_entry(3.14) == "3.14"

    def test_decimal(self):
        assert to_form_entry(Decimal("3.14")) == "3.14"

    def test_list(self):
        result = to_form_entry([1, 2, 3])
        assert result == "[1, 2, 3]"

    def test_dict(self):
        result = to_form_entry({"key": "value"})
        assert result == '{"key": "value"}'

    def test_none(self):
        import json

        assert to_form_entry(None) == json.dumps(None)
