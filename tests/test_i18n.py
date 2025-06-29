import datetime

import arrow
import pytest
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
    set_database_timezone,
    set_timezone,
)

from tests.dummy_model_view import DummyBaseModel, DummyModelView


class Post(DummyBaseModel):
    title: str
    time: datetime.time
    date: datetime.date
    created_at: datetime.datetime
    arrow_: arrow.Arrow

    class Config:
        arbitrary_types_allowed = True


class PostView(DummyModelView):
    model = Post
    fields = (
        IntegerField("id"),
        StringField("title"),
        TimeField("time"),
        DateField("date"),
        DateTimeField("created_at"),
        ArrowField("arrow_"),
    )
    row_actions = []


@pytest.mark.parametrize(
    "locale,expected_text",
    [
        ("de", "Post erstellen"),
        ("en", "New Post"),
        ("fr", "Créer Post"),
        ("ru", "Добавить Post"),
        ("tr", "Yeni Post"),
        ("pt", "Novo(a) Post"),
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
    admin.mount_to(app)
    admin.add_view(PostView())
    client = TestClient(app)
    response = client.get("/admin/post/list")
    assert response.text.count(f'<html lang="{locale}">') == 1
    assert expected_text in response.text


def test_extract_locale_from_cookies():
    admin = BaseAdmin(i18n_config=I18nConfig(default_locale="en"))
    app = Starlette()
    admin.mount_to(app)
    admin.add_view(PostView())
    client = TestClient(app, cookies={"language": "fr"})
    response = client.get("/admin/post/list")
    assert response.text.count('<html lang="fr">') == 1
    assert "Créer Post" in response.text


def test_extract_locale_from_headers():
    admin = BaseAdmin(i18n_config=I18nConfig(default_locale="en"))
    app = Starlette()
    admin.mount_to(app)
    admin.add_view(PostView())
    client = TestClient(app)
    response = client.get("/admin/post/list", headers={"Accept-Language": "fr"})
    assert response.text.count('<html lang="fr">') == 1
    assert "Créer Post" in response.text


def test_date_formats():
    admin = BaseAdmin(i18n_config=I18nConfig(default_locale="fr"))
    app = Starlette()
    admin.mount_to(app)
    view = PostView()
    admin.add_view(view)
    client = TestClient(app)
    _arrow = arrow.get("2023-01-06T16:12:16+00:00")
    PostView.db[1] = Post(
        id=1,
        title="This is important.",
        time="16:12:16",
        date="2023-01-06",
        created_at="2023-01-06T16:12:16+00:00",
        arrow_=_arrow,
    )
    response = client.get("admin/api/post?pks=1")
    assert len(response.json()["items"]) == 1
    item0 = response.json()["items"][0]
    del item0["_meta"]
    assert item0 == {
        "arrow_": _arrow.humanize(locale="fr"),
        "created_at": "6 janv. 2023, 16:12:16",
        "date": "6 janv. 2023",
        "id": 1,
        "time": "16:12:16",
        "title": "This is important.",
    }

    assert client.get("admin/post/edit/1").status_code == 200


@pytest.mark.parametrize(
    "database_tz,user_tz,db_datetime,expected_display",
    [
        (
            "UTC",
            "America/New_York",
            "2023-01-06T21:12:16",
            "Jan 6, 2023, 4:12:16\u202fPM",
        ),
        (
            "America/New_York",
            "Asia/Tokyo",
            "2023-01-06T16:12:16",
            "Jan 7, 2023, 6:12:16\u202fAM",
        ),
    ],
)
def test_timezone_integration_with_database_timezone(
    database_tz, user_tz, db_datetime, expected_display
):
    admin = BaseAdmin(
        timezone_config=TimezoneConfig(
            default_timezone="UTC",
            timezone_cookie_name="timezone",
            database_timezone=database_tz,
        ),
    )
    app = Starlette()
    admin.mount_to(app)
    view = PostView()
    admin.add_view(view)
    client = TestClient(app, cookies={"timezone": user_tz})

    PostView.db[1] = Post(
        id=1,
        title="Timezone Test Post",
        time="16:12:16",
        date="2023-01-06",
        created_at=db_datetime,
        arrow_=arrow.get("2023-01-06T16:12:16+00:00"),
    )

    response = client.get("admin/api/post?pks=1")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1

    created_at_display = items[0]["created_at"]
    assert created_at_display == expected_display


def test_timezone_edit_form_display_and_submission():
    admin = BaseAdmin(
        i18n_config=I18nConfig(default_locale="en"),
        timezone_config=TimezoneConfig(
            default_timezone="Asia/Tokyo",
            database_timezone="America/New_York",
        ),
    )
    app = Starlette()
    admin.mount_to(app)
    view = PostView()
    admin.add_view(view)
    client = TestClient(app)

    PostView.db[1] = Post(
        id=1,
        title="Edit Test Post",
        time="16:12:16",
        date="2023-01-06",
        created_at="2023-01-06T20:30:00",
        arrow_=arrow.get("2023-01-06T16:12:16+00:00"),
    )

    response = client.get("/admin/post/edit/1")
    assert response.status_code == 200
    assert "2023-01-07T10:30:00" in response.text

    edit_data = {
        "title": "Updated Edit Test Post",
        "time": "16:12:16",
        "date": "2023-01-06",
        "created_at": "2025-01-08T15:45:00",
    }

    edit_response = client.post("/admin/post/edit/1", data=edit_data)
    assert edit_response.status_code in [200, 302]

    saved_post = PostView.db[1]
    assert saved_post.title == "Updated Edit Test Post"

    # Tokyo 15:45 -> Eastern 01:45 (14 hour difference)
    expected_eastern_time = "2025-01-08 01:45:00"
    assert str(saved_post.created_at) == expected_eastern_time


def test_timezone_functions_with_invalid_timezone():
    set_timezone("Invalid/Timezone")
    assert get_timezone() == "UTC"

    set_database_timezone("Invalid/Database_Timezone")
    assert get_database_timezone() == "UTC"
