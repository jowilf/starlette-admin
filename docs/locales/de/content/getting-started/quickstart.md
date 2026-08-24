---
title: Schnellstart
description: Erstellen Sie in wenigen Minuten eine voll funktionsfähige CRUD-Admin-Oberfläche
  für FastAPI und Starlette mit unserem umfassenden Schnellstart-Leitfaden.
source_hash: 19c9639af6caf311e19b134a5042588a3329ca1c3eeb005f000e63d8ac92c7bc
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
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

# Schnellstart

Erstellen Sie in wenigen Minuten eine voll funktionsfähige CRUD-Admin-Oberfläche für einen Blog – mit automatisch generierten Formularen, Listen, Suche, Import und Export, die direkt aus Ihren Datenmodellen erzeugt werden.

## Installation

Installieren Sie die erforderlichen Pakete mit Ihrem bevorzugten Paketmanager:

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

!!! note
    Das Paket `fastapi[standard]` enthält die FastAPI CLI, mit der Sie den Entwicklungsserver durch Ausführen von `fastapi dev` starten können.

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

## Anwendung ausführen

Starten Sie den Entwicklungsserver:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Öffnen Sie einen Browser und navigieren Sie zu [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

Wählen Sie in der Seitenleiste **Posts** und anschließend **Create**. Sie haben nun Zugriff auf paginierte Listen-, Detail-, Erstellungs-, Bearbeitungs- und Löschseiten. Das System generiert alle diese Oberflächen automatisch aus Ihrer Modelldefinition.

## Funktionsweise

Die folgenden Abschnitte erläutern die zentralen Komponenten der Anwendung.

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

Dieser Code verwendet Standard-SQLAlchemy 2.0. Das Paket starlette-admin liest die Spaltenmetadaten, die diesen Attributen zugeordnet sind, um das exakte HTML-Eingabefeld zu bestimmen, das generiert werden soll. Beispielsweise erstellt es ein Textfeld für `str`, ein Kontrollkästchen für `bool` und einen Datums-Zeit-Auswahl für `datetime`.

### Die View

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")
```

`PostView` dient als zentrales Objekt für diese Ressource. Das Attribut `fields` steuert, welche Spalten in der Liste und im Formular erscheinen, während `searchable_fields` die Suchleiste aktiviert. Sämtliche Konfigurationen dafür, wie `Post` im Admin-Dashboard aussieht und sich verhält, befinden sich in dieser einzigen Klasse.

!!! note
    Das Beispiel importiert `ModelView` aus `starlette_admin.contrib.sqla`, da es auf SQLAlchemy basiert. Wenn Sie ein anderes Backend verwenden, etwa Beanie, MongoEngine oder Tortoise ORM, müssen Sie `ModelView` aus dem entsprechenden contrib-Paket importieren. Die Konfigurations-API bleibt über alle unterstützten Backends hinweg konsistent.

### Der Admin

```python
admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Die Klasse `Admin` verbindet die Datenbank-Engine mit der Benutzeroberfläche.

* `add_view` registriert Ihre View in der Seitenleiste. Der optionale Parameter `icon` akzeptiert jede gültige [Font Awesome](https://fontawesome.com/icons)-Klasse.
* `mount_to` bindet die Admin-Anwendung unter dem Pfad `/admin` an Ihre FastAPI- oder Starlette-Anwendung an.

!!! warning
    Der Parameter `secret_key` signiert Cookies für Sitzungsdaten, einschließlich Flash-Nachrichten und CSRF-Schutz. In Produktionsumgebungen müssen Sie den Beispielwert durch eine lange, zufällige und sicher generierte Zeichenkette ersetzen. Verwenden Sie niemals einen Platzhalterwert in einer Live-Bereitstellung.

## Ein zweites Modell hinzufügen

Sie können eine unbegrenzte Anzahl von Modellen registrieren. Um beispielsweise ein `Tag`-Modell mit der entsprechenden View hinzuzufügen, definieren Sie die Klassen und rufen `add_view` erneut auf:

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

Laden Sie das Browserfenster neu, um sowohl **Posts** als auch **Tags** in der Seitenleiste zu sehen. Jede Ressource verfügt nun über eigene voll funktionsfähige Listen-, Erstellungs-, Bearbeitungs- und Löschseiten.

---

## Nächste Schritte

* **[Konzepte](concepts.md):** Lernen Sie die Terminologie der hier eingeführten Konzepte kennen, um sich im Benutzerhandbuch besser zurechtzufinden.
* **[Admin](../user-guide/admin.md):** Entdecken Sie alle Optionen von `Admin(...)`, einschließlich Branding, Theming, Authentifizierung, Sicherheit und Internationalisierung.
* **[Views](../user-guide/views.md):** Erkunden Sie sämtliche Konfigurationsoptionen von `ModelView`, die zur Anpassung Ihrer Datenpräsentation zur Verfügung stehen.
