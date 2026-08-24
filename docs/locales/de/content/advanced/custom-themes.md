---
title: Eigene Themes
description: Überschreiben Sie Tabler-CSS-Variablen, binden Sie eigene Stylesheets
  ein und verändern Sie das Gesamtbild Ihres starlette-admin-Dashboards.
source_hash: 385a0c0718253e051a98f4f310990ad32d3e3babcae40ccddf75e59b931fe937
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/custom-themes/)
<!-- translation-notice:end -->

# Eigene Themes

Sie können das Erscheinungsbild des Admin-Bereichs über Theme-Einstellungen, eigene Templates und statische Dateien anpassen. `DefaultTheme` steuert das Standardaussehen, indem es aus einem `TablerSettings`-Objekt heraus Data-Attribute auf dem `<html>`-Tag setzt. Für tiefgreifendere Änderungen können Sie `BaseTheme` ableiten, um Ihre eigenen Templates, statischen Assets und Icon-Sets zu bündeln, oder Ihre eigenen Template- und Static-Verzeichnisse an `Admin` übergeben.

## Ein Theme anwenden

Verwenden Sie `TablerSettings`, um Ihre Farbpalette, den Border-Radius und den Farbmodus festzulegen. Übergeben Sie es an `DefaultTheme` und reichen Sie dieses anschließend an den Parameter `theme` Ihrer `Admin`-Instanz weiter.

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

Unter [examples/08-themes](https://github.com/jowilf/starlette-admin/tree/main/examples/08-themes) finden Sie eine lauffähige Anwendung, die bei jedem Start ein zufälliges Theme auswählt.

Diese Konfiguration setzt die Attribute `data-bs-theme*` direkt auf das Root-Element `<html>`:

```html
<html data-bs-theme="dark"
      data-bs-theme-base="slate"
      data-bs-theme-primary="blue"
      data-bs-theme-radius="2">

```

## Referenz für `TablerSettings`

| Attribut | Typ | Standardwert | Gültige Werte |
| --- | --- | --- | --- |
| `mode` | `str` | `"light"` | `"light"`, `"dark"` |
| `base` | `str | None` | `"stone"` | `"slate"`, `"gray"`, `"zinc"`, `"neutral"`, `"stone"`, `"pink"` |
| `primary` | `str | None` | `"blue"` | `"blue"`, `"azure"`, `"indigo"`, `"purple"`, `"pink"`, `"red"`, `"orange"`, `"yellow"`, `"lime"`, `"green"`, `"teal"`, `"cyan"`, `"inverted"` |
| `radius` | `float | None` | `1` | `0`, `0.5`, `1`, `1.5`, `2` |

## Komponenten mit einer Class Map umgestalten

Die Core-Templates verankern das Styling der Komponenten nicht hart im Code. Stattdessen rendern sie Klassenattribute über den Jinja-Helper `cls('role.name')`, der eine semantische Rolle wie `form.save_button` oder `list.table` in einen CSS-Klassenstring auflöst. Der Standardwert jeder Rolle ist in `starlette_admin.theme.CoreClasses` definiert.

Um eine Rolle umzugestalten, schreiben Sie eine Unterklasse von `ClassMap`. Jede Rolle, die Sie nicht zuordnen, fällt auf `CoreClasses` zurück – partielle Overrides sind also unbedenklich. Beachten Sie, dass eine Button-Rolle das gesamte class-Attribut des Elements festlegt, einschließlich Variante, Größe und Abstand; eine Zuordnung ersetzt daher das Aussehen des Buttons vollständig.

Class Maps erfordern kein vollständiges eigenes Theme. Um das Standard-Theme anzupassen, leiten Sie `DefaultTheme` ab und geben Ihre Map aus `get_class_map()` zurück:

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

Eine vollständige Übersicht aller Rollen finden Sie in `CoreClasses.classes` in `starlette_admin/theme.py`. Die Rollen decken drei Arten von Styling ab:

* **Buttons:** Eine Rolle pro Button-Position, etwa für Formular-Fußbereiche, Listen-Toolbars, Filterleisten, Action-Modals und Inline-Bearbeitung. Der Wert, den Sie setzen, wird zum gesamten class-Attribut des Buttons.
* **Component-Klassen:** Framework-spezifische Klassen, die ein anderes CSS-Framework austauschen muss, beispielsweise `list.table`, `modal.base` oder `filter.chip`.
* **Runtime-Klassen:** Klassen, die das Core-JavaScript dynamisch anwendet, etwa `alert.success` oder `import.status_badge`.

## Eigene Themes erstellen und teilen

Sie können ein Theme als Paket schnüren und auf PyPI veröffentlichen – ganz ähnlich wie ein Plugin. Leiten Sie `BaseTheme` ab, um ein wiederverwendbares Python-Paket zu bauen, das Layout und Styling des Admin-Bereichs über mehrere Projekte hinweg ersetzt, oder um ein visuelles System mit anderen Personen zu teilen.

### Grundgerüst mit Cookiecutter

Beginnen Sie mit der offiziellen Cookiecutter-Vorlage. Sie erzeugt ein veröffentlichbares Paket mit der richtigen Verzeichnisstruktur und den passenden Konfigurationsdateien.

Installieren Sie `cookiecutter` mit Ihrem Paketmanager. Details dazu finden Sie in der [offiziellen Installationsanleitung](https://cookiecutter.readthedocs.io/en/stable/README.html#installation):

```bash
pip install cookiecutter

```

Führen Sie die Vorlage anschließend aus einem beliebigen Verzeichnis aus:

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme

```

Die Vorlage fragt Sie nach dem Namen des Themes, dem Package-Slug, der Version und einigen weiteren Variablen. Nach Abschluss verfügen Sie über ein in sich geschlossenes Paket mit:

* einem `src/`-Verzeichnis, das die Theme-Klasse, das Icon-Set und die Class Map enthält,
* vorkonfigurierten Ordnern für `templates/`, `static/` und Übersetzungen,
* einer Testsuite und einer lauffähigen Beispielanwendung.

### Architektur von `BaseTheme`

Ein Theme steht an der Wurzel der Rendering-Kette, und jede `Admin`-Instanz hat genau ein aktives Theme. Eine Unterklasse von `BaseTheme` konfiguriert folgende Bausteine:

* **Templates:** Ersetzende Templates im Ordner `templates/` des Pakets, angegeben als schlichte relative Pfade wie `base.html`, `layout.html` oder `list.html`. Das aktive Theme steht in Jinjas Loader-Kette oberhalb der Plugins und kann daher sowohl Core- als auch Plugin-Templates umgestalten.
* **Statische Assets:** Stylesheets, Skripte und Bilder im Ordner `static/` des Pakets.
* **Icon-Set:** Eine eigene Unterklasse von `IconSet`, die `get_icon_set()` zurückgibt und semantische Schlüssel wie `list.new` oder `auth.logout` auf CSS-Klassen abbildet.
* **Class Map:** Eine Unterklasse von `ClassMap`, die `get_class_map()` zurückgibt, wie unter [Komponenten mit einer Class Map umgestalten](#komponenten-mit-einer-class-map-umgestalten) beschrieben.
* **Template-Globals:** Globale Variablen, die Jinja durch das Überschreiben von `template_globals()` bereitgestellt werden.

### Beispiel-Theme-Paket

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

### Hierarchie des Template-Loaders

Die Template-Engine löst Dateien in dieser Reihenfolge auf:

1. Ihr `templates_dir`, das alles darunterliegende überschreibt.
2. Der Ordner `templates/` des aktiven Themes, der Core- und Plugin-Templates umgestaltet.
3. Die namespaced Plugin-Ordner `templates/`.
4. Die Standard-Templates des Core-Pakets `starlette_admin`.

Um ein Theme-Template aus einem User-Override oder einer Theme-Unterklasse heraus zu erweitern, verwenden Sie den Jinja-Präfix `@theme`, beispielsweise `{% extends "@theme/layout.html" %}`.

## Eigenes Template-Verzeichnis

Um das Standard-HTML zu überschreiben, ohne ein vollständiges Theme zu bauen, übergeben Sie einen Verzeichnispfad an `templates_dir`.

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

Jede Datei, die Sie in diesem Verzeichnis ablegen, überlagert das eingebaute Template am selben relativen Pfad; der Rest des eingebauten Verzeichnisbaums wird unverändert gerendert. Eine vollständige Liste der überschreibbaren Templates finden Sie unter [Templates](templates.md).

## Eigenes Static-Verzeichnis

Um eigene CSS-, JavaScript- oder Bilddateien einzubinden, ohne ein vollständiges Theme zu bauen, übergeben Sie einen Verzeichnispfad an `static_dir`.

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

Dateien in diesem Verzeichnis werden zusammen mit den eingebauten Assets unter `/admin/static/` ausgeliefert. Eine Datei unter `my_static/custom.css` ist beispielsweise unter `/admin/static/custom.css` erreichbar.

Binden Sie das Stylesheet in Ihren Templates so ein:

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">

```

---

## Wie es weitergeht

* **[Templates](templates.md):** Überschreiben Sie eine einzelne Seite, Zelle oder ein Widget, ohne den gesamten Template-Baum zu forken.
* **[Extension Points](extension-points.md):** Entdecken Sie Hooks und Anpassungspunkte jenseits der grundlegenden Themes.
* **[Quickstart](../getting-started/quickstart.md):** Bauen Sie eine funktionsfähige Admin-Oberfläche von Grund auf.
