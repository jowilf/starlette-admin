---
title: Vergleich von starlette-admin, Django Admin und Flask-Admin
description: Ein direkter Vergleich von starlette-admin, Django Admin und Flask-Admin
  zu Webstacks, unterstützten ORMs, Funktionsumfang und Trade-offs.
source_hash: 7d6cd31a303552e61610bea128e3774a750ae1b417d7633fbffbf94df239a4cf
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/comparison/)
<!-- translation-notice:end -->

# Vergleich von starlette-admin, Django Admin und Flask-Admin

Django Admin, Flask-Admin und starlette-admin lösen dasselbe Problem: Sie generieren aus Ihren Datenmodellen ein produktionsreifes Admin-Interface, sodass Sie CRUD-Bildschirme nicht von Hand schreiben müssen. Sie unterscheiden sich darin, welche Webstacks sie ansprechen, welche ORMs sie unterstützen und wie viel sie bereits mitbringen beziehungsweise Ihnen überlassen.

Diese Seite vergleicht alle drei. Wenn Sie Django Admin oder Flask-Admin bereits kennen und eine direkte API-Übersetzung suchen, gehen Sie zur passenden Migrationsanleitung:

* [Migration von Django Admin](django-admin.md)
* [Migration von Flask-Admin](flask-admin.md)

## Positionierung auf einen Blick

| | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| **Webframework** | Nur Django | Nur Flask | Starlette, FastAPI und jede ASGI-App, die Sub-Applikationen mounten kann |
| **Ausführungsmodell** | Synchron (WSGI-first) | Synchron (WSGI) | Async-first (ASGI) |
| **Datenschicht** | Nur Django ORM | SQLAlchemy, MongoEngine, peewee, pymongo | SQLAlchemy, SQLModel, MongoEngine, Beanie, Tortoise ORM oder ein [benutzerdefiniertes Backend](../integrations/custom-backend.md) |
| **UI-Toolkit** | Django-Templates, klassisches Admin-Theme | Bootstrap 2/3/4 | [Tabler](https://tabler.io) (Bootstrap 5), Dark Mode, [benutzerdefinierte Themes](../advanced/custom-themes.md) |
| **Im Framework enthalten** | Ja, Teil von Django | Nein, separates Paket | Nein, separates Paket |
| **Authentifizierung** | Integriert über `django.contrib.auth` | Bringen Sie Ihre eigene mit (`is_accessible`) | Pluggable [`AuthProvider` / `OAuthProvider`](../user-guide/auth.md), bringen Sie Ihren eigenen Benutzerspeicher mit |

## Wann welches Framework passt

### Django Admin

Django Admin passt zu nativen Django-Anwendungen. Es ist ausgereift und integriert sich in `django.contrib.auth`, sodass Sie Benutzer, Gruppen, Berechtigungen pro Modell und den Änderungsverlauf ohne Konfiguration erhalten. Es läuft nur innerhalb von Django.

### Flask-Admin

Flask-Admin brachte die automatische Generierung nach Flask und machte den `ModelView`-Konfigurationsstil populär. Es ist synchron und an Flask gebunden, läuft also nicht auf einem Async-Stack.

### starlette-admin

starlette-admin zielt auf den asynchronen Python-Stack. Wenn Ihre Anwendung FastAPI oder Starlette verwendet, mounten Sie das Admin-Panel auf Ihrer App, und es läuft auf demselben Event Loop. Es funktioniert mit SQL- und NoSQL-Datenschichten, behält den `ModelView`-Konfigurationsstil von Flask-Admin bei und deckt den Funktionsumfang ab, den Django-Admin-Benutzer erwarten: Inlines, Massenaktionen, Berechtigungen pro Request und Internationalisierung.

## Feature-Matrix

**Legende:**

* **Ja:** Integriert
* **Teilweise:** Möglich über Pakete von Drittanbietern oder eigenen Code
* **Nein:** Nicht verfügbar

| Feature | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| Automatisch generierte CRUD-Views | **Ja** | **Ja** | **Ja** |
| Volltextsuche | **Ja** `search_fields` | **Ja** `column_searchable_list` | **Ja** [`searchable_fields`](../user-guide/filters.md) |
| Spaltenfilter | **Ja** `list_filter` | **Ja** `column_filters` | **Ja** [Visueller Filter-Builder](../user-guide/filters.md) mit `AND`/`OR`-Gruppen |
| Sortierung und Standardsortierung | **Ja** | **Ja** | **Ja** [`sortable_fields`, `fields_default_sort`](../user-guide/views.md#search-and-sort) |
| Inline-Bearbeitung auf der Listenseite | **Ja** `list_editable` | **Ja** `column_editable_list` | **Ja** [`inline_editable_fields`](../user-guide/inline-edit.md) |
| Inline-Formulare für verwandte Modelle | **Ja** `TabularInline` / `StackedInline` | **Ja** `inline_models` | **Ja** [`InlineModelView`](../user-guide/inline-forms.md) |
| Massenaktionen | **Ja** `actions` | **Ja** `@action` | **Ja** [`@action`](../user-guide/actions.md) mit Bestätigungsdialogen und benutzerdefinierten Formularen |
| Aktionen pro Zeile | **Teilweise** eigene Templates | **Teilweise** eigene Formatter | **Ja** [`@row_action`, `@link_row_action`](../user-guide/actions.md#row-actions) |
| Datenexport | **Teilweise** `django-import-export` | **Ja** CSV und weitere | **Ja** [CSV, JSON, Excel, PDF](../user-guide/export-import.md) |
| Datenimport | **Teilweise** `django-import-export` | **Nein** | **Ja** [CSV, JSON, Excel](../user-guide/export-import.md) mit Validierung der Vorschau und Upsert |
| Datei- und Bild-Uploads | **Ja** `FileField` / `ImageField` | **Teilweise** erfordert zusätzliche Einrichtung | **Ja** [Lokaler und S3-Dateispeicher](../user-guide/file-storage.md) |
| Dashboard-Widgets | **Teilweise** Themes von Drittanbietern | **Teilweise** eigene Index-View | **Ja** [Integriertes Widget-System](../user-guide/custom-views.md) |
| Eigenständige benutzerdefinierte Seiten | **Ja** eigene `AdminSite`-URLs | **Ja** `BaseView` + `@expose` | **Ja** [`CustomView`](../user-guide/custom-views.md) |
| Kontrolle über das Formularlayout | **Ja** `fieldsets` | **Ja** `form_rules` | **Ja** [`form_layout`](../advanced/form-layout.md) mit Tabs und Grids |
| Authentifizierung | **Ja** `django.contrib.auth` | **Nein** bringen Sie Ihre eigene mit | **Ja** [`AuthProvider`](../user-guide/auth.md) oder `OAuthProvider` |
| Berechtigungen pro Modell | **Ja** Permission-Framework | **Ja** Überschreiben der `can_*`-Flags | **Ja** [Methoden pro Request](../user-guide/views.md#security-and-authorization) |
| Berechtigungen pro Feld | **Teilweise** `get_readonly_fields` | **Nein** | **Ja** [`can_access_field`](../user-guide/views.md#security-and-authorization) |
| Lifecycle-Hooks | **Ja** `save_model`, Signals | **Ja** `on_model_change` | **Ja** [Lifecycle-Hooks](../user-guide/views.md#lifecycle-hooks) und [Events](../advanced/events.md) |
| CSRF-Schutz | **Ja** Django-Middleware | **Ja** über Flask-WTF | **Ja** [In `Admin` integriert](../user-guide/security.md) |
| Änderungsverlauf / Audit-Log | **Ja** `LogEntry` | **Nein** | **Teilweise** bauen Sie Ihre eigene mit [Events](../advanced/events.md) |
| Internationalisierung | **Ja** | **Ja** über Flask-Babel | **Ja** [`I18nConfig`](../user-guide/i18n.md) |
| Mehrere Admin-Instanzen | **Ja** mehrere `AdminSite`s | **Ja** | **Ja** [Mehrere `Admin`-Mounts](../advanced/multiple-admin.md) |
| Async-ORM-Unterstützung | **Teilweise** | **Nein** | **Ja** Async-SQLAlchemy, Beanie, Tortoise ORM |

## Trade-offs

* **Komplettes Benutzersystem:** Django Admin bringt ein vollständiges Benutzersystem mit. `django.contrib.auth` übernimmt Benutzer, Gruppen, Berechtigungen und Passwortverwaltung für Sie. In starlette-admin implementieren Sie `authenticate()` gegen Ihren eigenen Datenspeicher, was am Anfang mehr Einrichtung bedeutet und später mehr architektonische Freiheit bietet.
* **Automatisierter Änderungsverlauf:** Django Admin zeichnet den Änderungsverlauf in `LogEntry` auf. In starlette-admin bauen Sie den Audit-Trail selbst, indem Sie Lifecycle-[Events](../advanced/events.md) abonnieren. Das kostet einige Zeilen Code, ist aber nicht automatisch.
* **Ökosystem von Drittanbietern:** Django Admin hat ein großes Ökosystem an Drittanbieter-Paketen für Themes, Widgets und Datenworkflows. starlette-admin deckt viele dieser Funktionen nativ ab, aber eine Nischen-Erweiterung, von der Sie abhängen, existiert möglicherweise noch nicht.
* **Dateiverwaltung:** Flask-Admin bringt `FileAdmin` mit, einen Browser für das Serverdateisystem. starlette-admin verarbeitet Dateien, die an Modellfelder angehängt sind, über [lokale Festplatte oder S3](../user-guide/file-storage.md), und es gibt keinen universellen Server-Dateibrowser.

## Nächste Schritte

* Kommen Sie von Django? Lesen Sie [Migration von Django Admin](django-admin.md).
* Kommen Sie von Flask-Admin? Lesen Sie [Migration von Flask-Admin](flask-admin.md).
* Starten Sie neu? Der [Quickstart](../getting-started/quickstart.md) liefert Ihnen in wenigen Minuten ein funktionierendes Admin-Interface.
