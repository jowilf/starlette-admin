import datetime

import arrow
import pytest
from pydantic import ConfigDict
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin import (
    BaseAdmin,
    DateField,
    DateTimeField,
    I18nConfig,
    IntegerField,
    StringField,
    TimeField,
    TimezoneConfig,
)
from starlette_admin.fields import ArrowField
from starlette_admin.i18n import (
    SUPPORTED_LOCALES,
    get_database_timezone,
    get_timezone,
    get_timezone_display_name,
    set_database_timezone,
    set_timezone,
)

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView


class Post(TinydbBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str = ""
    time: datetime.time | None = None
    date: datetime.date | None = None
    created_at: datetime.datetime | None = None
    arrow_: arrow.Arrow | None = None


class PostView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        TimeField("time"),
        DateField("date"),
        DateTimeField("created_at"),
        ArrowField("arrow_"),
    ]
    row_actions = []


@pytest.mark.parametrize(
    "locale,expected_text",
    [
        ("de", "Post erstellen"),
        ("en", "New Post"),
        ("fr", "Nouveau Post"),
        ("ru", "Добавить Post"),
        ("tr", "Yeni Post"),
        ("pt", "Novo(a) Post"),
        ("zh", "新增Post"),
        ("zh_Hant", "新增Post"),
    ],
)
def test_default_locale(locale, expected_text):
    admin = BaseAdmin(
        i18n_config=I18nConfig(
            default_locale=locale, language_switcher=SUPPORTED_LOCALES
        )
    )
    app = Starlette()
    admin.add_view(PostView(Post))
    admin.mount_to(app)
    client = TestClient(app)
    response = client.get("/admin/post/list")
    assert response.text.count(f'<html lang="{locale}"') == 1
    assert expected_text in response.text


def test_extract_locale_from_cookies():
    admin = BaseAdmin(i18n_config=I18nConfig(default_locale="en"))
    app = Starlette()
    admin.add_view(PostView(Post))
    admin.mount_to(app)
    client = TestClient(app, cookies={"language": "fr"})
    response = client.get("/admin/post/list")
    assert response.text.count('<html lang="fr"') == 1
    assert "Nouveau Post" in response.text


def test_language_switcher():
    admin = BaseAdmin(
        i18n_config=I18nConfig(
            default_locale="en", language_switcher=["en", "fr", "de"]
        )
    )
    app = Starlette()
    admin.add_view(PostView(Post))
    admin.mount_to(app)
    client = TestClient(app)
    response = client.get("/admin/post/list")
    assert response.status_code == 200
    assert "fr" in response.text


def test_timezone_config():
    admin = BaseAdmin(
        timezone_config=TimezoneConfig(
            default_timezone="Europe/Paris",
            database_timezone="UTC",
        )
    )
    app = Starlette()
    admin.add_view(PostView(Post))
    admin.mount_to(app)
    client = TestClient(app)
    response = client.get("/admin/post/list")
    assert response.status_code == 200


def test_get_set_timezone():
    original = get_timezone()
    set_timezone("America/New_York")
    assert get_timezone() == "America/New_York"
    set_timezone(original)


def test_get_set_database_timezone():
    original = get_database_timezone()
    set_database_timezone("UTC")
    assert get_database_timezone() == "UTC"
    set_database_timezone(original)


def test_get_timezone_display_name():
    name = get_timezone_display_name("UTC")
    assert name is not None


def test_get_timezone_display_name_with_offset():
    from starlette_admin.i18n import get_timezone_display_name as gdn

    name = gdn("Europe/Paris", show_offset=True)
    assert "UTC" in name


def test_get_countries_list():
    from starlette_admin.i18n import get_countries_list

    countries = get_countries_list()
    assert len(countries) > 0
    assert all(len(c) == 2 for c in countries)


def test_get_currencies_list():
    from starlette_admin.i18n import get_currencies_list

    currencies = get_currencies_list()
    assert len(currencies) > 0


def test_format_datetime():
    import datetime

    from starlette_admin.i18n import format_datetime

    dt = datetime.datetime(2024, 3, 15, 10, 30, 0)
    result = format_datetime(dt)
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_date():
    import datetime

    from starlette_admin.i18n import format_date

    d = datetime.date(2024, 3, 15)
    result = format_date(d)
    assert isinstance(result, str)


def test_format_time():
    import datetime

    from starlette_admin.i18n import format_time

    t = datetime.time(10, 30, 0)
    result = format_time(t)
    assert isinstance(result, str)


def test_get_tzinfo():
    from starlette_admin.i18n import get_tzinfo, set_timezone

    set_timezone("UTC")
    tz = get_tzinfo()
    assert tz is not None


def test_get_database_tzinfo():
    from starlette_admin.i18n import get_database_tzinfo, set_database_timezone

    set_database_timezone("UTC")
    tz = get_database_tzinfo()
    assert tz is not None


def test_is_timezone_conversion_enabled():
    from starlette_admin.i18n import is_timezone_conversion_enabled, set_timezone

    # After setting a timezone, conversion should be enabled
    set_timezone("UTC")
    assert is_timezone_conversion_enabled() is True


def test_validate_timezone_invalid_returns_default():
    from starlette_admin.i18n import _validate_timezone

    result = _validate_timezone("Not/A/Timezone", "UTC")
    assert result == "UTC"


def test_language_header_based_locale():
    """Locale detection via HTTP header (language_header_name config)."""
    from starlette_admin.i18n import I18nConfig

    admin = BaseAdmin(
        i18n_config=I18nConfig(
            default_locale="en",
            language_switcher=SUPPORTED_LOCALES,
            language_header_name="X-Language",
        )
    )
    app = Starlette()
    admin.add_view(PostView(Post))
    admin.mount_to(app)
    client = TestClient(app)
    response = client.get("/admin/post/list", headers={"X-Language": "fr"})
    assert response.status_code == 200
    assert '<html lang="fr"' in response.text


def test_timezone_cookie_override():
    """Timezone cookie should override the default."""
    from starlette_admin.i18n import TimezoneConfig

    admin = BaseAdmin(
        timezone_config=TimezoneConfig(
            default_timezone="UTC",
            database_timezone="UTC",
            timezone_cookie_name="tz",
        )
    )
    app = Starlette()
    admin.add_view(PostView(Post))
    admin.mount_to(app)
    client = TestClient(app, cookies={"tz": "Europe/Paris"})
    response = client.get("/admin/post/list")
    assert response.status_code == 200
