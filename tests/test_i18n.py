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
)
from starlette_admin.fields import ArrowField
from starlette_admin.i18n import SUPPORTED_LOCALES

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


@pytest.mark.parametrize(
    "locale,expected_text",
    [("en", "New Post"), ("fr", "Créer Post"), ("ru", "Добавить Post")],
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
    admin.add_view(PostView())
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
    assert response.json()["items"] == [
        {
            "_detail_url": "http://testserver/admin/post/detail/1",
            "_edit_url": "http://testserver/admin/post/edit/1",
            "_repr": "1",
            "arrow_": _arrow.humanize(locale="fr"),
            "created_at": "6 janv. 2023, 16:12:16",
            "date": "6 janv. 2023",
            "id": 1,
            "time": "16:12:16",
            "title": "This is important.",
        }
    ]
    assert client.get("admin/post/edit/1").status_code == 200
