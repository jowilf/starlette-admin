---
title: Kernkonzepte
description: Verstehen Sie die architektonischen Designprinzipien von starlette-admin,
  einschließlich deklarativer Views, URL-basiertem Zustand und backend-agnostischen
  Modellen.
source_hash: 3928a168b4a3ffb7f57c78a8e7eed9fd92a949aa93c59339e49c29cb8ccb8a8c
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/getting-started/concepts/)
<!-- translation-notice:end -->

# Kernkonzepte

Nachdem Sie den Quickstart abgeschlossen haben, indem Sie eine `PostView` geschrieben und eine Admin-Instanz eingebunden haben, lernen Sie die architektonischen Designprinzipien des Frameworks kennen. Diese Kernkonzepte bilden die Grundlage für die gesamte übrige Dokumentation.

## Eine Klasse pro Ressource

Jede Ressource, die die Admin-Oberfläche verwaltet, wird über eine einzelne, dedizierte Klasse bereitgestellt. Wenn Sie `ModelView` ableiten und auf ein Datenbankmodell verweisen, werden automatisch paginierte, sortierbare und filterbare Views für alle Standard-CRUD-Operationen (Liste, Detail, Erstellen, Bearbeiten und Löschen) generiert.

Dadurch entfällt die Notwendigkeit, eigene Routen oder HTML-Templates zu schreiben. Alles, was das Aussehen, die Validierung und das Verhalten einer Ressource bestimmt, befindet sich innerhalb dieser einzelnen View-Klasse.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

## Dieselbe View, jedes Backend

Views kommunizieren mit Ihren Daten über eine anpassungsfähige Backend-Schicht. Ob Ihre Anwendung SQLAlchemy, SQLModel, Beanie, MongoEngine oder Tortoise ORM verwendet – die Konfigurations-API bleibt exakt identisch.

Felder, Filter, Berechtigungen und Lifecycle-Hooks funktionieren konsistent, unabhängig davon, wo Ihre Daten liegen. Das Wissen, das Sie für ein Backend erwerben, lässt sich direkt auf die anderen übertragen. Der Austausch Ihrer zugrunde liegenden Datenquelle erfordert lediglich eine Anpassung Ihrer Import-Anweisungen.

```python
# For SQLAlchemy backends
from starlette_admin.contrib.sqla import ModelView

# For Beanie backends: identical API surface, different import path
from starlette_admin.contrib.beanie import ModelView
```

## URL-basierter Listen-Zustand

Sortierung, Filterung, Paginierung und Suchkriterien synchronisieren sich direkt mit dem URL-Query-String. Da der Server die Listen-Zustände vollständig aus diesen URL-Parametern rendert, ist jeder View-Zustand von Natur aus als Lesezeichen speicherbar und teilbar.

Wenn Sie einen bestimmten Verwaltungslink an einen Kollegen senden, sieht dieser exakt dieselben gefilterten Zeilen und dieselbe Sortierkonfiguration wie Sie.

```text
/admin/post/list?page=2&order_by=published_at%20desc&q=release

```

## Felder wissen selbst, wie sie sich rendern

Felder sind selbstrendernde Komponenten. Jeder Feldtyp verwaltet seine eigene Anzeigelogik in drei unterschiedlichen Kontexten: als Zelle innerhalb einer Listentabelle, als Zeile innerhalb einer Detailansicht und als Eingabeelement innerhalb eines Formulars.

Beim Aufbau einer View deklarieren Sie Feldinstanzen oder übergeben Attributnamen, die das Backend automatisch Feldern zuordnet. Wählen Sie den Typ, der zu Ihrem Datenmodell passt, und das Framework übernimmt das Rendering:

* `StringField` für Textzeichenketten
* `IntegerField` für numerische Daten
* `ImageField` für Datei-Uploads

```python
from starlette_admin import StringField, IntegerField


class ProductView(ModelView):
    fields = [
        StringField("name"),
        IntegerField("price", help_text="In cents"),
    ]
```

## Deklarative Formularlayouts

Standardmäßig rendert das Attribut `fields` Ihre Erstellen- und Bearbeiten-Formulare als flache, vertikale Liste. Um die Benutzeroberfläche umzustrukturieren, ohne Ihre zugrunde liegenden Datendefinitionen zu verändern, verwenden Sie das Attribut `form_layout`.

### Die Tuple-Kurzschreibweise

Für einfache Grid-Layouts gruppieren Sie Feldnamen in einem Tuple, um sie nebeneinander in einer einzigen Zeile darzustellen. Dies erspart Ihnen den Import komplexer Widget-Klassen.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

### Fortgeschrittene Layout-Widgets

Wenn Ihre Formulare an Komplexität zunehmen, können Sie sie mithilfe von Layout-Widgets strukturieren. Die Tuple-Kurzschreibweise funktioniert auch innerhalb dieser Komponenten:

* **`PanelWidget` oder `FieldsetWidget`:** Verwenden Sie diese Komponenten, um verwandte Felder unter einer gemeinsamen Überschrift zu gruppieren.
* **`TabsWidget`:** Verwenden Sie diese Komponente, wenn eine Ressource unterschiedliche Datenkategorien besitzt (etwa Versanddaten gegenüber SEO-Metadaten), die nicht gleichzeitig sichtbar sein müssen.

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

## Filter sind an Feldtypen gebunden

Die Filterfunktionen sind direkt an Datentypen gekoppelt, sodass Benutzer nur relevante Abfrageoptionen sehen. Ein `StringField` bietet kontextbezogene Textoptionen wie *enthält*, *beginnt mit*, *ist gleich* und *ist null*. Ein Ganzzahlfeld bietet numerische Einschränkungen wie *größer als* oder *zwischen*.

Sie können diese Standardwerte auf Feldebene einschränken oder überschreiben, indem Sie den Parameter `filters` verwenden, oder Sie registrieren eigene Filter für besondere Datentypen.

```python
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla.filters import GreaterThanFilter, BetweenFilter


class OrderView(ModelView):
    fields = [
        IntegerField("total", filters=[GreaterThanFilter, BetweenFilter]),
    ]
```

## Bringen Sie Ihre eigene Authentifizierung mit

Das Framework bleibt hinsichtlich Ihres Benutzerschemas vollständig agnostisch, da es kein eingebautes Benutzermodell mitliefert. Die Authentifizierung erfordert die Implementierung einer einzigen Methode: `authenticate(request)`.

Verbinden Sie diese Methode mit Ihrer bestehenden Authentifizierungsinfrastruktur, etwa einer lokalen Datenbanktabelle, einem OAuth-Provider oder einem Upstream-Single-Sign-on-(SSO)-Proxy-Header. Die Rückgabe eines `AdminUser`-Objekts gewährt Zugriff auf die Oberfläche. Die Rückgabe von `None` verweigert den Zugriff.

```python
from starlette.requests import Request
from starlette_admin.auth import AdminUser, BaseAuthProvider


class MyAuthProvider(BaseAuthProvider):
    async def authenticate(self, request: Request) -> AdminUser | None:
        if request.session.get("user"):
            return AdminUser(username=request.session["user"])
        return None
```

## Aktionen laufen auf ausgewählten Zeilen

Sammelaktionen (Batch-Aktionen) operieren auf mehreren Zeilen, die über die obere Symbolleiste ausgewählt wurden, während Zeilenaktionen inline auf einzelnen Datensätzen ausgeführt werden. Wenn Sie eine View-Methode mit `@action` oder `@row_action` dekorieren, wird die Methode automatisch in der Benutzeroberfläche verfügbar gemacht – ganz ohne manuelle Routenregistrierung.

Statt eine Nachrichtenzeichenkette aus der Aktionsmethode zurückzugeben, lösen Sie Benutzerbenachrichtigungen direkt mithilfe der integrierten `flash()`-Utility-Funktion aus.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin import action, flash
from starlette_admin.contrib.sqla import ModelView


class ArticleView(ModelView):
    actions = ["make_published"]

    @action(
        name="make_published",
        text="Mark as published",
        confirmation="Publish selected articles?",
    )
    async def make_published_action(self, request: Request, pks: list[Any]) -> None:
        for article in await self.find_by_pks(request, pks):
            article.status = "published"
        flash(request, f"{len(pks)} article(s) published.", "success")
```

## Nativer Datenexport und -import

Jede Listenseite verfügt über einen Exportdialog, in dem Benutzer den Umfang (ausgewählte Zeilen oder die aktuelle Seite), die Felder, das Format und den Dateinamen auswählen können. Aktive Filter und Suchbegriffe bleiben erhalten, sodass die exportierte Datei exakt dem entspricht, was auf dem Bildschirm angezeigt wird.

Das Framework unterstützt nativ die Formate CSV, JSON und PDF. Für weitere Formate wie Excel (`xlsx`) bindet sich das Framework an `tablib`, um jeden kompatiblen Dateityp zu unterstützen. Formate werden als einfache Erweiterungszeichenketten deklariert. Die Zugriffssteuerung erfolgt auf granularer Ebene über den Hook `can_export`.

Der Import-Assistent nimmt Massendaten sicher in denselben Formaten entgegen. Der Assistent validiert den Upload zunächst in einem Vorschau-Schritt und markiert Fehler zeilenweise, bevor irgendwelche Datenbank-Schreibvorgänge durchgeführt werden; optional unterstützte Primärschlüssel-Upserts sind ebenfalls möglich. Den Zugriff auf diese Funktion können Sie über den Hook `can_import` einschränken.

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class OrderView(ModelView):
    exporters = ["csv", "xlsx"]

    def can_export(self, request: Request) -> bool:
        return request.state.user.is_staff

    def can_import(self, request: Request) -> bool:
        return request.state.user.is_admin
```

## Flexible Dateispeicherung

Die Medienverwaltung über `FileField` und `ImageField` basiert auf einer zugrunde liegenden `Storage`-Abstraktionsschicht. Verwenden Sie `LocalStorage` für Schreibvorgänge auf der lokalen Festplatte oder installieren Sie die optionale S3-Integration durch Ausführen von `pip install starlette-admin[s3]`.

Sobald Sie das Feld auf Ihre gewählte Speicherkonfiguration verweisen, koordiniert es automatisch Datei-Uploads, Backend-Validierung und Frontend-Rendering.

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/", name="local")


class AuthorView(ModelView):
    fields = [
        "name",
        ImageField("avatar", storage=local, upload_folder="avatars"),
    ]
```

## Eigene Views und Dashboard-Widgets

Seiten, die nicht explizit an ein Datenbankmodell gebunden sind – etwa Metrik-Dashboards oder individuelle Berichte –, erstellen Sie mit `CustomView`. Der Inhalt wird über einen Parameter `widget` befüllt. Dieser Parameter akzeptiert entweder eine statische `BaseWidget`-Instanz oder eine dynamische aufrufbare Funktion, wenn der Inhalt von der eingehenden Anfrage abhängt.

Komplexe Benutzeroberflächen setzen Sie zusammen, indem Sie Layout-Primitives und Widgets zur Datenvisualisierung in einer sauberen Hierarchie anordnen.

```python
from starlette.requests import Request
from starlette_admin import CustomView, CardRowWidget, Col, Breakpoints, StatWidget


async def count_users(request: Request) -> int:
    from sqlalchemy import func, select
    from myapp.models import User

    result = await request.state.session.execute(select(func.count(User.id)))
    return result.scalar()


dashboard = CustomView(
    menu_label="Dashboard",
    path="/",
    widget=CardRowWidget(
        children=[
            Col(
                StatWidget(title="Users", value_callback=count_users),
                breakpoints=Breakpoints(default=12, md=6),
            ),
        ]
    ),
)
```

## Ereignisse und Methoden-Hooks

Das Framework stellt zwei unterschiedliche Erweiterungspunkte bereit, um Code während der Erstell-, Aktualisierungs- und Löschzyklen auszuführen:

1. **Lifecycle-Methoden:** Für Logik, die auf eine bestimmte Entität beschränkt ist, überschreiben Sie lokale Methoden wie `before_create` direkt in Ihrer View-Klasse.
2. **Event-Listener:** Für übergreifende Belange wie Audit-Logs, Cache-Invalidierung oder Webhooks abonnieren Sie das System `admin.events`.

Beide Muster werden an identischen Ausführungspunkten ausgelöst, sodass Sie den Ansatz wählen können, der am besten zu Ihrer Anwendungsarchitektur passt.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.events import AdminEvent, AfterCreateContext


class PostView(ModelView):
    # Isolated to this view class only
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")


# Global system listener spanning every view class
async def log_create(ctx: AfterCreateContext) -> None:
    print(f"created {ctx.view_key} #{ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, log_create)
```

---

**Wie geht es weiter**

* **[Views](../user-guide/views.md):** Alle Konfigurationsoptionen von `ModelView`.
* **[Fields](../user-guide/fields.md):** Der vollständige Katalog der Feldtypen.
* **[Form Layouts](../advanced/form-layout.md):** Gestalten Sie Erstellen- und Bearbeiten-Formulare mit Zeilen, Panels und Tabs.
* **[Actions](../user-guide/actions.md):** Batch- und Zeilenaktionen im Detail.
