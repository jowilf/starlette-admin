---
title: Kernkonzepte
description: Verstehen Sie die architektonischen Designprinzipien von starlette-admin,
  einschließlich deklarativer Views, URL-basiertem Zustand und backend-agnostischen
  Modellen.
source_hash: 3928a168b4a3ffb7f57c78a8e7eed9fd92a949aa93c59339e49c29cb8ccb8a8c
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/getting-started/concepts/)
<!-- translation-notice:end -->

# Kernkonzepte

Nachdem Sie den Quickstart abgeschlossen haben, indem Sie eine `PostView` geschrieben und eine Admin-Instanz gemountet haben, lernen Sie die architektonischen Designprinzipien des Frameworks kennen. Diese Kernkonzepte bilden die Grundlage für die restliche Dokumentation.

## Eine Klasse pro Ressource

Jede Ressource, die das Admin-Panel verwaltet, wird über eine einzelne, dedizierte Klasse bereitgestellt. Wenn Sie `ModelView` subclassen und auf ein Datenbankmodell verweisen, generieren Sie automatisch paginierte, sortierbare und filterbare Views für alle Standard-CRUD-Operationen (Liste, Detail, Erstellen, Bearbeiten und Löschen).

Dies eliminiert die Notwendigkeit, benutzerdefinierte Routen oder HTML-Templates zu schreiben. Alles, was bestimmt, wie eine Ressource aussieht, validiert und sich verhält, befindet sich innerhalb dieser einzelnen View-Klasse.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

## Dieselbe View, jedes Backend

Views kommunizieren mit Ihren Daten über eine anpassbare Backend-Schicht. Ob Ihre Anwendung SQLAlchemy, SQLModel, Beanie, MongoEngine oder Tortoise ORM verwendet, die Konfigurations-API bleibt exakt dieselbe.

Felder, Filter, Berechtigungen und Lifecycle-Hooks funktionieren konsistent, unabhängig davon, wo sich Ihre Daten befinden. Das Wissen, das Sie zu einem Backend erwerben, lässt sich direkt auf die anderen übertragen. Der Austausch Ihrer zugrunde liegenden Datenquelle erfordert nur eine Aktualisierung Ihrer Import-Statements.

```python
# For SQLAlchemy backends
from starlette_admin.contrib.sqla import ModelView

# For Beanie backends: identical API surface, different import path
from starlette_admin.contrib.beanie import ModelView
```

## URL-basierter Listenzustand

Sortierung, Filterung, Paginierung und Suchkriterien synchronisieren sich direkt mit dem URL-Querystring. Da der Server Listenzustände vollständig aus diesen URL-Parametern rendert, ist jeder View-Zustand von Natur aus als Lesezeichen speicherbar und teilbar.

Wenn Sie einen bestimmten administrativen Link an einen Kollegen senden, sieht dieser exakt dieselben gefilterten Zeilen und dieselbe Sortierkonfiguration wie Sie.

```text
/admin/post/list?page=2&order_by=published_at%20desc&q=release

```

## Felder wissen, wie sie sich selbst rendern

Felder sind selbstrendernde Komponenten. Jeder Feldtyp verwaltet seine eigene Anzeigelogik in drei unterschiedlichen Kontexten: einer Zelle innerhalb einer Listentabelle, einer Zeile innerhalb einer Detailview und einem Eingabeelement innerhalb eines Formulars.

Wenn Sie eine View erstellen, deklarieren Sie Feldinstanzen oder übergeben Attributnamen, die das Backend automatisch Feldern zuordnet. Wählen Sie den Typ, der zu Ihrem Datenmodell passt, und das Framework übernimmt das Rendering:

* `StringField` für Textstrings
* `IntegerField` für numerische Daten
* `ImageField` für Dateiuploads

```python
from starlette_admin import StringField, IntegerField


class ProductView(ModelView):
    fields = [
        StringField("name"),
        IntegerField("price", help_text="In cents"),
    ]
```

## Deklarative Formularlayouts

Standardmäßig rendert das Attribut `fields` Ihre Create- und Edit-Formulare als flache, vertikale Liste. Um das User Interface umzustrukturieren, ohne Ihre zugrunde liegenden Datendefinitionen zu verändern, verwenden Sie das Attribut `form_layout`.

### Die Tuple-Kurzschreibweise

Für grundlegende Grid-Layouts gruppieren Sie Feldnamen in einem Tuple, um sie nebeneinander in einer einzigen Zeile zu rendern. Dies vermeidet die Notwendigkeit, komplexe Widget-Klassen zu importieren.

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

Wenn Ihre Formulare komplexer werden, können Sie sie mithilfe von Layout-Widgets strukturieren. Die Tuple-Kurzschreibweise funktioniert nativ innerhalb dieser Komponenten:

* **`PanelWidget` oder `FieldsetWidget`:** Verwenden Sie diese Komponenten, um verwandte Felder unter einer klaren Überschrift zu gruppieren oder um Abschnitte einklappbar zu machen.
* **`TabsWidget`:** Verwenden Sie diese Komponente, wenn eine Ressource unterschiedliche Datenkategorien hat (wie Versand- versus SEO-Metadaten), die nicht gleichzeitig sichtbar sein müssen.

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

Filterfunktionen werden direkt auf Datentypen abgebildet, sodass Benutzer nur relevante Query-Optionen sehen. Ein `StringField` bietet kontextbezogene Textoptionen wie *enthält*, *beginnt mit*, *ist gleich* und *ist null*. Ein Integer-Feld bietet numerische Einschränkungen wie *größer als* oder *zwischen*.

Sie können diese Defaults auf einem einzelnen Feld einschränken oder überschreiben, indem Sie den Parameter `filters` verwenden, oder Sie können benutzerdefinierte Filter für einzigartige Datentypen registrieren.

```python
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla.filters import GreaterThanFilter, BetweenFilter


class OrderView(ModelView):
    fields = [
        IntegerField("total", filters=[GreaterThanFilter, BetweenFilter]),
    ]
```

## Bringen Sie Ihre eigene Authentifizierung mit

Das Framework bleibt vollständig agnostisch gegenüber Ihrem Benutzerschema, indem es auf ein integriertes Benutzermodell verzichtet. Authentifizierung erfordert die Implementierung einer einzigen Methode: `authenticate(request)`.

Verbinden Sie diese Methode mit Ihrer bestehenden Authentifizierungsinfrastruktur, z. B. einer lokalen Datenbanktabelle, einem OAuth-Provider oder einem Upstream-Single-Sign-on-(SSO)-Proxy-Header. Die Rückgabe eines `AdminUser`-Objekts gewährt Zugriff auf das Interface. Die Rückgabe von `None` verweigert den Zugriff.

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

Massenaktionen operieren auf mehreren Zeilen, die aus der oberen Toolbar ausgewählt wurden, und Zeilenaktionen werden inline auf einzelnen Datensätzen ausgeführt. Wenn Sie eine View-Methode mit `@action` oder `@row_action` dekorieren, wird die Methode automatisch im User Interface verfügbar gemacht, ohne manuelle Routenregistrierung.

Statt einen Message-String aus der Aktionsmethode zurückzugeben, lösen Sie Benutzerbenachrichtigungen direkt mithilfe der integrierten `flash()`-Utility aus.

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

Jede Listenseite verfügt über einen Exportdialog, der es Benutzern ermöglicht, den Umfang (ausgewählte Zeilen oder die aktuelle Seite), Felder, Format und Dateinamen auszuwählen. Aktive Filter und Suchbegriffe bleiben erhalten, was bedeutet, dass die exportierte Datei exakt dem entspricht, was auf dem Bildschirm erscheint.

Das Framework unterstützt nativ die Formate CSV, JSON und PDF. Für zusätzliche Formate wie Excel (`xlsx`) integriert sich das Framework mit `tablib`, um jeden kompatiblen Dateityp zu unterstützen. Formate werden als einfache Extension-Strings deklariert. Die Zugriffskontrolle wird auf granularer Ebene mithilfe des Hooks `can_export` verwaltet.

Der Import-Assistent nimmt sicher Massendaten in denselben Formaten auf. Der Assistent validiert den Upload zunächst in einem Vorschau-Schritt, hebt Fehler zeilenweise hervor, bevor er irgendwelche Datenbank-Schreibvorgänge durchführt, und unterstützt optionale Primärschlüssel-Upserts. Sie können den Zugriff auf diese Funktion einschränken, indem Sie den Hook `can_import` verwenden.

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

## Flexibler Dateispeicher

Medienverwaltung über `FileField` und `ImageField` basiert auf einer zugrunde liegenden `Storage`-Abstraktionsschicht. Verwenden Sie `LocalStorage` für lokale Festplatten-Schreibvorgänge, oder installieren die optionale S3-Integration, indem Sie `pip install starlette-admin[s3]` ausführen.

Das Feld koordiniert automatisch Uploads, Backend-Validierung und Frontend-Rendering, nachdem Sie es auf Ihre gewählte Storage-Konfiguration verweisen.

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

## Benutzerdefinierte Views und Dashboard-Widgets

Seiten, die nicht explizit an ein Datenbankmodell gebunden sind, wie Metrik-Dashboards oder benutzerdefinierte Berichte, werden mithilfe von `CustomView` erstellt. Inhalte werden mithilfe eines Parameters `widget` befüllt. Dieser Parameter akzeptiert entweder eine statische `BaseWidget`-Instanz oder einen dynamischen Callable, der ausgeführt wird, wenn der Inhalt vom eingehenden Request abhängt.

Sie können komplexe User Interfaces zusammenstellen, indem Sie Layout-Primitives und Widgets zur Datenvisualisierung in einer sauberen Hierarchie anordnen.

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

## Events und Methoden-Hooks

Das Framework bietet zwei unterschiedliche Erweiterungspunkte, um Code während Create-, Update- und Delete-Zyklen auszuführen:

1. **Lifecycle-Methoden:** Für Logik, die auf eine bestimmte Entität beschränkt ist, überschreiben Sie lokale Methoden wie `before_create` direkt in Ihrer View-Klasse.
2. **Event-Listener:** Für globale Belange wie Audit-Logs, Cache-Invalidierung oder Webhooks abonnieren Sie das System `admin.events`.

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

* **[Views](../user-guide/views.md):** Jede Konfigurationsoption von `ModelView`.
* **[Fields](../user-guide/fields.md):** Der vollständige Katalog der Feldtypen.
* **[Formularlayouts](../advanced/form-layout.md):** Gestalten Sie Create- und Edit-Formulare mit Zeilen, Panels und Tabs.
* **[Actions](../user-guide/actions.md):** Massen- und Zeilenaktionen im Detail.
