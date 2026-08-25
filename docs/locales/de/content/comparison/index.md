---
title: Vergleich von starlette-admin, Django Admin und Flask-Admin
description: Ein direkter Vergleich von starlette-admin, Django Admin und Flask-Admin
  zu Web-Stacks, unterstützten ORMs, Funktionsumfang und Kompromissen.
source_hash: 7d6cd31a303552e61610bea128e3774a750ae1b417d7633fbffbf94df239a4cf
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/comparison/)
<!-- translation-notice:end -->

# Vergleich von starlette-admin, Django Admin und Flask-Admin

Django Admin, Flask-Admin und starlette-admin lösen dasselbe Problem: Sie generieren eine produktionsreife Admin-Oberfläche aus Ihren Datenmodellen, sodass Sie keine CRUD-Bildschirme von Hand schreiben müssen. Sie unterscheiden sich in den Web-Stacks, auf die sie abzielen, in den ORMs, die sie unterstützen, und darin, wie viel sie bereits mitbringen und was sie Ihnen überlassen.

Diese Seite vergleicht die drei Frameworks. Wenn Sie Django Admin oder Flask-Admin bereits kennen und eine direkte API-Übersetzung suchen, lesen Sie den passenden Migrationsleitfaden:

* [Migration von Django Admin](django-admin.md)
* [Migration von Flask-Admin](flask-admin.md)

## Positionierung auf einen Blick

| | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| **Web-Framework** | Nur Django | Nur Flask | Starlette, FastAPI und jede ASGI-Anwendung, die Sub-Applikationen einbinden kann |
| **Ausführungsmodell** | Synchron (WSGI-first) | Synchron (WSGI) | Async-first (ASGI) |
| **Datenschicht** | Nur Django ORM | SQLAlchemy, MongoEngine, peewee, pymongo | SQLAlchemy, SQLModel, MongoEngine, Beanie, Tortoise ORM oder ein [eigenes Backend](../integrations/custom-backend.md) |
| **UI-Toolkit** | Django-Templates, klassisches Admin-Theme | Bootstrap 2/3/4 | [Tabler](https://tabler.io) (Bootstrap 5), Dark Mode, [eigene Themes](../advanced/custom-themes.md) |
| **Im Framework enthalten** | Ja, Teil von Django | Nein, separates Paket | Nein, separates Paket |
| **Authentifizierung** | Integriert über `django.contrib.auth` | Bringen Sie Ihre eigene mit (`is_accessible`) | Austauschbares [`AuthProvider` / `OAuthProvider`](../user-guide/auth.md), bringen Sie Ihren eigenen User-Store mit |

## Wann welches Framework passt

### Django Admin

Django Admin passt zu nativen Django-Anwendungen. Es ist ausgereift und integriert sich in `django.contrib.auth`, sodass Sie Benutzer, Gruppen, Berechtigungen pro Modell und Änderungshistorie ohne Konfiguration erhalten. Es läuft ausschließlich innerhalb von Django.

### Flask-Admin

Flask-Admin hat die automatische Generierung nach Flask gebracht und den `ModelView`-Konfigurationsstil populär gemacht. Es ist synchron und an Flask gebunden und läuft daher nicht auf einem async-Stack.

### starlette-admin

starlette-admin zielt auf den asynchronen Python-Stack ab. Wenn Ihre Anwendung FastAPI oder Starlette verwendet, binden Sie das Admin-Interface in Ihre Anwendung ein, und es läuft auf demselben Event Loop. Es funktioniert mit SQL- und NoSQL-Datenschichten, übernimmt den `ModelView`-Konfigurationsstil von Flask-Admin und deckt den Funktionsumfang ab, den Django-Admin-Nutzer erwarten: Inlines, Batch-Aktionen, Berechtigungen pro Request und Internationalisierung.

## Feature-Matrix

**Legende:**

* **Ja:** Eingebaut
* **Teilweise:** Über Drittanbieter-Pakete oder eigenen Code möglich
* **Nein:** Nicht verfügbar

| Feature | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| Automatisch generierte CRUD-Views | **Ja** | **Ja** | **Ja** |
| Volltextsuche | **Ja** `search_fields` | **Ja** `column_searchable_list` | **Ja** [`searchable_fields`](../user-guide/filters.md) |
| Spaltenfilter | **Ja** `list_filter` | **Ja** `column_filters` | **Ja** [Visueller Filter-Builder](../user-guide/filters.md) mit `AND`/`OR`-Gruppen |
| Sortierung und Standardsortierung | **Ja** | **Ja** | **Ja** [`sortable_fields`, `fields_default_sort`](../user-guide/views.md#search-and-sort) |
| Inline-Bearbeitung in der Listenansicht | **Ja** `list_editable` | **Ja** `column_editable_list` | **Ja** [`inline_editable_fields`](../user-guide/inline-edit.md) |
| Inline-Formulare für verknüpfte Modelle | **Ja** `TabularInline` / `StackedInline` | **Ja** `inline_models` | **Ja** [`InlineModelView`](../user-guide/inline-forms.md) |
| Batch-Aktionen | **Ja** `actions` | **Ja** `@action` | **Ja** [`@action`](../user-guide/actions.md) mit Bestätigungsdialogen und eigenen Formularen |
| Aktionen pro Zeile | **Teilweise** eigene Templates | **Teilweise** eigene Formatter | **Ja** [`@row_action`, `@link_row_action`](../user-guide/actions.md#row-actions) |
| Datenexport | **Teilweise** `django-import-export` | **Ja** CSV und weitere | **Ja** [CSV, JSON, Excel, PDF](../user-guide/export-import.md) |
| Datenimport | **Teilweise** `django-import-export` | **Nein** | **Ja** [CSV, JSON, Excel](../user-guide/export-import.md) mit Vorschau-Validierung und Upsert |
| Datei- und Bild-Uploads | **Ja** `FileField` / `ImageField` | **Teilweise** zusätzlicher Aufwand nötig | **Ja** [Lokaler Speicher und S3](../user-guide/file-storage.md) |
| Dashboard-Widgets | **Teilweise** Themes von Drittanbietern | **Teilweise** eigene Index-View | **Ja** [Integriertes Widget-System](../user-guide/custom-views.md) |
| Eigene eigenständige Seiten | **Ja** eigene `AdminSite`-URLs | **Ja** `BaseView` + `@expose` | **Ja** [`CustomView`](../user-guide/custom-views.md) |
| Kontrolle über das Formularlayout | **Ja** `fieldsets` | **Ja** `form_rules` | **Ja** [`form_layout`](../advanced/form-layout.md) mit Tabs und Grids |
| Authentifizierung | **Ja** `django.contrib.auth` | **Nein** bringen Sie Ihre eigene mit | **Ja** [`AuthProvider`](../user-guide/auth.md) oder `OAuthProvider` |
| Berechtigungen pro Modell | **Ja** Permission-Framework | **Ja** Überschreiben der `can_*`-Flags | **Ja** [Methoden pro Request](../user-guide/views.md#security-and-authorization) |
| Berechtigungen pro Feld | **Teilweise** `get_readonly_fields` | **Nein** | **Ja** [`can_access_field`](../user-guide/views.md#security-and-authorization) |
| Lifecycle-Hooks | **Ja** `save_model`, Signals | **Ja** `on_model_change` | **Ja** [Lifecycle-Hooks](../user-guide/views.md#lifecycle-hooks) und [Events](../advanced/events.md) |
| CSRF-Schutz | **Ja** Django-Middleware | **Ja** über Flask-WTF | **Ja** [In `Admin` integriert](../user-guide/security.md) |
| Änderungshistorie / Audit-Log | **Ja** `LogEntry` | **Nein** | **Teilweise** bauen Sie selbst mit [Events](../advanced/events.md) |
| Internationalisierung | **Ja** | **Ja** über Flask-Babel | **Ja** [`I18nConfig`](../user-guide/i18n.md) |
| Mehrere Admin-Instanzen | **Ja** mehrere `AdminSite`s | **Ja** | **Ja** [Mehrere `Admin`-Mounts](../advanced/multiple-admin.md) |
| Unterstützung für async-ORMs | **Teilweise** | **Nein** | **Ja** async SQLAlchemy, Beanie, Tortoise ORM |

## Kompromisse

* **Komplettes Benutzersystem:** Django Admin liefert ein vollständiges Benutzersystem mit. `django.contrib.auth` übernimmt Benutzer, Gruppen, Berechtigungen und Passwortverwaltung für Sie. In starlette-admin implementieren Sie `authenticate()` gegen Ihren eigenen Datenspeicher – das bedeutet mehr Einrichtungsaufwand am Anfang, dafür mehr architektonische Freiheit später.
* **Automatisierte Änderungshistorie:** Django Admin zeichnet die Änderungshistorie in `LogEntry` auf. In starlette-admin bauen Sie den Audit-Trail selbst, indem Sie Lifecycle-[Events](../advanced/events.md) abonnieren. Das erfordert nur wenige Zeilen Code, ist aber nicht automatisch.
* **Ökosystem von Drittanbietern:** Django Admin verfügt über ein großes Ökosystem an Drittanbieter-Paketen für Themes, Widgets und Datenworkflows. starlette-admin deckt viele dieser Funktionen nativ ab, aber eine Nischen-Erweiterung, von der Sie abhängen, existiert möglicherweise noch nicht.
* **Dateiverwaltung:** Flask-Admin liefert `FileAdmin` mit, einen Browser für das Server-Dateisystem. starlette-admin verwaltet Dateien, die an Modelfelder gebunden sind, über [lokale Festplatte oder S3](../user-guide/file-storage.md) und bietet keinen universellen Datei-Browser für den Server.

## Nächste Schritte

* Migration von Django? Lesen Sie [Migration von Django Admin](django-admin.md).
* Migration von Flask-Admin? Lesen Sie [Migration von Flask-Admin](flask-admin.md).
* Neuanfang? Der [Quickstart](../getting-started/quickstart.md) liefert Ihnen in wenigen Minuten eine funktionierende Admin-Oberfläche.
