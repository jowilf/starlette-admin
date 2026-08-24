---
title: Quickstart
description: Erstellen Sie mit unserem umfassenden Quickstart-Guide in wenigen Minuten
  ein voll funktionsfähiges CRUD-Admin-Interface für FastAPI und Starlette.
source_hash: 19c9639af6caf311e19b134a5042588a3329ca1c3eeb005f000e63d8ac92c7bc
prompt_hash: e74e266b22cedf72eaa794c2ae7a360fd32046953223afb4ffa22b1342d51b63
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/getting-started/quickstart/)
<!-- translation-notice:end -->

# Quickstart

Erstellen Sie in wenigen Minuten ein voll funktionsfähiges CRUD-Admin-Interface für einen Blog, mit automatisch generierten Formularen, Listen, Suche, Import und Export, direkt aus Ihren Datenmodellen gespeist.

## Installation

Installieren Sie die notwendigen Pakete mit Ihrem bevorzugten Paketmanager:

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

!!! note
    Das Paket `fastapi[standard]` enthält die FastAPI-CLI, mit der Sie den Entwicklungsserver durch Ausführen von `fastapi dev` starten können.

## Das vollständige Beispiel

Erstellen Sie eine Datei namens `main.py` und fügen Sie den folgenden Code hinzu:

```python
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


# Note: This can also be replaced by Starlette(lifespan=lifespan)
app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

## Die Anwendung ausführen

Starten Sie den Entwicklungsserver:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Öffnen Sie einen Browser und gehen Sie zu [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

Wählen Sie in der Seitenleiste **Posts** und anschließend **Create** aus. Sie haben jetzt Zugriff auf paginierte List-, Detail-, Create-, Edit- und Delete-Seiten. Das System generiert all diese Interfaces automatisch aus Ihrer Modelldefinition.

## Wie es funktioniert

Die folgenden Abschnitte erklären die zentralen Komponenten der Anwendung.

### Das Modell

```python
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
```

Dieser Code verwendet Standard-SQLAlchemy 2.0. Das Paket starlette-admin liest die Spaltenmetadaten, die diesen Attributen zugeordnet sind, um das exakte HTML-Eingabefeld zu bestimmen, das generiert werden soll. Beispielsweise erstellt es ein Textfeld für `str`, eine Checkbox für `bool` und einen Datetime-Picker für `datetime`.

### Die View

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")
```

`PostView` dient als zentrales Objekt für diese Ressource. Das Attribut `fields` steuert, welche Spalten in der Liste und im Formular erscheinen, während `searchable_fields` die Suchleiste aktiviert. Alle Konfigurationen dazu, wie `Post` im Admin-Dashboard aussieht und sich verhält, befinden sich innerhalb dieser einen Klasse.

!!! note
    Das Beispiel importiert `ModelView` aus `starlette_admin.contrib.sqla`, da es auf SQLAlchemy basiert. Wenn Sie ein anderes Backend verwenden, etwa Beanie, MongoEngine oder Tortoise ORM, müssen Sie `ModelView` aus dem entsprechenden contrib-Paket importieren. Die Konfigurations-API bleibt über alle unterstützten Backends hinweg konsistent.

### Der Admin

```python
admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Die Klasse `Admin` verbindet die Datenbank-Engine mit dem User Interface.

* `add_view` registriert Ihre View in der Seitenleiste. Der optionale Parameter `icon` akzeptiert jede gültige [Font Awesome](https://fontawesome.com/icons)-Klasse.
* `mount_to` hängt die Admin-Anwendung unter dem Pfad `/admin` an Ihre FastAPI- oder Starlette-Anwendung an.

!!! warning
    Der Parameter `secret_key` signiert Cookies für Session-Daten, einschließlich Flash-Nachrichten und CSRF-Schutz. In Produktionsumgebungen müssen Sie den Beispielwert durch einen langen, zufälligen und sicher generierten String ersetzen. Verwenden Sie niemals einen Platzhalterwert in einem Live-Deployment.

## Ein zweites Modell hinzufügen

Sie können eine unbeschränkte Anzahl von Modellen registrieren. Um zum Beispiel ein `Tag`-Modell und seine entsprechende View hinzuzufügen, definieren Sie die Klassen und rufen `add_view` erneut auf:

```python
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class TagView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ("name",)


admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.add_view(TagView(Tag, icon="fa fa-tag"))
```

Aktualisieren Sie das Browserfenster, um sowohl **Posts** als auch **Tags** in der Seitenleiste zu sehen. Jede Ressource verfügt nun über ihre eigenen voll funktionsfähigen List-, Create-, Edit- und Delete-Seiten.

---

## Nächste Schritte

* **[Konzepte](concepts.md):** Lernen Sie die Terminologie der hier eingeführten Konzepte kennen, um sich besser in der Benutzeranleitung zurechtzufinden.
* **[Admin](../user-guide/admin.md):** Entdecken Sie alle `Admin(...)`-Optionen, einschließlich Branding, Theming, Authentifizierung, Sicherheit und Internationalisierung.
* **[Views](../user-guide/views.md):** Erkunden Sie alle verfügbaren `ModelView`-Konfigurationsoptionen zur Anpassung Ihrer Datenpräsentation.
