---
source_hash: e3296a30419e22b9def685804be98cc6f9b065e152edce097f750f28d339bfc2
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/blog/posts/add-admin-panel-to-fastapi-in-5-minutes/)
<!-- translation-notice:end -->

# Fügen Sie mit starlette-admin in 5 Minuten ein Admin-Panel zu FastAPI hinzu

_2026-07-13_

Sie haben die API ausgeliefert. Jetzt muss jemand in Ihrem Team die Daten dahinter bearbeiten: einen Tippfehler in einem Datensatz korrigieren, einen Beitrag zurückziehen oder prüfen, was ein Benutzer tatsächlich übermittelt hat. Die üblichen Optionen sind meist kostspielig:

| Option                   | Der Nachteil                                                                                               |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Eigenes CRUD-Frontend** | Beansprucht Wochen an Entwicklerzeit für Aufbau und Wartung.                                                       |
| **Direkter Datenbankzugriff**  | Schafft ein erhebliches Sicherheits- und Datenintegritätsrisiko.                                                   |
| **Django Admin / Flask Admin**         | Erzwingt eine Neuentwicklung mit anderem Framework oder setzt auf synchrones WSGI, was Ihre asynchrone ASGI-Anwendung blockiert. |
| **starlette-admin**      | **Lässt sich sofort in Ihre App einbinden – ganz ohne Frontend-Code.**                                                  |

`starlette-admin` funktioniert mit jeder auf Starlette basierenden Anwendung – und genau das ist FastAPI.

Diese Anleitung führt Sie in fünf Minuten von einer leeren Datei zu einer funktionierenden Back-Office-Anwendung. Sie bauen paginierte Listen, Suchfunktionalität, sortierbare Spalten, Erstellungs- und Bearbeitungsformulare, die durch Ihre vorhandenen Pydantic-Schemas validiert werden, Löschbestätigungen sowie CSV-Exporte – alles direkt aus einem SQLAlchemy-Modell generiert.

Der vollständige, lauffähige Code ist unter [`examples/11-sqla-pydantic-fastapi`](<%5Bhttps://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi%5D(https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi)>) verfügbar.

## Minute 1: Installation

Sie benötigen drei Pakete: das Admin-Framework, die ORM und FastAPI selbst.

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

Pydantic wird mit FastAPI mitgeliefert, was später wichtig wird: Das Admin-Panel kann dieselben Schemas wiederverwenden, die auch Ihre API zur Validierung nutzt.

## Minuten 2 und 3: Die vollständige App

Erstellen Sie `main.py`. Das ist die gesamte Anwendung:

```python title="main.py" hl_lines="36-38"
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///blog.db", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(120))
    slug: Mapped[str | None] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="dev-only-change-me")
admin.add_view(ModelView(Post, icon="fa fa-blog"))
admin.mount_to(app)

```

Beachten Sie, was fehlt: keine Templates, keine Route-Handler für die Admin-Seiten, keine Serialisierer und keine Feldkonfigurationen. `starlette-admin` liest die Spalten-Metadaten von SQLAlchemy und leitet die gesamte Oberfläche automatisch ab: Texteingaben mit Längenbegrenzung für die beiden `String`-Spalten, eine Textarea für den `Text`-Inhalt und eine Datums-Zeit-Auswahl für `published_at`.

Die drei hervorgehobenen Zeilen sind Ihre einzigen Integrationspunkte. `Admin` bindet die Database-Engine, `add_view` registriert das Modell in der Seitenleiste, und `mount_to` hängt alles unter dem Pfad `/admin` an Ihre bestehende FastAPI-App an. Ihre API-Routen bleiben unberührt; das Admin-Panel läuft einfach als eingebundene Sub-Anwendung.

## Minute 4: Ausführen

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Öffnen Sie [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) und klicken Sie in der Seitenleiste auf **Post**. Ab Werk erhalten Sie:

- Eine paginierte, sortierbare Listenansicht aller Beiträge.
- Erstellungs- und Bearbeitungsformulare mit dem passenden Eingabe-Widget je Spaltentyp.
- Eine Detailansicht für jeden Datensatz.
- Massenlöschung mit Bestätigungsdialog.
- CSV- und Excel-Exporte für die aktuelle Liste.

Ihre API bedient weiterhin normal den Datenverkehr. Prüfen Sie unter [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), dass alles intakt ist.

## Minute 5: Individuell statt Standard

Die Standardansicht bietet eine vollständige CRUD-Oberfläche, doch ein echtes Back Office verdient Feinschliff: Ihre Feldreihenfolge, Ihr Formularlayout und Ihr Suchverhalten. Hier entfaltet `starlette-admin` durch die Ableitung von `ModelView` sein volles Potenzial. Ersetzen Sie den `add_view`-Aufruf durch eine konfigurierte View:

```python title="main.py" hl_lines="8 9-13 17 22"
from starlette_admin import ComputedField, SlugField


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        ComputedField(
            "word_count",
            label="Word Count",
            getter=lambda request, post: len((post.content or "").split()),
        ),
        "content",
        "published_at",
    ]
    form_layout = [("title", "slug"), "content", "published_at"]
    exclude_fields_from_create = ("word_count",)
    exclude_fields_from_edit = ("word_count",)
    searchable_fields = ("title", "slug", "content", "published_at")
    fields_default_sort = (("published_at", True),)
    search_auto_submit = True


admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Blog Posts"))

```

Vier leistungsstarke Verbesserungen entstehen in dieser einzigen Klasse:

- **`SlugField(populate_from="title")`**: Erzeugt den Slug automatisch, während der Operator den Titel eingibt – ganz ohne eigenen JavaScript-Code.
- **`ComputedField`**: Stellt einen Wert dar, der nicht in der Datenbank existiert. Die Wortanzahl wird beim Rendern über einen einfachen Python-Callable berechnet.
- **`form_layout`**: Gliedert das Formular in logische Zeilen: Titel und Slug nebeneinander, Inhalt in voller Breite, darunter das Veröffentlichungsdatum.
- **`search_auto_submit`**: Filtert die Liste dynamisch, während der Operator über alle in `searchable_fields` definierten Spalten hinweg tippt.

## Schlechte Daten ablehnen: Nutzen Sie das Schema, das Sie bereits haben

Operatoren machen Fehler – das Admin-Panel muss daher Ihre Regeln serverseitig durchsetzen. Der Vorteil: Diese Regeln haben Sie bereits geschrieben. Jedes FastAPI-Projekt validiert seine Request-Bodies mit Pydantic-Modellen, sodass sich irgendwo in Ihrem Codebase ein Schema wie das folgende findet:

```python title="main.py"
from pydantic import BaseModel, Field, field_validator


class PostIn(BaseModel):
    id: int | None = None
    title: str = Field(min_length=3, max_length=120)
    slug: str = Field(
        min_length=3, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    content: str = Field(min_length=10)
    published_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        if len(v.split()) < 3:
            raise ValueError("Must contain at least 3 words")
        return v

```

Statt die Validierungslogik doppelt zu schreiben, übergeben Sie dem Admin-Panel Ihr vorhandenes Modell. Die Erweiterung `ext.pydantic` stellt eine `ModelView` bereit, die jede Formularübermittlung durch ein Pydantic-Modell schickt, bevor sie die Datenbank erreicht. Richten Sie Ihren `ModelView`-Import auf die Erweiterung, belassen Sie `Admin`, wie es ist, und übergeben Sie das Schema:

```python title="main.py" hl_lines="1 9"
from starlette_admin.contrib.sqla.ext.pydantic import ModelView


class PostView(ModelView):
    ...  # configuration from Minute 5, unchanged


admin.add_view(
    PostView(Post, pydantic_model=PostIn, icon="fa fa-blog", menu_label="Blog Posts")
)

```

Der Körper von `PostView` bleibt exakt derselbe; nur seine Basisklasse ändert sich durch den neuen Import.

Die Integration verläuft nahtlos. Jede Einschränkung greift beim Erstellen und Bearbeiten: die Längengrenzen, der Slug-Regex und der benutzerdefinierte `field_validator`. Jeder Pydantic-Fehler wird direkt dem entsprechenden Formularfeld zugeordnet und inline dargestellt – ganz wie bei einem handgebauten Formular. Achten Sie darauf, `id` im Schema optional zu halten, damit Erstellungsformulare, die zunächst keine ID besitzen, dennoch valide sind.

Damit etablieren Sie eine einzige Quelle der Wahrheit. Wenn Ihr API-Schema eine neue Regel erhält, setzt das Admin-Panel diese beim nächsten Request durch – ohne jegliche Änderungen am Admin-seitigen Code.

## Noch eine Minute übrig? Geben Sie den Beiträgen einen Autor

Echte Daten beruhen auf Beziehungen, und das Admin-Panel behandelt sie nach demselben Zero-Configuration-Ansatz. Fügen Sie ein `User`-Modell hinzu und verknüpfen Sie es mit `Post`:

```python title="main.py"
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))

    posts: Mapped[list["Post"]] = relationship(back_populates="user")

```

```python title="main.py" hl_lines="4 5"
class Post(Base):
    # ... columns from before ...

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")

```

Registrieren Sie das Benutzermodell nach demselben schema-getriebenen Muster. `EmailStr` und `HttpUrl` liefern die Formatvalidierung automatisch, und `email-validator` ist bereits in `fastapi[standard]` enthalten:

```python title="main.py" hl_lines="11"
from pydantic import EmailStr, HttpUrl


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl


admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))

```

Da diesmal nichts zu konfigurieren ist, kommt die Erweiterung `ModelView` direkt ohne Subklasse zum Einsatz.

Machen Sie abschließend den Autor verpflichtend, indem Sie zwei Zeilen zu `PostIn` hinzufügen:

```python title="main.py" hl_lines="2 3 6"
class PostIn(BaseModel):
    # validation runs after relations are resolved, so user is an ORM instance
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ... fields from before ...
    user: User

```

`user: User` hat keinen Standardwert, d. h. ein Beitrag ohne Autor wird abgelehnt wie jeder andere Validierungsfehler auch. Der Typ ist die SQLAlchemy-Klasse `User` selbst, weil das Admin-Panel die ausgewählte ID vor der Validierung zu einer ORM-Instanz auflöst. Genau deshalb ist `arbitrary_types_allowed` erforderlich (`ConfigDict` wird aus `pydantic` importiert).

Fügen Sie als Nächstes `"user"` zu `PostView.fields` und `form_layout` hinzu, damit der Autor im Beitragsformular erscheint. Dieses Feld ist kein gewöhnliches Dropdown. Es handelt sich um ein Select-Eingabefeld mit serverseitiger Autovervollständigung, das Ihre Benutzer während der Eingabe durchsucht, und die Benutzer-Detailseite verlinkt zurück zu jedem zugehörigen Beitrag.

!!! note
`create_all` ändert bestehende Tabellen nicht, daher müssen Sie `blog.db` löschen, bevor Sie neu starten, um die neue Spalte `user_id` zu übernehmen.

## Vor dem Deployment

!!! warning
Der Parameter `secret_key` signiert das Session-Cookie, das für den CSRF-Schutz und Flash-Messages verwendet wird. Ersetzen Sie den Platzhalter vor dem Deployment durch einen langen, zufälligen Wert aus Ihrer Konfiguration, und laden Sie ihn unbedingt aus Ihren Umgebungsvariablen, statt ihn fest in den Quellcode zu schreiben.

!!! note
`Base.metadata.create_all(engine)` im lifespan ist eine Annehmlichkeit für den Schnellstart. In einem Produktionsprojekt werden Ihre Tabellen durch Migrationen verwaltet (z. B. mit Alembic). Entfernen Sie diesen Aufruf und richten Sie `Admin` direkt auf Ihre vorhandene Engine. `starlette-admin` modifiziert niemals Ihr Schema; es liest und schreibt ausschließlich Zeilen.

## Das skaliert weit über die Demo hinaus

Alles oben Genannte nutzt zwei Modelle, doch genau diese `ModelView`-Mechaniken tragen auch ein umfangreiches Back Office. Datei- und Bild-Uploads lassen sich ebenso leicht implementieren wie [Authentifizierung mit rollenbasierter Zugriffskontrolle](../../user-guide/auth.md), [benutzerdefinierte Filter](../../user-guide/filters.md), [Zeilen- und Massenaktionen](../../user-guide/actions.md) und umfassendes [i18n](../../user-guide/i18n.md). Wo das eingebaute Verhalten nicht ausreicht, bietet jeder Query- und Lifecycle-Schritt einen Override-Hook. Genau mit dieser Flexibilität werden Muster wie [Soft Deletes mit einer Trash-View](soft-deletes-trash-view.md) umgesetzt.

---

## Wie es weitergeht

- **[Konzepte](../../getting-started/concepts.md):** Das Vokabular hinter dem, was Sie gerade gebaut haben – damit sich die restliche Dokumentation flüssig liest.
- **[Views](../../user-guide/views.md):** Ein tiefgehender Blick auf jede `ModelView`-Option einschließlich Permission-Hooks.
- **[Soft Deletes und eine Trash-View für FastAPI](soft-deletes-trash-view.md):** Das erste fortgeschrittene Rezept, direkt auf den hier eingeführten Override-Hooks aufbauend.
