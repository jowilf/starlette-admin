---
title: Admin-Konfiguration
description: Konfigurieren Sie Ihre starlette-admin-Instanz und passen Sie Theming,
  Routing und übergreifende Sicherheitseinstellungen an.
source_hash: 9e9a48b9e7e2e565b504c6d831eaf0e7a911489399ffb480ea19e50d0f8ad843
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/admin/)
<!-- translation-notice:end -->

# Admin

Sie übergeben jede instanzweite Einstellung als Schlüsselwortargument an die Klasse `Admin`: den Navbar-Titel, den Mount-Pfad, die CSRF- und Authentifizierungskonfiguration sowie das gerenderte Theme.

## Grundlegende Verwendung

Importieren Sie zunächst die Klasse `Admin` aus dem `contrib`-Paket, das zu Ihrem object-relational Mapper (ORM) passt:

```python
from starlette_admin.contrib.sqla import Admin  # SQLAlchemy
from starlette_admin.contrib.sqlmodel import Admin  # SQLModel
from starlette_admin.contrib.beanie import Admin  # Beanie
from starlette_admin.contrib.mongoengine import Admin  # MongoEngine
from starlette_admin.contrib.tortoise import Admin  # Tortoise ORM
```

Hier ist eine minimale Konfiguration mit SQLAlchemy:

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Post

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()

admin = Admin(
    session_provider=engine,
    title="My Admin",
    base_url="/admin",
    secret_key="a-long-random-string",
)
admin.add_view(ModelView(Post))
admin.mount_to(app)
```

* `title` legt den Text in der Navbar und das HTML-Tag `<title>` fest.
* `base_url` definiert das Pfadpräfix, unter dem der Admin gemountet wird.
* `secret_key` signiert die CSRF- und Flash-Cookies.
* `add_view` registriert ein View, und `mount_to` erzeugt die Routen und Middleware des Admins, bevor es diese in Ihre Anwendung einhängt.

Jede Klasse `Admin` akzeptiert alle unten beschriebenen Konfigurationsoptionen, und einige fügen backend-spezifisches Verhalten hinzu:

* `contrib.sqla.Admin(session_provider, ...)` nimmt als erstes positionales Argument eine Instanz von `Engine`, `AsyncEngine`, `sessionmaker` oder `async_sessionmaker` entgegen und fügt für Sie `DBSessionMiddleware` ein. `contrib.sqlmodel.Admin` ist dieselbe Klasse, die lediglich re-exportiert wird. Siehe [SQLAlchemy](../integrations/sqlalchemy.md) und [SQLModel](../integrations/sqlmodel.md).
* `contrib.beanie.Admin`, `contrib.mongoengine.Admin` und `contrib.tortoise.Admin` nehmen keine zusätzlichen Konstruktorargumente entgegen, da Beanie, MongoEngine und Tortoise ORM ihre Verbindungen außerhalb des Admins selbst verwalten. `mongoengine.Admin` registriert außerdem eine Route zum Ausliefern von GridFS-Dateien in `mount_to`. Siehe [Beanie](../integrations/beanie.md), [MongoEngine](../integrations/mongoengine.md) und [Tortoise ORM](../integrations/tortoise.md).

## Vollständige Referenz

Der Konstruktor `Admin` akzeptiert alle folgenden Parameter als Schlüsselwortargumente.

### Identität und Branding

| Parameter | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `title` | `str` | `"Admin"` | Text in der Navbar und `<title>`-Tag. |
| `logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Logo, das in der Navbar anstelle von `title` angezeigt wird. Übergeben Sie eine einfache URL oder eine Callable, die sie pro Anfrage auflöst, beispielsweise für Mandanten-spezifisches Branding. |
| `login_logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Logo, das auf der Anmeldeseite anstelle von `logo_url` angezeigt wird. Fällt auf `logo_url` zurück, wenn nicht gesetzt. |
| `favicon_url` | `str | Callable[[Request], str | None] | None` | `None` | href des Favicon-`<link>`-Tags. |

`logo_url`, `login_logo_url` und `favicon_url` akzeptieren jeweils entweder einen String oder eine `(request) -> str | None`-Callable. Verwenden Sie eine Callable, wenn das Branding von der Anfrage abhängt, etwa in einer Multi-Tenant-Anwendung oder wenn Sie mehrere Hostnamen bedienen:

```python
def logo_for_tenant(request):
    return f"https://cdn.example.com/{request.state.tenant}/logo.png"


admin = Admin(engine, title="My Admin", logo_url=logo_for_tenant)
```

### Mounting

| Parameter | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `base_url` | `str` | `"/admin"` | URL-Präfix, unter dem der Admin gemountet wird. |
| `route_name` | `str` | `"admin"` | Name des Starlette-Mounts. Jeder interne Link (`list`, `edit`, Exporte, statische Assets) wird durch den Aufruf von `request.url_for(route_name + ":list", ...)` generiert. |

Um mehr als einen `Admin` in derselben Anwendung zu betreiben, geben Sie jeder Instanz ein eigenständiges `base_url` und `route_name`. Andernfalls können Links, die von einem Admin generiert werden, zu einem anderen auflösen. Siehe [Multiple Admin Instances](../advanced/multiple-admin.md).


### Templates, statische Dateien und Theme

| Parameter | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `templates_dir` | `str` | `"templates"` | Verzeichnis, das vor dem Zurückfallen auf die integrierten Templates nach Template-Overrides durchsucht wird. |
| `static_dir` | `str | None` | `None` | Verzeichnis zusätzlicher statischer Dateien, die zusammen mit dem integrierten CSS und JS ausgeliefert werden. |
| `theme` | `BaseTheme` | `DefaultTheme()` | Eine Theme-Unterklasse, die die Layout-Templates, den Icon-Satz und die statischen Assets definiert. |

[Custom Themes](../advanced/custom-themes.md) und [Templates](../advanced/templates.md) behandeln diese Optionen im Detail.

### Die Startseite

| Parameter | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `index_view` | `CustomView | None` | `None` (ein `DefaultIndexView`, der aus Ihren registrierten Views erstellt wird) | Die Seite, die unter `base_url` gerendert wird. |

Die Standard-Startseite besteht aus einem Willkommens-Banner plus einem Panel pro registriertem Model View, das jeweils dessen Datensatzanzahl anzeigt. Um sie zu ersetzen, übergeben Sie Ihr eigenes `CustomView`, typischerweise eine Unterklasse von `DefaultIndexView` oder ein beliebiges `CustomView` mit einem `widget`. Siehe [Custom Views & Widgets](custom-views.md).

### Authentifizierung, Sicherheit und Datenschutz

| Parameter | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `auth_provider` | `BaseAuthProvider | None` | `None` (der Admin ist öffentlich zugänglich) | Schützt jede Route. Siehe [Authentication](auth.md). |
| `secret_key` | `str | None` | `None` (beim Start wird ein zufälliger Schlüssel generiert, mit einer `UserWarning`) | Signiert die CSRF- und Flash-Cookies. |
| `middlewares` | `Sequence[Middleware] | None` | `None` | Zusätzliche Starlette-Middleware, die zusätzlich zur CSRF-, Flash- und Auth-Middleware ausgeführt wird, die der Admin selbst hinzufügt. |
| `import_config` | `ImportConfig | None` | `None` (`ImportConfig()`-Standardwerte) | Größenlimits für Uploads und ZIP-Bomben-Limits für den Import-Endpoint. |
| `export_config` | `ExportConfig | None` | `None` (`ExportConfig()`-Standardwerte) | Obergrenze der Zeilenanzahl und Limits für URL-Datei-Downloads beim Export-Endpoint. |

Das Handbuch [Security](security.md) behandelt alle fünf Parameter ausführlich.

### Locale und Zeitzone

| Parameter | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `i18n_config` | `I18nConfig | None` | `None` (nur Englisch, keine `LocaleMiddleware`) | Aktiviert übersetzte UI-Strings. |
| `timezone_config` | `TimezoneConfig | None` | `TimezoneConfig()` (aktiviert) | Wandelt angezeigte Datum/Uhrzeit-Werte in die Zeitzone des Betrachters um. |

Eine vollständige Anleitung finden Sie unter [Internationalization & Timezones](i18n.md).

### Debugging {#debugging}

| Parameter | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `debug` | `bool` | `False` | Wenn `True`, ruft der Admin vor dem Start `starlette_admin.logging.configure_logging()` auf, was farbige Konsolen-Logging-Ausgaben auf DEBUG-Ebene für das Paket `starlette_admin` aktiviert. |

```python
admin = Admin(
    session_provider=engine, title="My Admin", secret_key="a-long-random-string", debug=True
)
```

Debug-Logging ist während der Entwicklung hilfreich. Bei jeder Anfrage wird protokolliert, welche Middleware ausgeführt wurde, welches View die URL aufgelöst hat und warum eine Berechtigungsprüfung bestanden oder fehlgeschlagen ist.

!!! warning
    Setzen Sie `debug=False` in der Produktionsumgebung. Logging auf DEBUG-Ebene ist sehr ausführlich und verursacht bei jeder Anfrage erheblichen Overhead.

Für einen leichtgewichtigeren Ansatz rufen Sie stattdessen selbst `starlette_admin.logging.configure_logging(level=logging.INFO)` auf, statt `debug=True` zu übergeben. So erhalten Sie den Handler ohne die volle DEBUG-Ausführlichkeit.

## Views registrieren und mounten

Nachdem Sie die Instanz `Admin` erstellt haben, registrieren Sie Ihre Views und mounten den Admin in Ihre Anwendung.

```python
admin.add_view(ModelView(Post))  # Register a view (BaseModelView, CustomView, and so on)
admin.mount_to(app)  # Mount the admin onto your Starlette or FastAPI app
```

### Views registrieren

Verwenden Sie `add_view`, um Komponenten zu Ihrem Admin-Dashboard hinzuzufügen. Die Methode akzeptiert entweder eine View-Instanz oder eine View-Klasse, und Sie können Model Views, benutzerdefinierte Seiten, Dropdown-Menüs und externe Links registrieren.

### Die Anwendung mounten

Nachdem Sie alle Ihre Views registriert haben, rufen Sie `mount_to(app)` genau einmal auf, um den Admin an Ihre Starlette- oder FastAPI-Anwendung anzuhängen. Dieser Schritt finalisiert die Routing- und Sicherheitskonfiguration.

!!! important "Order of operations matters"
    Das Mounting sperrt die Admin-Konfiguration, sodass jedes View korrekt geroutet wird.

    * Der Zugriff auf `admin.app` vor dem Mounting löst einen `RuntimeError` aus.
    * Das Registrieren eines weiteren Views oder ein erneuter Aufruf von `mount_to` nach dem ersten Mounting löst ebenfalls einen `RuntimeError` aus.

```python
admin.app  # Raises RuntimeError: not mounted yet

admin.mount_to(app)
admin.app  # Returns the mounted sub-application

admin.add_view(ModelView(Comment))  # Raises RuntimeError: already mounted
```

---

**Wie geht es weiter**

* **[Security](security.md):** Der `secret_key`, CSRF sowie die Export- und Import-Limits.
* **[Authentication](auth.md):** Die Einbindung des `auth_provider`.
* **[Multiple Admin Instances](../advanced/multiple-admin.md):** Den Betrieb mehrerer `Admin`-Instanzen in derselben Anwendung.
