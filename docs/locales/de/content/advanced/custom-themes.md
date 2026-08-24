---
title: Custom Themes
description: Tabler-CSS-Variablen überschreiben, eigene Stylesheets einbinden und
  die Gesamtästhetik Ihres starlette-admin-Dashboards anpassen.
source_hash: 385a0c0718253e051a98f4f310990ad32d3e3babcae40ccddf75e59b931fe937
prompt_hash: e74e266b22cedf72eaa794c2ae7a360fd32046953223afb4ffa22b1342d51b63
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-24'
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/custom-themes/)
<!-- translation-notice:end -->

# Custom Themes

Sie können das Admin-Interface über Theme-Einstellungen, benutzerdefinierte Templates und statische Dateien umgestalten. `DefaultTheme` steuert den Standard-Look, indem es aus einem `TablerSettings`-Objekt heraus Data-Attribute auf das `<html>`-Tag schreibt. Für tiefere Änderungen leiten Sie von `BaseTheme` ab, um Ihre eigenen Templates, statischen Assets und Icon-Sets zu bündeln, oder übergeben Sie Ihre eigenen Template- und Static-Verzeichnisse an `Admin`.

## Ein Theme anwenden

Verwenden Sie `TablerSettings`, um Ihre Farbpalette, den Border-Radius und den Color-Mode festzulegen. Übergeben Sie es an `DefaultTheme` und dann dieses an den Parameter `theme` Ihrer `Admin`-Instanz.

```python
from myapp.models import Post
from sqlalchemy import create_engine
from starlette_admin.theme import DefaultTheme, TablerSettings
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///admin.sqlite")

admin = Admin(
    engine,
    title="My Admin",
    theme=DefaultTheme(
        settings=TablerSettings(base="slate", primary="blue", radius=2, mode="dark")
    ),
)
admin.add_view(ModelView(Post))
```

Unter [examples/08-themes](https://github.com/jowilf/starlette-admin/tree/main/examples/08-themes) finden Sie eine lauffähige App, die bei jedem Start ein zufälliges Theme auswählt.

Diese Konfiguration wendet die Attribute `data-bs-theme*` direkt auf das Wurzel-Element `<html>` an:

```html
<html data-bs-theme="dark"
      data-bs-theme-base="slate"
      data-bs-theme-primary="blue"
      data-bs-theme-radius="2">

```

## `TablerSettings`-Referenz

| Attribut | Typ | Defaultwert | Gültige Werte |
| --- | --- | --- | --- |
| `mode` | `str` | `"light"` | `"light"`, `"dark"` |
| `base` | `str | None` | `"stone"` | `"slate"`, `"gray"`, `"zinc"`, `"neutral"`, `"stone"`, `"pink"` |
| `primary` | `str | None` | `"blue"` | `"blue"`, `"azure"`, `"indigo"`, `"purple"`, `"pink"`, `"red"`, `"orange"`, `"yellow"`, `"lime"`, `"green"`, `"teal"`, `"cyan"`, `"inverted"` |
| `radius` | `float | None` | `1` | `0`, `0.5`, `1`, `1.5`, `2` |

## Komponenten mit einer Class Map umgestalten {#restyling-components-with-a-class-map}

Die Kern-Templates hardcoden das Styling der Komponenten nicht. Sie rendern Klassenattribute über den Jinja-Helper `cls('role.name')`, der eine semantische Rolle wie `form.save_button` oder `list.table` zu einem String aus CSS-Klassen auflöst. Der Defaultwert für jede Rolle liegt in `starlette_admin.theme.CoreClasses`.

Um eine Rolle umzugestalten, schreiben Sie eine `ClassMap`-Unterklasse. Jede Rolle, die Sie nicht mappen, fällt auf `CoreClasses` zurück, daher sind partielle Überschreibungen sicher. Beachten Sie, dass eine Button-Rolle das gesamte Klassenattribut des Elements festlegt, einschließlich Variante, Größe und Abstände. Das Mappen einer solchen Rolle ersetzt also das Erscheinungsbild des Buttons komplett.

Class Maps erfordern kein vollständiges benutzerdefiniertes Theme. Um das Standard-Theme anzupassen, leiten Sie von `DefaultTheme` ab und geben Sie Ihr Mapping von `get_class_map()` zurück:

```python
from starlette_admin.theme import ClassMap, DefaultTheme


class MyClasses(ClassMap):
    classes = {
        # Rounded success save button instead of the default primary one
        "form.save_button": "btn btn-success rounded-pill",
        # Outline create button on the list toolbar
        "list.create_button": "btn btn-outline-primary ms-2",
        # Pill-shaped filter chips
        "filter.chip": "badge rounded-pill bg-primary-subtle",
    }


class MyTheme(DefaultTheme):
    def get_class_map(self) -> ClassMap:
        return MyClasses()


admin = Admin(engine, title="My Admin", theme=MyTheme())
```

Sehen Sie sich `CoreClasses.classes` in `starlette_admin/theme.py` an, um das gesamte Vokabular der Rollen kennenzulernen. Rollen decken drei Arten von Styling ab:

* **Buttons:** Eine Rolle pro Button-Position, die Formular-Footer, Listen-Toolbars, Filterleisten, Aktions-Modals und Inline-Bearbeitung abdeckt. Der Wert, den Sie setzen, wird zum gesamten Klassenattribut des Buttons.
* **Komponenten-Klassen:** Framework-spezifische Klassen, die ein anderes CSS-Framework austauschen muss, etwa `list.table`, `modal.base` oder `filter.chip`.
* **Runtime-Klassen:** Klassen, die das Kern-JavaScript dynamisch anwendet, etwa `alert.success` oder `import.status_badge`.

## Benutzerdefinierte Themes erstellen und teilen

Sie können ein Theme paketieren und auf PyPI veröffentlichen, ähnlich wie ein Plugin. Leiten Sie von `BaseTheme` ab, um ein wiederverwendbares Python-Paket zu bauen, das Layout und Styling des Admins in mehreren Projekten ersetzt, oder um ein visuelles System mit anderen Menschen zu teilen.

### Grundgerüst mit Cookiecutter erstellen

Beginnen Sie mit dem offiziellen Cookiecutter-Template. Es generiert ein veröffentlichtbares Paket mit der richtigen Verzeichnisstruktur und den passenden Konfigurationsdateien.

Installieren Sie `cookiecutter` mit Ihrem Paketmanager. Einzelheiten finden Sie im [offiziellen Installationsleitfaden](https://cookiecutter.readthedocs.io/en/stable/README.html#installation):

```bash
pip install cookiecutter

```

Führen Sie das Template anschließend aus einem beliebigen Verzeichnis aus:

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme

```

Das Template fragt Sie nach dem Namen des Themes, dem Package-Slug, der Version und einigen weiteren Variablen. Wenn es fertig ist, haben Sie ein in sich geschlossenes Paket mit:

* Einem `src/`-Verzeichnis, das die Theme-Klasse, das Icon-Set und die Class Map enthält.
* Vorkonfigurierten Ordnern für `templates/`, `static/` und Übersetzungen.
* Einer Testsuite und einer lauffähigen Beispielanwendung.

### `BaseTheme`-Architektur

Ein Theme sitzt am Anfang der Renderkette, und jede `Admin`-Instanz hat genau ein aktives Theme. Eine `BaseTheme`-Unterklasse konfiguriert folgende Teile:

* **Templates:** Ersatz-Templates im Ordner `templates/` des Pakets, mit bloßen relativen Pfaden wie `base.html`, `layout.html` oder `list.html`. Das aktive Theme steht in Jinjas Loader-Kette oberhalb der Plugins und kann daher sowohl Kern-Templates als auch Plugin-Templates umgestalten.
* **Statische Assets:** Stylesheets, Skripte und Bilder im Verzeichnis `static/` des Pakets.
* **Icon-Set:** Eine benutzerdefinierte `IconSet`-Unterklasse, die von `get_icon_set()` zurückgegeben wird und semantische Schlüssel wie `list.new` oder `auth.logout` auf CSS-Klassen abbildet.
* **Class Map:** Eine `ClassMap`-Unterklasse, die von `get_class_map()` zurückgegeben wird, wie unter [Komponenten mit einer Class Map umgestalten](#restyling-components-with-a-class-map) beschrieben.
* **Template-Globals:** Globale Variablen, die Jinja durch das Überschreiben von `template_globals()` bereitgestellt werden.

### Beispiel für ein Theme-Paket

```python
from typing import Any
from starlette_admin.theme import BaseTheme, ClassMap, IconSet


class CustomIconSet(IconSet):
    icons = {
        "list.new": "hi hi-plus",
        "default_actions.view": "hi hi-eye",
        # Map remaining semantic icon keys
    }


class CorporateClasses(ClassMap):
    classes = {
        "form.save_button": "btn btn-corporate",
        # Map remaining roles to restyle; unmapped roles keep core defaults
    }


class CorporateTheme(BaseTheme):
    name = "corporate"
    package = "corporate_theme_package"  # Auto-detected from class module if omitted

    def get_icon_set(self) -> IconSet:
        return CustomIconSet()

    def get_class_map(self) -> ClassMap:
        return CorporateClasses()

    def template_globals(self) -> dict[str, Any]:
        return {"company_name": "Acme Corp"}
```

### Template-Loader-Hierarchie

Die Template-Engine löst Dateien in dieser Reihenfolge auf:

1. Ihr `templates_dir`, das alles darunterliegende überschreibt.
2. Das `templates/`-Verzeichnis des aktiven Themes, das Kern- und Plugin-Templates umgestaltet.
3. Die `templates/` der Plugins mit ihrem Namespace.
4. Die Standard-Templates von `starlette_admin`.

Um ein Theme-Template von einer Benutzer-Überschreibung oder einer Theme-Unterklasse aus zu erweitern, verwenden Sie das Jinja-Präfix `@theme`, zum Beispiel `{% extends "@theme/layout.html" %}`.

## Benutzerdefiniertes Templates-Verzeichnis

Um das standardmäßige HTML zu überschreiben, ohne ein vollständiges Theme zu bauen, übergeben Sie einen Verzeichnispfad an `templates_dir`.

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

Jede Datei, die Sie in dieses Verzeichnis legen, verdeckt das integrierte Template am selben relativen Pfad, und der Rest des integrierten Baums rendert weiterhin wie zuvor. Die vollständige Liste der überschreibbaren Templates finden Sie unter [Templates](templates.md).

## Benutzerdefiniertes Static-Verzeichnis

Um Ihre eigenen CSS-, JavaScript- oder Bilddateien hinzuzufügen, ohne ein vollständiges Theme zu bauen, übergeben Sie einen Verzeichnispfad an `static_dir`.

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

Dateien in diesem Verzeichnis werden zusammen mit den integrierten Assets unter `/admin/static/` ausgeliefert. Eine Datei unter `my_static/custom.css` ist beispielsweise unter `/admin/static/custom.css` verfügbar.

Referenzieren Sie das Stylesheet in Ihren Templates wie folgt:

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">

```

---

## Was kommt als Nächstes?

* **[Templates](templates.md):** Überschreiben Sie eine einzelne Seite, Zelle oder ein Widget, ohne den gesamten Template-Baum zu forken.
* **[Extension Points](extension-points.md):** Erkunden Sie Hooks und Anpassungspunkte jenseits einfacher Themes.
* **[Quickstart](../getting-started/quickstart.md):** Bauen Sie ein funktionierendes Admin-Interface von Grund auf.
