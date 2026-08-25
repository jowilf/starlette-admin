---
title: Templates
description: Überschreiben Sie Jinja2-Templates in starlette-admin, um die HTML-Struktur
  bestimmter Views oder Felder vollständig anzupassen.
source_hash: 92643d00ab546c400a73e995d391d57cd0f5c054cba9d3ca8a5438df8eeb86ae
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/templates/)
<!-- translation-notice:end -->

# Templates

Jede Seite im Admin ist ein Jinja2-Template, das Sie überschreiben können. Ändern Sie eine einzelne Listenseite, die Tabellenzelle eines Feldes oder ein Dashboard-Widget, ohne den integrierten Template-Baum zu forken.

## Funktionsweise des Template-Loaders

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

`Admin` erzeugt einen Jinja2-`ChoiceLoader`, der zuerst Ihr `templates_dir` und danach das integrierte Paketverzeichnis `starlette_admin/templates/` durchsucht. Legen Sie eine Datei unter `my_templates/` mit demselben relativen Pfad ab, den sie innerhalb von `starlette_admin/templates/` hat, so überlagert Ihre Datei die integrierte Version. Alle übrigen Templates werden weiterhin aus dem integrierten Verzeichnis gerendert.

!!! note
    Die Loader-Kette registriert außerdem einen `PrefixLoader` unter dem Schlüssel `@starlette-admin`, der stets auf die integrierten Templates verweist – unabhängig davon, was sie in `templates_dir` überlagert. Erreichen Sie sie mit dem Pfadformat `@starlette-admin/<name>.html`; lassen Sie dabei den abschließenden Schrägstrich am Präfix weg. Wozu das dient, erfahren Sie weiter unten unter [Überschreiben eines einzelnen Seiten-Templates](#überschreiben-eines-einzelnen-seiten-templates).

## Verzeichnisübersicht der Templates

| Pfad | Gerendert für |
| --- | --- |
| `base.html` | Äußeres HTML-Layout (`<html>`, `<head>`, Skripte) |
| `layout.html` | Sidebar- und Topbar-Chrome (erweitert `base.html`) |
| `index.html` | Dashboard oder Startseite |
| `list.html` | Modell-Listenseite (Tabelle, Filterleiste, Paginierung) |
| `detail.html` | Detailansicht (schreibgeschützt) eines Datensatzes |
| `create.html` | Erstellungsformular |
| `edit.html` | Bearbeitungsformular |
| `login.html` | Login-Seite |
| `error.html` | HTTP-Fehlerseite (403, 404 usw.) |
| `actions.html` | Modal für Massenaktionen |
| `row-actions.html` | Aktions-Dropdown pro Zeile |
| `inline.html` | Inline-Formset auf der Erstellungs-/Bearbeitungsseite |
| `inline_detail.html` | Inline-Tabelle auf der Detailseite |
| `inline_row.html` | Einzelne Zeile innerhalb eines Inline-Formsets |
| `_filter_bar.html` | Leiste mit aktiven Filter-Chips oberhalb der Liste |
| `_filter_builder.html` | Modal des Filter-Builders |
| `_pagination.html` | Paginierungssteuerung |
| `_column_header.html` | Sortierbare Spaltenkopfzelle |
| `_form_footer.html` | Schaltflächen „Speichern“, „Speichern und fortfahren“ oder „Weiteren hinzufügen“ |
| `_form_group.html` | Fieldset einer einzelnen [Formularlayout](form-layout.md)-Gruppe auf dem Erstellungs-/Bearbeitungsformular |
| `_form_group_fields.html` | Die innerhalb einer Formularlayout-Gruppe gerenderten Feldeingaben |
| `fields/list/<type>.html` | Listenspaltenzelle für einen Feldtyp |
| `fields/detail/<type>.html` | Detailseitenanzeige für einen Feldtyp |
| `fields/form/<type>.html` | Formulareingabe-Widget für einen Feldtyp |
| `widgets/<name>.html` | Dashboard-Widget-Template |
| `modals/actions.html` | Bestätigungsmodal für Aktionen |
| `modals/delete.html` | Bestätigungsmodal zum Löschen |
| `modals/error.html` | Fehlermodal |
| `modals/import.html` | Import-Modal |
| `macros/views.html` | Gemeinsame Jinja2-Makros, die seitenübergreifend verwendet werden |

!!! note
    Der integrierte Baum enthält außerdem `modals/loading.html` – ein generisches Ladezustands-Modal – sowie mehrere feldspezifische Templates in `fields/list/`, `fields/detail/` und `fields/form/`. Prüfen Sie die exakten Dateinamen in `starlette_admin/templates/` für Ihre installierte Version, bevor Sie eine generische `<type>.html`-Datei überschreiben.

## Überschreiben eines einzelnen Seiten-Templates {#überschreiben-eines-einzelnen-seiten-templates}

```
my_templates/
└── list.html   ← überlagert das integrierte list.html

```

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block content %}
  <div class="alert alert-info">Eigener Banner oberhalb der Liste.</div>
  {{ super() }}
{% endblock %}

```

`{% extends "list.html" %}` würde zurück auf Ihr eigenes `my_templates/list.html` aufgelöst, weil `templates_dir` zuerst geprüft wird – und diese zirkuläre Referenz löst einen Fehler wegen unendlicher Rekursion aus. Das Präfix `@starlette-admin/` zeigt immer auf die integrierte Kopie; daher muss jedes `extends` und `include` innerhalb einer Überlagerung dieses Präfix verwenden statt des bloßen Dateinamens.

## Überschreibbare Blöcke

Jede integrierte Seite erweitert `layout.html`, das wiederum `base.html` erweitert. Überschreiben Sie einen einzelnen `{% block %}` statt einer ganzen Datei, um ein Fragment zu ändern, ohne den Rest der Seite zu duplizieren:

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block list_toolbar_extra %}
  {{ super() }}
  <a class="btn btn-outline-primary" href="/reports/export">Eigener Bericht</a>
{% endblock %}

```

### `base.html`

| Block | Inhalt |
| --- | --- |
| `favicon` | Das Favicon-`<link>`-Tag |
| `title` | Das `<title>`-Tag |
| `head_meta` | Die `<meta>`-Tags innerhalb des `<head>`-Elements |
| `head_css` | Stylesheet-`<link>`-Tags |
| `head` | Ein frei nutzbarer Einfügepunkt innerhalb des `<head>`-Elements |
| `body` | Der gesamte `<body>`-Inhalt (wird von `layout.html` überschrieben) |
| `modal` | Ein Einfügepunkt auf Seitenebene für Modals |
| `script` | Die `<script>`-Tags unmittelbar vor dem schließenden `</body>`-Tag |
| `tail` | Ein leerer Einfügepunkt am allerletzten Ende von `<body>`, nach `script` |

### `layout.html`

| Block | Inhalt |
| --- | --- |
| `sidebar` | Das gesamte Sidebar-`<aside>`-Element (einschließlich Nav-Brand, Menü und Footer) |
| `brand` | Das Logo-Bild (oder der `app_title`-Fallback) innerhalb des Nav-Brand-Links der Sidebar |
| `sidebar_menu` | Die Liste der View-Links innerhalb der Sidebar |
| `sidebar_footer` | Der untere Bereich der Sidebar |
| `user_menu_trigger` | Avatar und Benutzername auf der User-Menü-Schaltfläche. Einmal definiert und sowohl auf der mobilen Sidebar als auch auf der Desktop-Navigationsleiste via `self.user_menu_trigger()` wiederverwendet; eine Überlagerung aktualisiert daher beide |
| `user_menu_items` | Die Dropdown-Einträge im User-Menü |
| `navbar` | Die obere Navigationsleiste |
| `navbar_extra` | Zusätzlicher Inhalt, der in der Navbar neben dem User-Menü platziert wird |
| `header` | Der Kopfzeilenbereich der Seite, positioniert oberhalb von `content` (enthält Titel und Breadcrumbs) |
| `flash_messages` | Der vorgesehene Bereich zum Rendern von Flash-Meldungen |
| `content_before` | Ein Einfügepunkt unmittelbar vor `content` |
| `content` | Der Hauptinhalt der Seite (dies ist der Block, den `list.html`, `detail.html` usw. füllen) |
| `content_after` | Ein Einfügepunkt unmittelbar nach `content` |
| `page_footer` | Der Footer-Bereich unterhalb des Seiteninhalts |

### `list.html`

| Block | Inhalt |
| --- | --- |
| `header` | Die Seitenkopfzeile (enthält Titel und Breadcrumbs) |
| `page_title` | Die `<h1>`-Überschrift innerhalb der Kopfzeile |
| `breadcrumbs` | Die Breadcrumb-Navigation innerhalb der Kopfzeile |
| `modal` | Die Delete-, Action- und Import-Modals |
| `content` | Der vollständige Körper der Listenseite |
| `list_search` | Der Sucheingabebereich |
| `list_toolbar` | Die Toolbar-Zeile mit Filtern, Export-, Import- und Erstellen-Schaltflächen |
| `list_toolbar_extra` | Ein zusätzlicher Einfügepunkt ganz am Ende der Toolbar |
| `list_before_table` | Ein Einfügepunkt vor der Tabelle |
| `list_table` | Das `<table>`-Element selbst |
| `list_header` | Die `<thead>`-Zeile mit der Checkbox und den Spaltenkopfzellen |
| `list_row` | Eine einzelne `<tr>` in der Ergebnistabelle (ein scoped Block; hat Zugriff auf `row`, `row_pk` und `row_clickable`) |
| `list_row_actions_before` | Die Row-Actions-Zelle, wenn `row_actions_position` auf `BEFORE_COLUMNS` steht (ein scoped Block) |
| `list_row_actions_after` | Die Row-Actions-Zelle, wenn `row_actions_position` auf `AFTER_COLUMNS` steht (ein scoped Block) |
| `list_empty` | Der Platzhalter „Keine Daten“ (ein scoped Block, der für leere Zustände gerendert wird) |
| `list_after_table` | Ein Einfügepunkt nach der Tabelle |
| `list_footer` | Der Footer mit Paginierung und Bereichsanzeige |
| `head_css` | Seitenspezifische Stylesheet-Ergänzungen |
| `script` | Seitenspezifische Skript-Ergänzungen |

### `detail.html`

| Block | Inhalt |
| --- | --- |
| `header` | Die Seitenkopfzeile (enthält Titel, Breadcrumbs und Aktionen) |
| `page_title` | Die `<h1>`-Überschrift innerhalb der Kopfzeile |
| `breadcrumbs` | Die Breadcrumb-Navigation innerhalb der Kopfzeile |
| `modal` | Die Delete- und Action-Modals |
| `content` | Der vollständige Körper der Detailseite |
| `detail_before` | Ein Einfügepunkt vor der Detailkarte |
| `detail_title` | Der Titelanzeige-Bereich innerhalb der Detailkarte |
| `detail_actions` | Die Aktionsschaltflächen innerhalb der Detailkarte |
| `details_table` | Die primäre Tabelle mit Feldern und Werten |
| `detail_after` | Ein Einfügepunkt nach der Detailkarte |
| `head_css` | Seitenspezifische Stylesheet-Ergänzungen |
| `script` | Seitenspezifische Skript-Ergänzungen |

### `create.html` / `edit.html`

| Block | Inhalt |
| --- | --- |
| `header` | Die Seitenkopfzeile (enthält Titel und Breadcrumbs) |
| `page_title` | Die `<h1>`-Überschrift innerhalb der Kopfzeile |
| `breadcrumbs` | Die Breadcrumb-Navigation innerhalb der Kopfzeile |
| `content` | Der vollständige Körper der Formularseite |
| `form_before` | Ein Einfügepunkt vor der Formularkarte |
| `create_card_header` / `edit_card_header` | Der Kopfzeilenbereich innerhalb der Formularkarte |
| `create_form` / `edit_form` | Die [Formularlayout](form-layout.md)-Gruppen (jeweils gerendert via `_form_group.html`) samt ihren Feldeingabeelementen |
| `create_inlines` / `edit_inlines` | Der Inline-Formset-Bereich |
| `form_footer` | Die Schaltflächen „Speichern“, „Speichern und fortfahren“ und „Weiteren hinzufügen“ |
| `form_after` | Ein Einfügepunkt nach der Formularkarte |
| `head_css` | Seitenspezifische Stylesheet-Ergänzungen |
| `script` | Seitenspezifische Skript-Ergänzungen |

### `login.html`

| Block | Inhalt |
| --- | --- |
| `header` / `sidebar` | Bleibt leer (die Login-Seite blendet den Standard-Anwendungschrome aus) |
| `content` | Der vollständige Körper der Login-Seite |
| `login_logo` | Das Logo oberhalb des Login-Formulars |
| `login_title` | Der Titeltext der Login-Seite |
| `login_form_before` | Ein Einfügepunkt vor den Formularfeldern |
| `login_fields` | Die Eingabefelder für Benutzername und Passwort |
| `login_form_footer` | Ein Einfügepunkt nach den Feldern, aber noch innerhalb des Formulars |
| `login_card_footer` | Ein Einfügepunkt direkt unterhalb der Login-Karte |
| `script` | Seitenspezifische Skript-Ergänzungen |

### `index.html`

| Block | Inhalt |
| --- | --- |
| `head_css` | Widget-spezifische Stylesheet-Ergänzungen |
| `content` | Das Dashboard-Widget-Raster |
| `script` | Widget-spezifische Skript-Ergänzungen |

### `error.html`

| Block | Inhalt |
| --- | --- |
| `header` / `sidebar` | Bleibt leer (die Fehlerseite blendet den Standard-Anwendungschrome aus) |
| `content` | Die Fehlermeldung und die zugehörigen Aktionen |
| `error_actions` | Aktionsschaltflächen unterhalb der Fehlermeldung (etwa eine „Zurück“-Schaltfläche) |

!!! tip
    Rufen Sie `{{ super() }}` innerhalb einer Überlagerung auf, um den Inhalt des integrierten Blocks zu erhalten und zu ergänzen, statt ihn zu ersetzen. Das Beispiel `list_toolbar_extra` oben macht genau das, und die integrierten `index.html` und `create.html` verwenden dasselbe Muster für den Block `head_css`.

### Beispiel: Ersetzen des Sidebar-Logos durch ein Inline-SVG

Das Übergeben einer URL an `Admin(logo_url=...)` ist der schnellste Weg, ein Logo zu setzen, und deckt die meisten Fälle ab – auch externe `.svg`-Dateien. Da das integrierte Template diese URL jedoch innerhalb eines `<img>`-Tags rendert, kann das SVG keine CSS-Eigenschaften von der umgebenden Seite erben.

Überschreiben Sie den Block `brand` mit **Inline-`<svg>`-Markup**, wenn das Logo auf die restliche Benutzeroberfläche reagieren soll.

#### Implementierung

Erstellen Sie eine Datei `layout.html` in Ihrem Templates-Verzeichnis. Jede Seite im Admin erbt von `layout.html`, sodass diese eine Überlagerung sitewide greift.

```jinja
{# my_templates/layout.html #}
{% extends "@starlette-admin/layout.html" %}

{% block brand %}
  <svg class="navbar-logo" viewBox="0 0 32 32" fill="currentColor">
    <path d="M16 2 L30 9 L30 23 L16 30 L2 23 L2 9 Z" />
  </svg>
{% endblock %}

```

!!! tip "Klasse navbar-logo beibehalten"
    Belassen Sie die CSS-Klasse `navbar-logo` auf Ihrem eigenen `<svg>`-Element. Sie verleiht Ihrer Inline-Grafik Ausrichtung, Padding und Größenanpassung des Frameworks, ganz ohne eigenes CSS.

## Überschreiben von Feld-Templates

Jeder Feldkontext verwendet drei Unterverzeichnisse:

| Verzeichnis | Verwendet in |
| --- | --- |
| `fields/list/<type>.html` | Listentabellenzelle (kompakt, schreibgeschützt) |
| `fields/detail/<type>.html` | Detailseitenanzeige (vollständig, schreibgeschützt) |
| `fields/form/<type>.html` | Erstellungs- und Bearbeitungsformular-Eingabe |

Sie können die Listenzelle für Textfelder überschreiben, ohne das Formular oder die Detailanzeige anzupassen:

```
my_templates/
└── fields/
    └── list/
        └── text.html

```

Um eine einzelne **Feldinstanz** auf Ihr Template zu verweisen, statt den Typ überall zu überschreiben, setzen Sie `list_template`, `detail_template`, `form_template`, `null_template` oder `empty_template` direkt am Feld:

```python
from starlette_admin.fields import StringField

StringField("status", list_template="fields/list/status_badge.html")
```

`null_template` (Standard `"fields/detail/_null.html"`) und `empty_template` (Standard `"fields/detail/_empty.html"`) sind eigene Slots. Die Listen- und Detailseiten rendern sie anstelle von `list_template` bzw. `detail_template`, wann immer der Wert des Feldes `None` oder eine leere Liste bzw. ein leeres Tupel ist:

```python
StringField("status", null_template="fields/detail/_status_null.html")
```

## Überschreiben von Widget-Templates

Widgets folgen demselben Überlagerungsmuster. Legen Sie Ihre Dateien unter dem Verzeichnis `widgets/` ab:

```
my_templates/
└── widgets/
    └── stat_widget.html

```

## Globale Template-Variablen

Diese Variablen sind in jedem Template verfügbar, ohne dass sie übergeben werden müssen. `Admin` installiert sie einmalig während des Setups als Jinja2-Globals:

| Variable | Typ | Beschreibung |
| --- | --- | --- |
| `views` | `list[BaseView]` | Alle registrierten Views (werden zum Rendern der Sidebar verwendet) |
| `app_title` | `str` | Der Titel des Admin (`Admin(title=...)`) |
| `is_auth_enabled` | `bool` | `True`, wenn ein Auth-Provider konfiguriert ist |
| `__name__` | `str` | Das Routennamen-Präfix des Admin (z. B. `"admin"`) |
| `static_url` | `callable` | `static_url(request, path, v=None)` → URL für ein integriertes Static-Asset. Das Argument `v` hängt einen Cache-Busting-Query-Parameter `?v=` an. |
| `logo_url` | `callable` | `logo_url(request)` → URL für das Sidebar-Logo, oder `None`, falls nicht gesetzt |
| `login_logo_url` | `callable` | `login_logo_url(request)` → URL für das Logo der Login-Seite, oder `None`, falls nicht gesetzt |
| `favicon_url` | `callable` | `favicon_url(request)` → URL für das Favicon, oder `None`, falls nicht gesetzt |
| `list_url` | `callable` | `list_url(request, **overrides)` → URL, bei der `overrides` in den Query-String eingemischt werden (verwendet für Sortier-, Paginierungs- oder Suchlinks). Übergeben Sie `None`, um einen Schlüssel zu entfernen. |
| `detail_url` | `callable` | `detail_url(request, key, pk)` → URL der Detailseite eines Datensatzes |
| `edit_url` | `callable` | `edit_url(request, key, pk)` → URL der Bearbeitungsseite eines Datensatzes |
| `export_url` | `callable` | `export_url(request, key, fmt)` → Download-URL für den Export, die den Filter-/Sortier-/Suchzustand der aktuellen Listenseite trägt |
| `import_url` | `callable` | `import_url(request, key)` → POST-URL für den Import |
| `get_locale` | `callable` | `get_locale()` → Aktiver Locale-String (benötigt kein `request`-Argument) |
| `get_locale_display_name` | `callable` | `get_locale_display_name(locale)` → Lesbarer Name eines Locale-Strings |
| `i18n_config` | `I18nConfig` | Das i18n-Konfigurationsobjekt des Admin |
| `get_timezone` | `callable` | `get_timezone()` → Aktiver Timezone-String (benötigt kein `request`-Argument) |
| `get_timezone_display_name` | `callable` | `get_timezone_display_name(timezone, show_offset=False)` → Lesbarer Name eines Timezone-Strings |
| `timezone_config` | `TimezoneConfig | None` | Die Timezone-Konfiguration des Admin |
| `theme_settings` | `TablerSettings` | Aktive Tabler-Theme-Konfiguration (base, primary, radius, mode), bereitgestellt von `DefaultTheme` |
| `csrf_input` | `callable` | `csrf_input(request)` → Rendert das versteckte CSRF-`<input>` |

!!! note
    `get_locale`, `get_locale_display_name`, `get_timezone` und `get_timezone_display_name` nehmen keinen `request`-Parameter entgegen. Sie lesen Locale und Timezone aus `contextvars`, die `LocaleMiddleware` für die Dauer des Requests befüllt, und nicht aus dem `Request`-Objekt.

## Kontextvariablen pro Seite

Zusätzlich zu den Globals oben übergibt jede Seite ihr eigenes Kontext-Wörterbuch an `TemplateResponse`.

### `list.html`

| Variable | Typ | Beschreibung |
| --- | --- | --- |
| `view` | `BaseModelView` | Der aktuelle View |
| `title` | `str` | Seitentitel |
| `fields` | `list[BaseField]` | Derzeit sichtbare Spalten |
| `all_fields` | `list[BaseField]` | Alle Listenfelder (einschließlich ausgeblendeter) |
| `rows` | `list[dict]` | Serialisierte Zeilendaten |
| `total` | `int` | Gesamtzahl passender Datensätze für die Paginierung |
| `total_pages` | `int` | Gesamtzahl der Seiten |
| `range_start` | `int` | Nummer des ersten Datensatzes auf dieser Seite (1-basiert) |
| `range_end` | `int` | Nummer des letzten Datensatzes auf dieser Seite |
| `list_params` | `ListParams` | Geparster URL-Zustand (page, page_size, q, sorts, filters) |
| `filter_logic` | `str | None` | Ergibt `"and"` oder `"or"` für die aktive Filtergruppe auf oberster Ebene |
| `filter_chips` | `list` | Deskriptoren der aktiven Filter-Chips |
| `filter_builder_fields` | `list` | In der Filter-Builder-Oberfläche verfügbare Felder |
| `raw_filter` | `str | None` | Roher JSON-Filterstring aus der URL |
| `_actions` | `list` | Verfügbare Massenaktionen |
| `row_actions` | `dict[Any, list]` | Verfügbare Row-Actions pro Datensatz, verschlüsselt nach pk |

### `detail.html`

| Variable | Typ | Beschreibung |
| --- | --- | --- |
| `view` | `BaseModelView` | Der aktuelle View |
| `title` | `str` | Seitentitel |
| `obj` | `dict` | Serialisierter Datensatz |
| `raw_obj` | `Any` | Das rohe Modellobjekt vor der Serialisierung |
| `inlines` | `list[dict]` | Inline-Kontext (`[{"inline": InlineModelView, "rows": [...]}]`) |
| `_actions` | `list` | Verfügbare Row-Actions |

### `create.html` / `edit.html`

| Variable | Typ | Beschreibung |
| --- | --- | --- |
| `view` | `BaseModelView` | Der aktuelle View |
| `title` | `str` | Seitentitel |
| `obj` | `dict` | Aktuelle Feldwerte (Defaults beim Erstellen, bestehende Werte beim Bearbeiten) |
| `raw_obj` | `Any` | Rohes Modellobjekt (nur beim Bearbeiten, beim Erstellen nicht vorhanden) |
| `errors` | `dict[str, list[str]]` | Validierungsfehler, verschlüsselt nach Feldname (nur nach einem fehlgeschlagenen Absenden vorhanden) |
| `inlines` | `list[dict]` | Inline-Formset-Kontext |

## Eigene Globals und Filter hinzufügen

Um eigene Variablen und Funktionen zu den Templates hinzuzufügen, subclassen Sie `Admin` und überschreiben `__init__`. Rufen Sie zunächst `super().__init__()` auf, damit `self.templates` existiert, bevor Sie etwas ergänzen:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin


class MyAdmin(Admin):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.templates.env.globals["site_name"] = "My App"
        self.templates.env.filters["currency"] = lambda v: f"${v:,.2f}"


engine = create_engine("sqlite:///admin.sqlite")
admin = MyAdmin(engine, title="My Admin")
```

## Integrierte Jinja2-Filter

Jede Admin-Instanz registriert diese Filter während `_setup_templates`:

| Filter | Signatur | Beschreibung |
| --- | --- | --- |
| `is_custom_view` | `view | is_custom_view` | Gibt `True` zurück, wenn die Ressource ein `CustomView` ist |
| `is_link` | `view | is_link` | Gibt `True` zurück, wenn die Ressource ein `Link` ist |
| `is_model_view` | `view | is_model_view` | Gibt `True` zurück, wenn die Ressource ein `BaseModelView` ist |
| `is_dropdown` | `view | is_dropdown` | Gibt `True` zurück, wenn die Ressource ein `DropDown` ist |
| `tojson` | `value | tojson` | HTML-sichere JSON-Serialisierung (ersetzt Jinja2s Standard-`tojson`) |
| `file_icon` | `mime_type | file_icon` | Gibt eine vollständige Icon-Klasse für einen MIME-Typ zurück (z. B. `application/pdf` → `fa-solid fa-fw fa-file-pdf`); überschreiben Sie `self.templates.env.filters["file_icon"]`, um Ihr eigenes Icon-Set zu verwenden |
| `to_view` | `key | to_view` | Sucht einen registrierten `BaseModelView` anhand seines Key-Strings; wirft eine 404-`HTTPException`, falls nicht gefunden |
| `is_iter` | `value | is_iter` | Gibt `True` zurück, wenn der Wert eine `list` oder ein `tuple` ist |
| `is_str` | `value | is_str` | Gibt `True` zurück, wenn der Wert ein `str` ist |
| `is_dict` | `value | is_dict` | Gibt `True` zurück, wenn der Wert ein `dict` ist |
| `ra` | `value | ra` | Wandelt einen String in ein `RequestAction`-Enum-Member um |
| `safe_url` | `url | safe_url` | Gibt die URL nur zurück, wenn sie die Safe-URL-Prüfung besteht, andernfalls `""` |
| `sanitize_html` | `html | sanitize_html` | Entfernt nicht erlaubte Tags aus einem HTML-String und gibt ein `Markup` zurück |

---

## Nächste Schritte

* **[Formularlayouts](form-layout.md):** Teilen Sie die Erstellungs- und Bearbeitungsformulare in betitelte, optional einklappbare Gruppen auf, und überschreiben Sie `_form_group.html`, um deren Markup zu ändern.
* **[Eigene Themes](custom-themes.md):** Gestalten Sie den Admin um, ohne einzelne Templates anzufassen.
* **[Eigene Felder](custom-fields.md):** Kombinieren Sie die Python-Klasse eines Feldes mit dessen eigenem `list_template` oder `form_template`.
* **[Erweiterungspunkte](extension-points.md):** Die vollständige Liste der pluggable Oberflächen jenseits der Templates.
