---
title: Templates
description: Jinja2-Templates in starlette-admin überschreiben, um die HTML-Struktur
  bestimmter Views oder Felder vollständig anzupassen.
source_hash: 92643d00ab546c400a73e995d391d57cd0f5c054cba9d3ca8a5438df8eeb86ae
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/templates/)
<!-- translation-notice:end -->

# Templates

Jede Seite im Admin-Panel ist ein Jinja2-Template, das Sie überschreiben können. Ändern Sie eine einzelne Listenseite, die Tabellenzelle eines Feldes oder ein Dashboard-Widget, ohne den integrierten Template-Baum zu forken.

## Wie der Template-Loader funktioniert

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

`Admin` baut einen Jinja2-`ChoiceLoader`, der zuerst Ihr `templates_dir` prüft und danach das integrierte Paketverzeichnis `starlette_admin/templates/`. Legen Sie eine Datei unter `my_templates/` unter demselben relativen Pfad ab, den sie innerhalb von `starlette_admin/templates/` hat, dann überdeckt Ihre Datei die integrierte. Alle anderen Templates rendern weiterhin aus dem integrierten Verzeichnis.

!!! note
    Die Loader-Kette registriert außerdem einen `PrefixLoader` unter dem Schlüssel `@starlette-admin`, der immer auf die integrierten Templates auflöst, egal was sie in `templates_dir` überdeckt. Sie erreichen sie mit dem Pfadformat `@starlette-admin/<name>.html`, wobei der abschließende Slash am Präfix selbst wegfällt. Wozu das dient, sehen Sie unten unter [Ein einzelnes Seitentemplate überschreiben](#ein-einzelnes-seitentemplate-uberschreiben).

## Übersicht über die Template-Verzeichnisse

| Pfad | Gerendert für |
| --- | --- |
| `base.html` | Äußeres HTML-Layout (`<html>`, `<head>`, Skripte) |
| `layout.html` | Sidebar und Topbar-Oberfläche (erweitert `base.html`) |
| `index.html` | Dashboard oder Startseite |
| `list.html` | Modell-Listenseite (Tabelle, Filterleiste, Paginierung) |
| `detail.html` | Detailseite (schreibgeschützt) eines Datensatzes |
| `create.html` | Formular zum Erstellen |
| `edit.html` | Formular zum Bearbeiten |
| `login.html` | Login-Seite |
| `error.html` | HTTP-Fehlerseite (403, 404 usw.) |
| `actions.html` | Modal für Massenaktionen |
| `row-actions.html` | Dropdown-Menü für Zeilenaktionen |
| `inline.html` | Inline-Formset auf der Erstellen-/Bearbeiten-Seite |
| `inline_detail.html` | Inline-Tabelle auf der Detailseite |
| `inline_row.html` | Einzelne Zeile innerhalb eines Inline-Formsets |
| `_filter_bar.html` | Leiste mit aktiven Filter-Chips oberhalb der Liste |
| `_filter_builder.html` | Filter-Builder-Modal |
| `_pagination.html` | Paginierungssteuerung |
| `_column_header.html` | Sortierbare Spaltenkopfzelle |
| `_form_footer.html` | Schaltflächen Speichern, Speichern und weiter oder Weiteren hinzufügen |
| `_form_group.html` | Fieldset einer einzelnen [Formularlayout](form-layout.md)-Gruppe im Erstellen-/Bearbeiten-Formular |
| `_form_group_fields.html` | Die innerhalb einer Formularlayout-Gruppe gerenderten Feldeingaben |
| `fields/list/<type>.html` | Listenspaltenzelle für einen Feldtyp |
| `fields/detail/<type>.html` | Darstellung auf der Detailseite für einen Feldtyp |
| `fields/form/<type>.html` | Formulareingabe-Widget für einen Feldtyp |
| `widgets/<name>.html` | Template für ein Dashboard-Widget |
| `modals/actions.html` | Bestätigungsmodal für Aktionen |
| `modals/delete.html` | Bestätigungsmodal für das Löschen |
| `modals/error.html` | Fehlermodal |
| `modals/import.html` | Import-Modal |
| `macros/views.html` | Gemeinsame Jinja2-Makros, die seitenübergreifend verwendet werden |

!!! note
    Der integrierte Baum enthält außerdem `modals/loading.html`, ein generisches Ladezustands-Modal, sowie mehrere feldspezifische Templates in `fields/list/`, `fields/detail/` und `fields/form/`. Prüfen Sie vor dem Überschreiben einer generischen `<type>.html`-Datei die exakten Dateinamen in `starlette_admin/templates/` für die Version, die Sie installiert haben.

## Ein einzelnes Seitentemplate überschreiben

```
my_templates/
└── list.html   ← shadows the built-in list.html

```

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block content %}
  <div class="alert alert-info">Custom banner above the list.</div>
  {{ super() }}
{% endblock %}

```

`{% extends "list.html" %}` würde wieder zu Ihrem eigenen `my_templates/list.html` auflösen, weil `templates_dir` zuerst geprüft wird, und diese zirkuläre Referenz löst einen Infinite-Recursion-Fehler aus. Das Präfix `@starlette-admin/` zeigt immer auf die integrierte Kopie, deshalb muss jedes `extends` und `include` innerhalb einer Überdeckung dieses Präfix statt des bloßen Dateinamens verwenden.

## Überschreibbare Blöcke

Jede integrierte Seite erweitert `layout.html`, das wiederum `base.html` erweitert. Überschreiben Sie einen einzelnen `{% block %}` statt einer ganzen Datei, um ein Fragment zu ändern, ohne den Rest der Seite zu duplizieren:

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block list_toolbar_extra %}
  {{ super() }}
  <a class="btn btn-outline-primary" href="/reports/export">Custom report</a>
{% endblock %}

```

### `base.html`

| Block | Enthält |
| --- | --- |
| `favicon` | Das Favicon-`<link>`-Tag |
| `title` | Das `<title>`-Tag |
| `head_meta` | Die `<meta>`-Tags innerhalb des `<head>`-Elements |
| `head_css` | Stylesheet-`<link>`-Tags |
| `head` | Ein frei nutzbarer Einfügepunkt innerhalb des `<head>`-Elements |
| `body` | Der gesamte Inhalt von `<body>` (dies wird von `layout.html` überschrieben) |
| `modal` | Ein Einfügepunkt auf Seitenebene für Modals |
| `script` | Die `<script>`-Tags direkt vor dem schließenden `</body>`-Tag |
| `tail` | Ein leerer Einfügepunkt ganz am Ende von `<body>`, nach `script` |

### `layout.html`

| Block | Enthält |
| --- | --- |
| `sidebar` | Das gesamte Sidebar-`<aside>`-Element (einschließlich Nav-Marke, Menü und Footer) |
| `brand` | Das Logo-Bild (oder den `app_title`-Fallback) innerhalb des Nav-Marken-Links in der Sidebar |
| `sidebar_menu` | Die Liste der View-Links innerhalb der Sidebar |
| `sidebar_footer` | Der untere Bereich der Sidebar |
| `user_menu_trigger` | Avatar und Benutzername, die auf der Benutzermenü-Schaltfläche angezeigt werden. Einmal definiert und sowohl in der mobilen Sidebar als auch in der Desktop-Navigationsleiste über `self.user_menu_trigger()` wiederverwendet, sodass eine Überdeckung beide aktualisiert |
| `user_menu_items` | Die Dropdown-Einträge im Benutzermenü |
| `navbar` | Die obere Navigationsleiste |
| `navbar_extra` | Zusätzlicher Inhalt, der neben dem Benutzermenü in der Navigationsleiste platziert wird |
| `header` | Der Seitenkopfbereich oberhalb von `content` (enthält den Titel und die Breadcrumbs) |
| `flash_messages` | Der vorgesehene Bereich zum Rendern von Flash-Nachrichten |
| `content_before` | Ein Einfügepunkt unmittelbar vor `content` |
| `content` | Der Hauptseiteninhalt (dies ist der Block, der von `list.html`, `detail.html` usw. gefüllt wird) |
| `content_after` | Ein Einfügepunkt unmittelbar nach `content` |
| `page_footer` | Der Footer-Bereich unterhalb des Seiteninhalts |

### `list.html`

| Block | Enthält |
| --- | --- |
| `header` | Der Seitenkopf (enthält den Titel und die Breadcrumbs) |
| `page_title` | Die `<h1>`-Überschrift innerhalb des Kopfs |
| `breadcrumbs` | Die Breadcrumb-Navigation innerhalb des Kopfs |
| `modal` | Die Delete-, Action- und Import-Modals |
| `content` | Der vollständige Inhalt der Listenseite |
| `list_search` | Der Sucheingabebereich |
| `list_toolbar` | Die Toolbar-Zeile mit Filter-, Export-, Import- und Erstellen-Schaltflächen |
| `list_toolbar_extra` | Ein zusätzlicher Einfügepunkt ganz am Ende der Toolbar |
| `list_before_table` | Ein Einfügepunkt vor der Tabelle |
| `list_table` | Das `<table>`-Element selbst |
| `list_header` | Die `<thead>`-Zeile mit Checkbox- und Spaltenkopfzellen |
| `list_row` | Eine einzelne `<tr>` in der Ergebnistabelle (ein scoped Block; hat Zugriff auf `row`, `row_pk` und `row_clickable`) |
| `list_row_actions_before` | Die Zeilenaktionszelle, wenn `row_actions_position` gleich `BEFORE_COLUMNS` ist (ein scoped Block) |
| `list_row_actions_after` | Die Zeilenaktionszelle, wenn `row_actions_position` gleich `AFTER_COLUMNS` ist (ein scoped Block) |
| `list_empty` | Der Platzhalter „Keine Daten“ (ein scoped Block, der für leere Zustände gerendert wird) |
| `list_after_table` | Ein Einfügepunkt nach der Tabelle |
| `list_footer` | Der Paginierungs- und Bereichs-Footer |
| `head_css` | Seitenspezifische Stylesheet-Ergänzungen |
| `script` | Seitenspezifische Skript-Ergänzungen |

### `detail.html`

| Block | Enthält |
| --- | --- |
| `header` | Der Seitenkopf (enthält Titel, Breadcrumbs und Aktionen) |
| `page_title` | Die `<h1>`-Überschrift innerhalb des Kopfs |
| `breadcrumbs` | Die Breadcrumb-Navigation innerhalb des Kopfs |
| `modal` | Die Delete- und Action-Modals |
| `content` | Der vollständige Inhalt der Detailseite |
| `detail_before` | Ein Einfügepunkt vor der Detailkarte |
| `detail_title` | Der Titelbereich innerhalb der Detailkarte |
| `detail_actions` | Die Aktionsschaltflächen innerhalb der Detailkarte |
| `details_table` | Die Haupttabelle mit Feldern und Werten |
| `detail_after` | Ein Einfügepunkt nach der Detailkarte |
| `head_css` | Seitenspezifische Stylesheet-Ergänzungen |
| `script` | Seitenspezifische Skript-Ergänzungen |

### `create.html` / `edit.html`

| Block | Enthält |
| --- | --- |
| `header` | Der Seitenkopf (enthält den Titel und die Breadcrumbs) |
| `page_title` | Die `<h1>`-Überschrift innerhalb des Kopfs |
| `breadcrumbs` | Die Breadcrumb-Navigation innerhalb des Kopfs |
| `content` | Der vollständige Inhalt der Formularseite |
| `form_before` | Ein Einfügepunkt vor der Formularkarte |
| `create_card_header` / `edit_card_header` | Der Kopfbereich innerhalb der Formularkarte |
| `create_form` / `edit_form` | Die [Formularlayout](form-layout.md)-Gruppen (jeweils über `_form_group.html` gerendert) und ihre Feldeingabeelemente |
| `create_inlines` / `edit_inlines` | Der Inline-Formset-Bereich |
| `form_footer` | Die Schaltflächen Speichern, Speichern und weiter und Weiteren hinzufügen |
| `form_after` | Ein Einfügepunkt nach der Formularkarte |
| `head_css` | Seitenspezifische Stylesheet-Ergänzungen |
| `script` | Seitenspezifische Skript-Ergänzungen |

### `login.html`

| Block | Enthält |
| --- | --- |
| `header` / `sidebar` | Bleibt leer (die Login-Seite blendet die Standard-Anwendungsoberfläche aus) |
| `content` | Der vollständige Inhalt der Login-Seite |
| `login_logo` | Das Logo, das über dem Login-Formular angezeigt wird |
| `login_title` | Der Titeltext der Login-Seite |
| `login_form_before` | Ein Einfügepunkt vor den Formularfeldern |
| `login_fields` | Die Eingabefelder für Benutzername und Passwort |
| `login_form_footer` | Ein Einfügepunkt nach den Feldern, aber innerhalb des Formulars |
| `login_card_footer` | Ein Einfügepunkt direkt unterhalb der Login-Karte |
| `script` | Seitenspezifische Skript-Ergänzungen |

### `index.html`

| Block | Enthält |
| --- | --- |
| `head_css` | Widget-spezifische Stylesheet-Ergänzungen |
| `content` | Das Dashboard-Widget-Grid |
| `script` | Widget-spezifische Skript-Ergänzungen |

### `error.html`

| Block | Enthält |
| --- | --- |
| `header` / `sidebar` | Bleibt leer (die Fehlerseite blendet die Standard-Anwendungsoberfläche aus) |
| `content` | Die Fehlermeldung und die zugehörigen Aktionen |
| `error_actions` | Unter der Fehlermeldung angezeigte Aktionsschaltflächen (z. B. eine Schaltfläche „Zurück“) |

!!! tip
    Rufen Sie `{{ super() }}` innerhalb einer Überdeckung auf, um den Inhalt des integrierten Blocks beizubehalten und ihn zu ergänzen, statt ihn zu ersetzen. Das Beispiel `list_toolbar_extra` oben macht genau das, und die integrierten `index.html` und `create.html` verwenden dasselbe Muster für den `head_css`-Block.

### Beispiel: Das Sidebar-Logo durch ein Inline-SVG ersetzen

Das Übergeben einer URL an `Admin(logo_url=...)` ist der schnellste Weg, ein Logo zu setzen, und deckt die meisten Fälle ab, auch externe `.svg`-Dateien. Da das integrierte Template diese URL allerdings innerhalb eines `<img>`-Tags rendert, kann das SVG keine CSS-Eigenschaften von der umgebenden Seite erben.

Überschreiben Sie den `brand`-Block mit **Inline-`<svg>`-Markup**, wenn das Logo auf den Rest der Benutzeroberfläche reagieren soll.

#### Implementierung

Erstellen Sie eine `layout.html`-Datei in Ihrem Templates-Verzeichnis. Jede Seite im Admin-Panel erbt von `layout.html`, daher gilt diese eine Überdeckung für die gesamte Anwendung.

```jinja
{# my_templates/layout.html #}
{% extends "@starlette-admin/layout.html" %}

{% block brand %}
  <svg class="navbar-logo" viewBox="0 0 32 32" fill="currentColor">
    <path d="M16 2 L30 9 L30 23 L16 30 L2 23 L2 9 Z" />
  </svg>
{% endblock %}

```

!!! tip "Die Klasse navbar-logo beibehalten"
    Lassen Sie die CSS-Klasse `navbar-logo` an Ihrem benutzerdefinierten `<svg>`-Element. Sie gibt Ihrer Inline-Grafik die Ausrichtung, das Padding und die Größenanpassung des Frameworks, ohne dass Sie eigenes CSS schreiben müssen.

## Field-Templates überschreiben

Jeder Feldkontext verwendet drei Unterverzeichnisse:

| Verzeichnis | Verwendet in |
| --- | --- |
| `fields/list/<type>.html` | Tabellenzelle in der Liste (kompakt, schreibgeschützt) |
| `fields/detail/<type>.html` | Darstellung auf der Detailseite (vollständig, schreibgeschützt) |
| `fields/form/<type>.html` | Formulareingabe für Erstellen und Bearbeiten |

Sie können die Listenzelle für Textfelder überschreiben, ohne das Formular oder die Detaildarstellung anzufassen:

```
my_templates/
└── fields/
    └── list/
        └── text.html

```

Um stattdessen eine einzelne **Feldinstanz** auf Ihr Template verweisen zu lassen, ohne den Typ überall zu überschreiben, setzen Sie `list_template`, `detail_template`, `form_template`, `null_template` oder `empty_template` direkt am Feld:

```python
from starlette_admin.fields import StringField

StringField("status", list_template="fields/list/status_badge.html")
```

`null_template` (Defaultwert `"fields/detail/_null.html"`) und `empty_template` (Defaultwert `"fields/detail/_empty.html"`) sind separate Slots. Die Listen- und Detailseiten rendern sie anstelle von `list_template` bzw. `detail_template`, wann immer der Wert des Feldes `None` oder eine leere Liste bzw. ein leeres Tupel ist:

```python
StringField("status", null_template="fields/detail/_status_null.html")
```

## Widget-Templates überschreiben

Widgets folgen demselben Überdeckungsmuster. Legen Sie Ihre Dateien unter dem Verzeichnis `widgets/` ab:

```
my_templates/
└── widgets/
    └── stat_widget.html

```

## Globale Template-Variablen

Diese Variablen sind in jedem Template verfügbar, ohne dass sie übergeben werden müssen. `Admin` installiert sie einmal während des Setups als Jinja2-Globals:

| Variable | Typ | Beschreibung |
| --- | --- | --- |
| `views` | `list[BaseView]` | Alle registrierten Views (werden zum Rendern der Sidebar verwendet) |
| `app_title` | `str` | Der Titel des Admin-Panels (`Admin(title=...)`) |
| `is_auth_enabled` | `bool` | `True`, wenn ein Auth-Provider konfiguriert ist |
| `__name__` | `str` | Das Routennamen-Präfix des Admin-Panels (z. B. „admin“) |
| `static_url` | `callable` | `static_url(request, path, v=None)` → URL für ein integriertes Static-Asset. Das Argument `v` hängt einen Cache-Busting-Query-Parameter `?v=` an. |
| `logo_url` | `callable` | `logo_url(request)` → URL für das Sidebar-Logo, oder `None`, wenn nicht gesetzt |
| `login_logo_url` | `callable` | `login_logo_url(request)` → URL für das Logo der Login-Seite, oder `None`, wenn nicht gesetzt |
| `favicon_url` | `callable` | `favicon_url(request)` → URL für das Favicon, oder `None`, wenn nicht gesetzt |
| `list_url` | `callable` | `list_url(request, **overrides)` → URL, in deren Query-String `overrides` eingemergt wurden (verwendet für Sortier-, Paginierungs- oder Suchlinks). Übergeben Sie `None`, um einen Schlüssel zu entfernen. |
| `detail_url` | `callable` | `detail_url(request, key, pk)` → URL der Detailseite eines Datensatzes |
| `edit_url` | `callable` | `edit_url(request, key, pk)` → URL der Bearbeitungsseite eines Datensatzes |
| `export_url` | `callable` | `export_url(request, key, fmt)` → Download-URL für den Export, die den Filter-, Sortier- und Suchzustand der aktuellen Listenseite trägt |
| `import_url` | `callable` | `import_url(request, key)` → POST-URL für den Import |
| `get_locale` | `callable` | `get_locale()` → Aktiver Locale-String (erfordert kein `request`-Argument) |
| `get_locale_display_name` | `callable` | `get_locale_display_name(locale)` → Lesbarer Name eines Locale-Strings |
| `i18n_config` | `I18nConfig` | Das i18n-Konfigurationsobjekt des Admin-Panels |
| `get_timezone` | `callable` | `get_timezone()` → Aktiver Timezone-String (erfordert kein `request`-Argument) |
| `get_timezone_display_name` | `callable` | `get_timezone_display_name(timezone, show_offset=False)` → Lesbarer Name eines Timezone-Strings |
| `timezone_config` | `TimezoneConfig | None` | Die Timezone-Konfiguration des Admin-Panels |
| `theme_settings` | `TablerSettings` | Aktive Tabler-Theme-Konfiguration (base, primary, radius, mode), bereitgestellt von `DefaultTheme` |
| `csrf_input` | `callable` | `csrf_input(request)` → Rendert das versteckte CSRF-`<input>` |

!!! note
    `get_locale`, `get_locale_display_name`, `get_timezone` und `get_timezone_display_name` nehmen keinen `request`-Parameter. Sie lesen Locale und Timezone aus `contextvars`, die `LocaleMiddleware` für die Dauer des Requests befüllt, statt aus dem `Request`-Objekt.

## Seitenspezifische Kontextvariablen

Zusätzlich zu den Globals oben übergibt jede Seite ihr eigenes Kontextdictionary an `TemplateResponse`.

### `list.html`

| Variable | Typ | Beschreibung |
| --- | --- | --- |
| `view` | `BaseModelView` | Die aktuelle View |
| `title` | `str` | Seitentitel |
| `fields` | `list[BaseField]` | Derzeit sichtbare Spalten |
| `all_fields` | `list[BaseField]` | Alle Listenfelder (auch versteckte) |
| `rows` | `list[dict]` | Serialisierte Zeilendaten |
| `total` | `int` | Gesamtzahl der passenden Datensätze für die Paginierung |
| `total_pages` | `int` | Gesamtzahl der Seiten |
| `range_start` | `int` | Nummer des ersten Datensatzes auf dieser Seite (1-basiert) |
| `range_end` | `int` | Nummer des letzten Datensatzes auf dieser Seite |
| `list_params` | `ListParams` | Geparster URL-Zustand (page, page_size, q, sorts, filters) |
| `filter_logic` | `str | None` | Ergibt „and“ oder „or“ für die aktive Filtergruppe auf oberster Ebene |
| `filter_chips` | `list` | Deskriptoren der aktiven Filter-Chips |
| `filter_builder_fields` | `list` | Im Filter-Builder-UI verfügbare Felder |
| `raw_filter` | `str | None` | Roher JSON-Filterstring aus der URL |
| `_actions` | `list` | Verfügbare Massenaktionen |
| `row_actions` | `dict[Any, list]` | Verfügbare Zeilenaktionen pro Datensatz, nach pk geschlüsselt |

### `detail.html`

| Variable | Typ | Beschreibung |
| --- | --- | --- |
| `view` | `BaseModelView` | Die aktuelle View |
| `title` | `str` | Seitentitel |
| `obj` | `dict` | Serialisierter Datensatz |
| `raw_obj` | `Any` | Das rohe Modellobjekt vor der Serialisierung |
| `inlines` | `list[dict]` | Inline-Kontext (`[{"inline": InlineModelView, "rows": [...]}]`) |
| `_actions` | `list` | Verfügbare Zeilenaktionen |

### `create.html` / `edit.html`

| Variable | Typ | Beschreibung |
| --- | --- | --- |
| `view` | `BaseModelView` | Die aktuelle View |
| `title` | `str` | Seitentitel |
| `obj` | `dict` | Aktuelle Feldwerte (Defaults beim Erstellen, vorhandene Werte beim Bearbeiten) |
| `raw_obj` | `Any` | Das rohe Modellobjekt (nur beim Bearbeiten, beim Erstellen nicht vorhanden) |
| `errors` | `dict[str, list[str]]` | Validierungsfehler, nach Feldname geschlüsselt (nur nach einem fehlgeschlagenen Absenden vorhanden) |
| `inlines` | `list[dict]` | Inline-Formset-Kontext |

## Eigene Globals und Filter hinzufügen

Um eigene Variablen und Funktionen zu den Templates hinzuzufügen, subclassen Sie `Admin` und überschreiben `__init__`. Rufen Sie zunächst `super().__init__()` auf, damit `self.templates` existiert, bevor Sie etwas hinzufügen:

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
| `is_custom_view` | `view | is_custom_view` | Gibt `True` zurück, wenn die Ressource eine `CustomView` ist |
| `is_link` | `view | is_link` | Gibt `True` zurück, wenn die Ressource ein `Link` ist |
| `is_model_view` | `view | is_model_view` | Gibt `True` zurück, wenn die Ressource eine `BaseModelView` ist |
| `is_dropdown` | `view | is_dropdown` | Gibt `True` zurück, wenn die Ressource ein `DropDown` ist |
| `tojson` | `value | tojson` | HTML-sichere JSON-Serialisierung (ersetzt den Default-`tojson` von Jinja2) |
| `file_icon` | `mime_type | file_icon` | Gibt eine vollständige Icon-Klasse für einen MIME-Typ zurück (z. B. `application/pdf` → `fa-solid fa-fw fa-file-pdf`); überschreiben Sie `self.templates.env.filters["file_icon"]`, um Ihr eigenes Icon-Set zu verwenden |
| `to_view` | `key | to_view` | Sucht eine registrierte `BaseModelView` anhand ihres Key-Strings; wirft eine 404-`HTTPException`, wenn nichts gefunden wurde |
| `is_iter` | `value | is_iter` | Gibt `True` zurück, wenn der Wert eine `list` oder ein `tuple` ist |
| `is_str` | `value | is_str` | Gibt `True` zurück, wenn der Wert ein `str` ist |
| `is_dict` | `value | is_dict` | Gibt `True` zurück, wenn der Wert ein `dict` ist |
| `ra` | `value | ra` | Wandelt einen String in einen `RequestAction`-Enum-Member um |
| `safe_url` | `url | safe_url` | Gibt die URL nur zurück, wenn sie die Safe-URL-Prüfung besteht, sonst `""` |
| `sanitize_html` | `html | sanitize_html` | Entfernt nicht erlaubte Tags aus einem HTML-String und gibt ein `Markup` zurück |

---

## Wie es weitergeht

* **[Formularlayouts](form-layout.md):** Teilen Sie die Erstellen- und Bearbeiten-Formulare in betitelte, optional einklappbare Gruppen auf, und überschreiben Sie `_form_group.html`, um deren Markup zu ändern.
* **[Benutzerdefinierte Themes](https://jowilf.github.io/starlette-admin/advanced/custom-themes/):** Gestalten Sie das Admin-Panel um, ohne einzelne Templates anzufassen.
* **[Benutzerdefinierte Felder](custom-fields.md):** Kombinieren Sie die Python-Klasse eines Feldes mit seinem eigenen `list_template` oder `form_template`.
* **[Erweiterungspunkte](extension-points.md):** Die vollständige Liste der erweiterbaren Oberflächen jenseits der Templates.
