---
title: Admin-Konfiguration
description: Konfigurieren Sie Ihre starlette-admin-Instanz und passen Sie Theming,
  Routing und übergreifende Sicherheitseinstellungen an.
source_hash: 9e9a48b9e7e2e565b504c6d831eaf0e7a911489399ffb480ea19e50d0f8ad843
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/admin/)
<!-- translation-notice:end -->

# Admin

Sie übergeben jede admin-weite Einstellung als Schlüsselwortargument an die `Admin`-Klasse: den Navbar-Titel, den Mount-Pfad, die CSRF- und Authentifizierungskonfiguration sowie das gerenderte Theme.

## Grundlegende Verwendung

Beginnen Sie mit dem Import der `Admin`-Klasse aus dem `contrib`-Paket, das zu Ihrem objektrelationalen Mapper (ORM) passt:

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

* `title` legt den Text in der Navbar und das HTML-`<title>`-Tag fest.
* `base_url` definiert das Pfadpräfix, unter dem das Admin-Panel eingebunden wird.
* `secret_key` signiert die CSRF- und Flash-Cookies.
* `add_view` registriert eine View, und `mount_to` baut die Routen und die Middleware des Admin-Panels auf, bevor sie in Ihre Anwendung eingehängt werden.

Jede `Admin`-Klasse akzeptiert alle unten beschriebenen Konfigurationsoptionen, und einige fügen backend-spezifisches Verhalten hinzu:

* `contrib.sqla.Admin(session_provider, ...)` nimmt als erstes positionales Argument einen `Engine`, `AsyncEngine`, `sessionmaker` oder `async_sessionmaker` entgegen und fügt für Sie die `DBSessionMiddleware` ein. `contrib.sqlmodel.Admin` ist dieselbe Klasse, re-exportiert. Siehe [SQLAlchemy](../integrations/sqlalchemy.md) und [SQLModel](../integrations/sqlmodel.md).
* `contrib.beanie.Admin`, `contrib.mongoengine.Admin` und `contrib.tortoise.Admin` nehmen keine zusätzlichen Konstruktorargumente entgegen, da Beanie, MongoEngine und Tortoise ORM ihre Verbindungen außerhalb des Admin-Panels selbst verwalten. `mongoengine.Admin` registriert außerdem in `mount_to` eine GridFS-Route zum Ausliefern von Dateien. Siehe [Beanie](../integrations/beanie.md), [MongoEngine](../integrations/mongoengine.md) und [Tortoise ORM](../integrations/tortoise.md).

## Vollständige Referenz

Der `Admin`-Konstruktor akzeptiert alle folgenden Parameter als Schlüsselwortargumente.

### Identität und Branding

| Parameter | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `title` | `str` | `"Admin"` | Text in der Navbar und `<title>`-Tag. |
| `logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Logo, das in der Navbar statt `title` angezeigt wird. Übergeben Sie eine einfache URL oder eine Callable, die sie pro Request auflöst, z. B. für Branding pro Mandant. |
| `login_logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Logo, das auf der Login-Seite statt `logo_url` angezeigt wird. Fällt auf `logo_url` zurück, wenn nicht gesetzt. |
| `favicon_url` | `str | Callable[[Request], str | None] | None` | `None` | href des Favicon-`<link>`-Tags. |

`logo_url`, `login_logo_url` und `favicon_url` akzeptieren jeweils entweder einen String oder eine Callable `(request) -> str | None`. Verwenden Sie eine Callable, wenn das Branding vom Request abhängt, etwa in einer Multi-Tenant-Anwendung oder wenn Sie mehrere Hostnames bereitstellen:

```python
def logo_for_tenant(request):
    return f"https://cdn.example.com/{request.state.tenant}/logo.png"


admin = Admin(engine, title="My Admin", logo_url=logo_for_tenant)
```

### Einbinden

| Parameter | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `base_url` | `str` | `"/admin"` | URL-Präfix, unter dem das Admin-Panel eingebunden wird. |
| `route_name` | `str` | `"admin"` | Name des Starlette-Mounts. Jeder interne Link (`list`, `edit`, Exporte, statische Assets) wird durch den Aufruf von `request.url_for(route_name + ":list", ...)` generiert. |

Um mehr als ein `Admin` in derselben Anwendung zu betreiben, geben Sie jeder Instanz ein eigenes `base_url` und `route_name`. Andernfalls können Links, die von einem Admin generiert werden, zu einem anderen auflösen. Siehe [Mehrere Admin-Instanzen](../advanced/multiple-admin.md).


### Templates, statische Dateien und Theme

| Parameter | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `templates_dir` | `str` | `"templates"` | Verzeichnis, das vor dem Zurückfallen auf die integrierten Templates nach Template-Overrides durchsucht wird. |
| `static_dir` | `str | None` | `None` | Verzeichnis zusätzlicher statischer Dateien, die neben dem integrierten CSS und JS ausgeliefert werden. |
| `theme` | `BaseTheme` | `DefaultTheme()` | Eine Theme-Unterklasse, die die Layout-Templates, den Icon-Satz und die statischen Assets definiert. |

[Benutzerdefinierte Themes](../advanced/custom-themes.md) und [Templates](../advanced/templates.md) behandeln diese Optionen im Detail.

### Die Startseite

| Parameter | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `index_view` | `CustomView | None` | `None` (eine `DefaultIndexView`, gebaut aus Ihren registrierten Views) | Die Seite, die unter `base_url` gerendert wird. |

Die Standard-Startseite ist ein Willkommensbanner plus ein Panel pro registriertem Modell-View, das jeweils die Anzahl seiner Datensätze zeigt. Um sie zu ersetzen, übergeben Sie Ihre eigene `CustomView`, typischerweise eine `DefaultIndexView`-Unterklasse oder eine beliebige `CustomView` mit einem Widget. Siehe [Benutzerdefinierte Views & Widgets](custom-views.md).

### Authentifizierung, Sicherheit und Datensicherheit

| Parameter | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `auth_provider` | `BaseAuthProvider | None` | `None` (das Admin-Panel ist öffentlich zugänglich) | Schützt jede Route. Siehe [Authentifizierung](auth.md). |
| `secret_key` | `str | None` | `None` (beim Start wird ein zufälliger Schlüssel generiert, mit einer `UserWarning`) | Signiert die CSRF- und Flash-Cookies. |
| `middlewares` | `Sequence[Middleware] | None` | `None` | Zusätzliche Starlette-Middleware, die zusätzlich zur CSRF-, Flash- und Auth-Middleware ausgeführt wird, die das Admin-Panel selbst hinzufügt. |
| `import_config` | `ImportConfig | None` | `None` (`ImportConfig()`-Defaults) | Limits für Upload-Größe und ZIP-Bomben beim Import-Endpoint. |
| `export_config` | `ExportConfig | None` | `None` (`ExportConfig()`-Defaults) | Obergrenze für die Zeilenanzahl und Limits für Downloads per URL beim Export-Endpoint. |

Der Leitfaden [Sicherheit](security.md) behandelt alle fünf Parameter ausführlich.

### Locale und Zeitzone

| Parameter | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `i18n_config` | `I18nConfig | None` | `None` (nur Englisch, keine `LocaleMiddleware`) | Aktiviert übersetzte UI-Strings. |
| `timezone_config` | `TimezoneConfig | None` | `TimezoneConfig()` (aktiv) | Konvertiert angezeigte Datums- und Zeitangaben in die Zeitzone des Betrachters. |

Eine vollständige Anleitung finden Sie unter [Internationalisierung & Zeitzonen](i18n.md).

### Debugging

| Parameter | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `debug` | `bool` | `False` | Wenn `True`, ruft starlette-admin vor dem Start `starlette_admin.logging.configure_logging()` auf, was farbige Konsolenprotokollierung auf DEBUG-Level für das Paket `starlette_admin` aktiviert. |

```python
admin = Admin(
    session_provider=engine, title="My Admin", secret_key="a-long-random-string", debug=True
)
```

Debug-Protokollierung hilft während der Entwicklung. Jeder Request protokolliert die Middleware, die ausgeführt wurde, die View, die die URL aufgelöst hat, und den Grund, warum eine Berechtigungsprüfung bestanden oder fehlgeschlagen ist.

!!! warning
    Behalten Sie `debug=False` in der Produktion bei. Protokollierung auf DEBUG-Level ist sehr ausführlich und fügt jedem Request erheblichen Overhead hinzu.

Für einen leichtgewichtigeren Ansatz rufen Sie stattdessen selbst `starlette_admin.logging.configure_logging(level=logging.INFO)` auf, statt `debug=True` zu übergeben. So erhalten Sie den Handler ohne die volle DEBUG-Ausführlichkeit.

## Views registrieren und einbinden

Nachdem Sie die `Admin`-Instanz erstellt haben, registrieren Sie Ihre Views und binden das Admin-Panel in Ihre Anwendung ein.

```python
admin.add_view(ModelView(Post))  # Register a view (BaseModelView, CustomView, and so on)
admin.mount_to(app)  # Mount the admin onto your Starlette or FastAPI app
```

### Views registrieren

Verwenden Sie `add_view`, um Komponenten zu Ihrem Dashboard hinzuzufügen. Die Methode akzeptiert entweder eine View-Instanz oder eine View-Klasse, und Sie können Modellviews, benutzerdefinierte Seiten, Dropdown-Menüs und externe Links registrieren.

### Die Anwendung einbinden

Nachdem Sie alle Ihre Views registriert haben, rufen Sie `mount_to(app)` genau einmal auf, um das Admin-Panel an Ihre Starlette- oder FastAPI-Anwendung anzuhängen. Dieser Schritt finalisiert die Routing- und Sicherheitskonfiguration.

!!! important "Die Reihenfolge der Schritte ist wichtig"
    Das Einbinden sperrt die Admin-Konfiguration, damit jede View korrekt geroutet wird.

    * Der Zugriff auf `admin.app` vor dem Einbinden löst einen `RuntimeError` aus.
    * Das Registrieren einer weiteren View oder ein erneuter Aufruf von `mount_to` nach dem ersten Einbinden löst ebenfalls einen `RuntimeError` aus.

```python
admin.app  # Raises RuntimeError: not mounted yet

admin.mount_to(app)
admin.app  # Returns the mounted sub-application

admin.add_view(ModelView(Comment))  # Raises RuntimeError: already mounted
```

---

**Nächste Schritte**

* **[Sicherheit](security.md):** Der `secret_key`, CSRF und die Limits für Export und Import.
* **[Authentifizierung](auth.md):** Die Verdrahtung des `auth_provider`.
* **[Mehrere Admin-Instanzen](../advanced/multiple-admin.md):** Mehr als ein `Admin` in derselben Anwendung betreiben.
