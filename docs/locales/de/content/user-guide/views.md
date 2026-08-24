---
title: Ansichten
description: Erfahren Sie, wie Sie Listen- und Detailansichten in starlette-admin
  konfigurieren, einschließlich Suche, Sortierung und Paginierung.
source_hash: 33fc39d0f563908c141e8f5f8dc89dfdff925d4b959ed1d032ee685346daae57
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/views/)
<!-- translation-notice:end -->

# Ansichten

`starlette-admin` baut seine Sidebar aus drei Arten von View auf: `ModelView` stellt ein Datenbankmodell bereit, `CustomView` rendert eine eigenständige Seite, und `Link` fügt einen Hyperlink hinzu.

## ModelView

Eine `ModelView`-Unterklasse ist die Art, wie Sie ein Datenbankmodell im Admin bereitstellen. Klassenattribute und Methoden-Overrides dieser View definieren, wie die Ressource aussieht, sich verhält und mit Daten umgeht.

Jedes Beispiel in diesem Abschnitt verwendet das folgende SQLAlchemy-Setup:

```python
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    books: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(back_populates="books")
```

### Grundlegende Verwendung

Um das Modell `Post` bereitzustellen, leiten Sie von `ModelView` ab und konfigurieren dessen Attribute.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

Eine View-Klasse hat keine Wirkung, bis Sie sie bei einer `Admin`-Instanz registrieren:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///blog.db")
admin = Admin(engine, title="Blog Admin", secret_key="change-me")

# Register the view
admin.add_view(PostView(Post))
```

Unter [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) finden Sie einen lauffähigen Admin, der auf dieselbe Weise um ein `Post`-Modell herum aufgebaut wurde.

Durch die Registrierung einer View werden paginierte, sortierbare und durchsuchbare Oberflächen für das Auflisten, Anzeigen, Erstellen, Bearbeiten und Löschen von Datensätzen generiert. Sie müssen weder Routen noch Templates schreiben.

!!! note
    Sie importieren `ModelView` aus dem contrib-Paket Ihres Backends, etwa `starlette_admin.contrib.sqla`, `.beanie`, `.mongoengine`, `.sqlmodel` oder `.tortoise`. **Jedes unten beschriebene Attribut ist über alle Backends hinweg identisch**, sodass Sie später ein SQLAlchemy-Modell gegen ein MongoEngine-Dokument austauschen können, ohne Ihre View-Logik zu ändern.

### Zentrale Konfiguration

#### Benennung und Routing

Standardmäßig leitet der Admin URL-Routing und UI-Beschriftungen aus dem Klassennamen des Modells ab. Für das Modell `Post` verwendet er:

* **Key:** `post` (URL: `/admin/post/list`)
* **Menu label:** `Posts` (Sidebar-Eintrag)
* **Display name:** `Post` (UI-Schaltflächen wie **New Post**)

Wenn die abgeleiteten Werte nicht passen, überschreiben Sie sie bei der Registrierung oder im Konstruktor.

| Attribut | Beschreibung | Beispiel-Override | Resultierende UI oder URL |
| --- | --- | --- | --- |
| **`key`** | Der interne Slug und die Basis-URL-Route. | `key="blog-post"` | `/admin/blog-post/list` |
| **`menu_label`** | Der Pluralbegriff, der in der Sidebar verwendet wird. | `menu_label="Blog Posts"` | **Sidebar:** Blog Posts |
| **`display_name`** | Der Singularbegriff, der in Aktionen und Formularen verwendet wird. | `display_name="Article"` | **Buttons:** New Article |

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

#### Feldauswahl und Anpassung {#field-selection-and-customization}

Die Liste `fields` legt fest, welche Modellattribute in der Listenansicht, auf der Detailseite und in den Formularen erscheinen. Lassen Sie sie weg, um jedes Modellattribut bereitzustellen.

Mischen Sie Zeichenkettennamen mit expliziten `BaseField`-Instanzen, um Widgets, Validierung und Beschriftungen zu steuern:

```python
from starlette_admin.fields import (
    StringField,
    TextAreaField,
    BooleanField,
    DateTimeField,
)


class PostView(ModelView):
    fields = [
        "id",
        StringField("title", required=True, maxlength=200),
        TextAreaField("content", rows=10),
        BooleanField("published"),
        DateTimeField("created_at", exclude_from_create=True, exclude_from_edit=True),
    ]
```

!!! note
    Der Admin erkennt den Primärschlüssel automatisch für Sie. Definieren Sie `pk_attr` nur dann, wenn die Erkennung fehlschlägt, etwa bei einem Custom-Backend ohne Primärschlüssel aus einem einzelnen Feld.

#### Kontextabhängige Feldsichtbarkeit

Felder gehören oft auf die Liste oder Detailseite, aber nicht in ein Erstellungsformular – etwa Zeitstempel und systemverwaltete Status. Verwenden Sie die Attribute `exclude_fields_from_*`, um ein Feld auf bestimmten Oberflächen auszublenden:

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Hide from specific surfaces
    exclude_fields_from_create = ["published", "created_at"]
    exclude_fields_from_export = ["content"]
```

Die verfügbaren Ausschlussattribute enden auf `_create`, `_edit`, `_list`, `_detail`, `_export` und `_import`.

!!! important
    Um Benutzern zu erlauben, den Primärschlüssel beim Erstellen eines Datensatzes selbst festzulegen – standardmäßig deaktiviert –, setzen Sie `show_pk_in_forms = True`.

#### Formularlayout

Standardmäßig rendert `fields` Ihre Erstellungs- und Bearbeitungsformulare als flache, vertikale Liste. Um die Oberfläche umzugestalten, ohne Ihre Datendefinitionen anzufassen, verwenden Sie das Attribut `form_layout`.

**Die Tuple-Kurzschreibweise**

Für ein einfaches Raster müssen Sie keine Widget-Klassen importieren. Gruppieren Sie Feldnamen in einem Tuple, um sie nebeneinander in einer Zeile darzustellen.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

**Fortgeschrittene Layout-Widgets**

Wenn Ihre Formulare wachsen, strukturieren Sie sie mit Layout-Widgets. Die Tuple-Kurzschreibweise funktioniert auch darin:

* **`PanelWidget` oder `FieldsetWidget`:** Gruppieren Sie verwandte Felder unter einer Überschrift oder machen Sie einen Abschnitt einklappbar.
* **`TabsWidget`:** Trennen Sie klar unterscheidbare Datenkategorien – etwa Versanddetails und SEO-Metadaten –, die nicht gleichzeitig sichtbar sein müssen.

```python
from starlette_admin import TabsWidget


class ProductView(ModelView):
    fields = [
        "name",
        "price",
        "description",
        "sku",
        "weight",
        "shipping_class",
        "meta_title",
        "meta_description",
    ]

    form_layout = [
        TabsWidget(
            tabs=[
                ("Listing", [("name", "price"), "description"]),
                ("Shipping", [("sku", "weight"), "shipping_class"]),
                ("SEO", ["meta_title", "meta_description"]),
            ]
        ),
    ]
```

Informationen zu mehrspaltigen Zeilen mit expliziten Breiten, Tabs, statischen Inhalten und Zugriffssteuerungsverhalten finden Sie unter [Formularlayouts](../advanced/form-layout.md).

### Funktionen der Datentabelle

#### Suche und Sortierung {#search-and-sort}

Steuern Sie mit `searchable_fields` und `sortable_fields`, wie Benutzer Daten finden und ordnen.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ["title", "content"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]  # Sort newest first
```

* **`searchable_fields`**: Aktiviert den Filter-Builder und das globale Suchfeld. Die globale Suche führt eine Volltextabfrage über diese Felder aus.
* **`sortable_fields`**: Beschränkt, nach welchen Spaltenüberschriften Benutzer sortieren können. Eine über URL-Parameter übergebene Sortierabfrage für ein anderes Feld wird ignoriert.
* **`fields_default_sort`**: Legt den Anfangszustand der Tabelle fest. Übergeben Sie einen bloßen String für aufsteigende Sortierung, ein Tuple mit `True` für absteigende Sortierung oder ein Tuple mit `False` für eine explizit aufsteigende Sortierung. Verketten Sie mehrere Einträge für eine Sortierung über mehrere Spalten.

#### Paginierung und UI-Steuerelemente {#pagination-and-ui-controls}

Feinjustieren Sie das Layout der Listenseite mit diesen Attributen:

```python
class PostView(ModelView):
    page_size = 25
    page_size_options = [25, 50, 100, -1]  # -1 renders as "All"
    show_goto_page = True
    search_auto_submit = True
    show_detail_search = True
    row_click_navigate = False
```

* **`page_size` und `page_size_options`**: Das Standard-Paginierungslimit und die Auswahlmöglichkeiten im Dropdown.
* **`show_goto_page`**: Fügt ein „Zu Seite springen“-Eingabefeld für große Datenmengen hinzu.
* **`search_auto_submit`**: Filtert bereits während der Eingabe.
* **`show_detail_search`**: Fügt der Detailseite ein Suchfeld hinzu, um eingebettete Beziehungstabellen zu filtern.
* **`row_click_navigate`**: Öffnet die Detailseite, wenn der Benutzer irgendwo in einer Tabellenzeile klickt. Es ist standardmäßig aktiviert. Setzen Sie es auf `False`, um Zeilen inert zu halten, sodass Benutzer stattdessen über die Zeilenaktionen navigieren. Zeilen sind für Benutzer, deren `can_view_detail`-Prüfung fehlschlägt, niemals anklickbar.

#### Inline-Bearbeitung

Sie können Benutzern ermöglichen, bestimmte Felder direkt aus der Listenansicht zu ändern, ohne das vollständige Bearbeitungsformular zu öffnen.

Verwenden Sie das Attribut `inline_editable_fields`, um zu deklarieren, welche Spalten dies unterstützen. Ein Klick auf eine aktivierte Zelle öffnet dann ein Popover für eine schnelle Aktualisierung.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Enable quick edits for short text and boolean toggles
    inline_editable_fields = ["title", "published"]
```

!!! note "Sicherheit und Zugriff"
    Inline-Bearbeitung ist standardmäßig deaktiviert. Wenn Sie sie aktivieren, schränkt die bestehende `can_edit`-Berechtigung der View sie weiterhin ein.

Konfigurationsdetails, Validierungsverhalten und die vollständige Matrix der unterstützten Feldtypen finden Sie in der Anleitung [Inline-Bearbeitung](inline-edit.md).

### Relationale Daten

Der Admin übernimmt die Handhabung von Datenbeziehungen für Sie. Für die Many-to-One-Beziehung zwischen `Post` und `Author` fügen Sie das Beziehungsattribut zu Ihrer `fields`-Liste hinzu. Solange beide Modelle registrierte Views haben, rendert die UI die passenden Widgets.

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]  # 'books' is a Many relationship


class PostView(ModelView):
    fields = ["id", "title", "author"]  # 'author' is a One relationship


admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post))
```

#### Manuelle Deklaration von Beziehungen

Deklarieren Sie `HasOne`- oder `HasMany`-Felder selbst nur dann, wenn die Ziel-View unter einem benutzerdefinierten `key` registriert ist.

```python
from starlette_admin import HasMany, HasOne, StringField


class AuthorView(ModelView):
    fields = ["id", "name", HasMany("books", key="post-article")]


class PostView(ModelView):
    fields = ["id", "title", HasOne("author", key="author")]


# Author uses default key ("author"), Post uses custom key ("post-article")
admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post, key="post-article"))
```

### Objektdarstellung

Wenn der Admin einen Datensatz als einzelnen Wert anzeigen muss, greift er auf den Primärschlüssel zurück. Ein mit `Author #3` verknüpfter `Post` wird dann in Beziehungsspalten als „3“ dargestellt, was dem Benutzer kaum etwas verrät. Zwei optionale Methoden, definiert am **Modell** statt an der View, ersetzen diesen Standard durch etwas Aussagekräftiges. Beide akzeptieren den aktuellen `Request` und können synchron oder asynchron sein.

#### `__admin_repr__`

Gibt einen einfachen String zurück, der überall dort verwendet wird, wo der Datensatz als Text erscheint: in Beziehungsspalten auf der Listen- und Detailseite, in Breadcrumbs und in Bestätigungsmeldungen von Aktionen.

```python
class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __admin_repr__(self, request: Request) -> str:
        return self.name
```

Mit dieser Methode wird der Autor eines Posts als „Gabriel Garcia Marquez“ statt als „3“ dargestellt.

#### `__admin_select2_repr__`

Gibt ein HTML-Snippet zurück, das die Optionen in den `select2`-Dropdowns der Beziehungsformularfelder rendert, sodass Sie Auswahlmöglichkeiten mit Bildern, Badges oder ergänzendem Text anreichern können. Ohne diese Methode greift der Admin auf die maskierte Ausgabe von `__admin_repr__` zurück. Ohne beide Methoden greift er auf eine automatisch generierte Zusammenfassung der Nicht-Beziehungsfelder des Datensatzes zurück.

```python
from jinja2 import Template


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str] = mapped_column(String(255))

    def __admin_select2_repr__(self, request: Request) -> str:
        template = Template(
            '<div class="d-flex align-items-center">'
            '<span class="avatar me-2" style="background-image: url({{ obj.avatar_url }})"></span>'
            "<span>{{ obj.name }}</span>"
            "</div>",
            autoescape=True,
        )
        return template.render(obj=self)
```

!!! note
    Der zurückgegebene Wert muss gültiges HTML sein.

!!! warning
    Maskieren Sie Datenbankwerte, um Cross-Site-Scripting-Angriffe (XSS) zu verhindern. Rendern Sie das Snippet mit Jinja2 und `autoescape=True`, wie oben gezeigt, oder maskieren Sie jeden Wert selbst mit `html.escape`. Weitere Informationen finden Sie in der [OWASP-Dokumentation](https://owasp.org/www-community/attacks/xss/).

### Sicherheit und Autorisierung {#security-and-authorization}

Beschränken Sie den Zugriff, indem Sie die Berechtigungsmethoden Ihrer `ModelView` überschreiben. Jede gibt einen booleschen Wert zurück, und die Basisimplementierungen geben alle `True` zurück.

Dieses Muster lässt sich direkt in Ihren `AuthProvider` integrieren. Im folgenden Beispiel liest jede Prüfung eine `roles`-Liste aus dem `admin_user` der Session:

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        # If this returns False, the view is entirely hidden from the UI
        return any(":post" in role for role in request.state.admin_user.roles)

    def can_create(self, request: Request) -> bool:
        return "create:post" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit:post" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete:post" in request.state.admin_user.roles

    def can_view_detail(self, request: Request) -> bool:
        return "read:post" in request.state.admin_user.roles
```

Weitere Informationen zur Konfiguration Ihres `AuthProvider` und zum Befüllen des `admin_user`-Objekts finden Sie unter [Authentifizierung](auth.md).

!!! note
    Überschreiben Sie nur die Methoden, die Sie einschränken möchten. Die übrigen gewähren weiterhin Zugriff.

### Lifecycle-Hooks {#lifecycle-hooks}

Verwenden Sie Lifecycle-Hooks, um Seiteneffekte auszuführen oder Daten unmittelbar vor oder nach einer Datenbanktransaktion zu verändern.

```python
from typing import Any
from starlette.requests import Request


class PostView(ModelView):
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        # Mutate the object before it hits the database
        obj.title = obj.title.strip()

    async def after_create(self, request: Request, obj: Any) -> None:
        # Trigger post-creation side effects
        print(f"Created post #{obj.id}")
```

Die verfügbaren Hooks sind `before_create`, `after_create`, `after_create_committed`, `before_edit`, `after_edit`, `after_edit_committed`, `before_delete`, `after_delete` und `after_delete_committed`.

#### Committed-Hooks

`after_create_committed`, `after_edit_committed` und `after_delete_committed` werden erst ausgeführt, nachdem die Datenbanktransaktion committet wurde. Verwenden Sie sie für Seiteneffekte, die bei einem Rollback eines Schreibvorgangs nicht stattfinden dürfen – etwa den Versand von E-Mails oder das Einreihen von Hintergrundjobs:

```python
class PostView(ModelView):
    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await send_new_post_notification(obj.id)
```

!!! warning
    Zu dem Zeitpunkt, an dem diese Hooks ausgeführt werden, ist die Session der Anfrage bereits committed und geschlossen. Schreiben Sie innerhalb dieser Hooks nicht über `request.state.session` in die Datenbank. Nutzen Sie externe I/O oder öffnen Sie eine neue Datenbank-Session.

!!! important
    In `after_delete_committed` ist `obj` von jeder Session detached. Vor dem Löschen geladene Attribute bleiben lesbar, aber das Lesen eines nie geladenen Attributs schlägt fehl, da die Zeile nicht mehr existiert.

!!! note "Unterstützung durch Backends"
    Nur Backends, die den Commit bis zum Ende der Anfrage verzögern, emittieren diese Hooks. Derzeit ist das das SQLAlchemy-Backend.

!!! tip
    Für Logik, die sich über mehrere Views erstreckt – etwa ein Audit-Log –, verwenden Sie stattdessen [Events](../advanced/events.md).

### UI-Anpassung

#### Organisation der Sidebar {#sidebar-organization}

Gruppieren Sie verwandte Views mit `DropDown` in einem einklappbaren Ordner. Ein Ordner kann `ModelView`-, `CustomView`- und `Link`-Einträge mischen.

```python
from starlette_admin import DropDown, Link

admin.add_view(
    DropDown(
        "Content Management",
        icon="fa fa-folder",
        views=[
            PostView(Post, icon="fa fa-newspaper"),
            AuthorView(Author, icon="fa fa-user"),
            Link(
                menu_label="View Live Site",
                icon="fa fa-external-link",
                url="/",
                target="_blank",
            ),
        ],
    )
)
```

#### Exporter und Importer

Die Attribute `exporters` und `importers` legen fest, welche Formate für den Datentransfer verfügbar sind. Informationen zu den integrierten Optionen und zum Schreiben eigener Implementierungen finden Sie in der Anleitung [Export & Import](export-import.md).

```python
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["json"]
```

### Aktionen, Inline-Formulare und Templates

`ModelView` bietet drei weitere Funktionsgruppen für komplexe Fälle, jeweils mit eigener Anleitung:

* **Aktionen und Zeilenaktionen:** Die Attribute `actions` und `row_actions` fügen benutzerdefinierte Batch- und zeilenweise Operationen jenseits von CRUD hinzu. Siehe [Aktionen](actions.md).
* **Inline-Formulare:** Das Attribut `inlines` bettet die Erstellungs- und Bearbeitungsformulare eines verwandten Modells in die übergeordnete View ein. Siehe [Inline-Formulare](inline-forms.md).
* **Templates und Assets:** Ersetzen Sie die Standardseiten durch Ihre eigenen Jinja-Templates über `list_template`, `detail_template`, `create_template` oder `edit_template`. Siehe [Templates](../advanced/templates.md).

## CustomView

Nicht jede Admin-Seite lässt sich auf ein Datenbankmodell abbilden. `CustomView` erstellt eine eigenständige Sidebar-Seite auf Basis von Widgets, eigenen Templates oder eigenen Routen.

```python
from starlette_admin import CustomView, StatWidget

admin.add_view(
    CustomView(
        menu_label="System Status",
        icon="fa fa-heart-pulse",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)
```

Informationen zum vollständigen Widget-Katalog, zu Dashboard-Anleitungen und zu eigenen Routen finden Sie unter [Eigene Views](custom-views.md).

## Link

`Link` fügt der Sidebar einen Hyperlink hinzu, der Benutzer zu einer Live-Site, externen Dokumentation oder einem anderen internen Tool führt.

```python
from starlette_admin import Link

admin.add_link(
    Link(
        menu_label="View Live Site",
        icon="fa fa-external-link",
        url="/",
        target="_blank",
    )
)
```

* **`label`** und **`icon`**: Der Text und das Icon des Sidebar-Eintrags.
* **`url`** und **`target`**: Das Ziel und das Zielattribut des Ankers.

`admin.add_link(link)` ist ein schlanker Wrapper um `admin.add_view(link)`. Verwenden Sie, was in Ihrer Codebase besser lesbar ist. Sie können einen `Link` auch in ein `DropDown` verschachteln, wie unter [Organisation der Sidebar](#sidebar-organization) gezeigt.

---

## Nächste Schritte

* **[Felder](fields.md)**: Der vollständige Katalog der Feldtypen.
* **[Formularlayouts](../advanced/form-layout.md)**: Arrangieren Sie Erstellungs- und Bearbeitungsformulare mit Zeilen, Panels, Fieldsets und Tabs.
* **[Eigene Views](custom-views.md)**: Erstellen Sie Dashboards und eigenständige Seiten mit Widgets, Templates und eigenen Routen.
* **[Aktionen & Zeilenaktionen](actions.md)**: Fügen Sie Batch- und zeilenweise Operationen jenseits von CRUD hinzu.
* **[Inline-Bearbeitung](inline-edit.md)**: Ermöglichen Sie Benutzern, ein einzelnes Feld einer Zeile direkt auf der Listenseite zu bearbeiten.
* **[Inline-Formulare](inline-forms.md)**: Betten Sie die Erstellungs- und Bearbeitungsformulare eines verwandten Modells in eine übergeordnete View ein.
* **[Templates](../advanced/templates.md)**: Tauschen Sie die Jinja-Templates gegen eigene aus und binden Sie eigene Assets ein.
