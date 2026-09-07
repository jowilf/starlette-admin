---
title: Plugins
description: Wiederverwendbare Admin-Funktionen und Erweiterungen als Drop-in-Plugins
  für starlette-admin paketieren.
source_hash: c9ecd9e51a7426d12b628b06c9c664579e5f269d456e93e9d985c4d2853ac758
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/plugins/)
<!-- translation-notice:end -->

# Plugins

Ein Plugin ist ein Python-Paket, das `starlette-admin` über ein einzelnes Konstruktorargument erweitert. Ein Plugin kann beliebige Kombinationen aus Feldern, Templates, statischen Assets, Modell-Konvertern, Filtern, Import-/Exportformaten, Storage-Backends, Event-Subscribern, Views, Routen, Middlewares, Theme-Assets und Übersetzungskatalogen bündeln.

## Ein Plugin verwenden

Übergeben Sie Plugins über das Argument `plugins`, wenn Sie Ihre `Admin`-Instanz konstruieren:

```python
from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[GeospatialPlugin(default_zoom=13)])
```

Der Plugin-Konstruktor nimmt die Optionen entgegen, und die Liste geht direkt an `Admin`. Es gibt nichts weiter einzurichten oder zu registrieren. Die Optionen fließen vom Konstruktor bis zum Python-Backend, den Jinja-Templates und dem Frontend-JavaScript durch.

## Ein Plugin entwickeln

Um ein Plugin zu schreiben, beginnen Sie mit der offiziellen Cookiecutter-Vorlage. Sie erzeugt ein veröffentlichbares Paket mit der richtigen Verzeichnisstruktur und Konfiguration.

### Voraussetzungen

Installieren Sie `cookiecutter` mit Ihrem Paketmanager. Details finden Sie in der [offiziellen Installationsanleitung](https://cookiecutter.readthedocs.io/en/stable/README.html#installation):

```bash
pip install cookiecutter
```

### Scaffolding

Führen Sie die Cookiecutter-Vorlage von einem beliebigen Ort aus:

```bash
cookiecutter gh:jowilf/starlette-admin --directory plugins/cookiecutter-starlette-admin-plugin
```

Die Vorlage fragt Sie nach dem Plugin-Namen, dem Paket-Slug, der Version und einigen weiteren Variablen. Nach Abschluss verfügen Sie über ein in sich geschlossenes Paket mit:

* Einem `src/`-Verzeichnis, das Ihre Plugin-Klasse und Ihre Felder enthält.
* Korrekt namespaced angelegten Ordnern `templates/`, `static/` und `translations/`.
* Einer vollständigen Testsuite.
* Einer lauffähigen Beispielanwendung.

## Die Plugin-API

Im Kern jedes Plugins steht eine Unterklasse von `BasePlugin` (`starlette_admin.plugins.BasePlugin`), die Ihnen Hooks bereitstellt, um Ihre Features zu registrieren, während `Admin` initialisiert wird.

```python
from starlette_admin.plugins import BasePlugin


class MyPlugin(BasePlugin):
    name = "my-plugin"
```

Das Attribut `name` ist ein eindeutiger Bezeichner im kebab-case, der zugleich als Namespace für Ihre Templates und statischen Assets dient. Jedes Template und jede statische Datei, die Ihr Plugin ausliefert, muss unter `plugins/<name>/` liegen.

### Asset-Ordner

Ein Plugin kann genau drei Ordner im Stammverzeichnis seines Pakets führen. Es gibt nichts zu registrieren, da die Admin-Anwendung sie per Konvention findet:

* `templates/`: Jinja-Templates, die unter `templates/plugins/<name>/` liegen müssen.
* `static/`: Statische Assets wie CSS- und JS-Dateien, die unter `static/plugins/<name>/` liegen müssen.
* `translations/`: Babel-Übersetzungskataloge.

Wenn Sie sich innerhalb des Namespaces `plugins/<name>/` bewegen, kollidieren Ihre Assets weder mit Kerndateien noch mit anderen Plugins, während sie weiterhin über das eigene `templates_dir` bzw. `static_dir` des Benutzers überschreibbar bleiben.

### Deklarative Hooks

Überschreiben Sie die deklarativen Hooks, um Assets einzubinden, Views zu registrieren oder Routen zu mounten.

* `css_links(self, request: Request) -> Sequence[str]`: Fügt Stylesheets zum Layout jeder Admin-Seite hinzu.
* `js_links(self, request: Request) -> Sequence[str]`: Fügt Skripte zum Layout jeder Admin-Seite hinzu.
* `views(self) -> Sequence[BaseView]`: Liefert die Views zurück, die in der Admin-Sidebar registriert werden sollen. Geben Sie ein `DropDown` zurück, um sie zu gruppieren.
* `routes(self) -> Sequence[Route | Mount]`: Liefert headless Endpoints zurück, die unter `/plugins/<name>/` gemountet werden – praktisch für Webhooks und Proxy-Endpoints.
* `middlewares(self) -> Sequence[Middleware]`: Fügt Starlette-Middlewares hinzu.
* `template_globals(self) -> dict[str, Any]`: Stellt Jinja-Globals bereit, mit dem Präfix `<name>_` versehen, damit Kollisionen ausgeschlossen sind.
* `template_filters(self) -> dict[str, Callable]`: Stellt Jinja-Filter auf dieselbe Weise mit dem Präfix `<name>_` bereit.

### Der Setup-Hook

`setup(self, admin: BaseAdmin) -> None` integriert Ihr Plugin in die zentralen Registries. Nutzen Sie ihn, um Modell-Konverter, Filter, Import- und Exportformate, Storage-Backends sowie Event-Subscriber zu registrieren. Er wird ausgeführt, nachdem die deklarativen Hooks angewendet wurden.

```python
def setup(self, admin: "BaseAdmin") -> None:
    admin.events.subscribe(MyEventSubscriber(self.config))
```

### Der Lifecycle-Hook

`on_mount(self, admin: BaseAdmin) -> None` läuft genau einmal, nachdem die Starlette-Subanwendung gebaut und gemountet wurde. Die gebaute Anwendung steht als `admin.app` zur Verfügung.

## Templates und Overrides

Plugin-Templates werden automatisch in die Loader-Kette aufgenommen. Ein Benutzer überschreibt eines, indem er eine Datei am entsprechenden Pfad innerhalb seines eigenen `templates_dir` ablegt; dieser Pfad hat immer Vorrang. Um beispielsweise `plugins/geospatial/fields/form/point.html` zu überschreiben, legt er `templates_dir/plugins/geospatial/fields/form/point.html` an.

Damit ein Benutzer-Override das Original sicher erweitern kann, erhält jedes Plugin ein Präfix-Mapping `@<name>`, das genauso funktioniert wie das Präfix `@core`. Der Override beginnt mit `{% extends "@geospatial/fields/form/point.html" %}` und erweitert das Basis-Template des Plugins, ohne sich selbst rekursiv einzuschließen.

## Frontend-JavaScript-Integration

Ein Plugin, das eigene Felder ausliefert, sollte seine Frontend-Skripte gemäß dem Field-Initializer-Vertrag paketieren. So funktionieren sie sowohl bei vollständigen Seitenladevorgängen als auch bei dynamisch eingefügten Fragmenten.

* **Lokal zielen:** Fragen Sie innerhalb des übergebenen Elements `container` ab, niemals global über `document`.
* **Idempotent sein:** Der Core führt den Initializer beim DOM ready aus und erneut, wann immer er Inline-Zeilen oder Fragmente einfügt.
* **Data-Attribute verwenden:** Lesen Sie die Konfiguration aus den `data-*`-Attributen, die auf dem Feldelement gerendert werden.

```javascript title="plugins/<name>/js/slider.js"
(function () {
  function initSlider(container) {
    var input = container.querySelector('input[type="range"]');
    var output = container.querySelector(".sa-slider-output");
    var suffix = container.dataset.suffix || "";

    input.addEventListener("input", function () {
      output.textContent = input.value + suffix;
    });
  }

  // Register the initializer so core runs it on the right lifecycle events
  window.StarletteAdmin.registerFieldInitializer(function (element) {
    element.querySelectorAll("[data-sa-slider]").forEach(initSlider);
  });
})();
```

## Erweiterungspunkte über den Setup-Hook

Plugins nutzen die vorhandenen öffentlichen Registries statt eines separaten eigenen Erweiterungswegs.

* **Konverter**: Rufen Sie `register_converter` – aus dem Contrib-Backend, das Sie ansteuern – auf, um ORM-Spaltentypen Ihren Feldklassen zuzuordnen. Definieren Sie das Feld selbst als gewöhnliche `StringField`-Unterklasse, die Geometrien als WKT-Text speichert und anzeigt:

  ```python
  from dataclasses import dataclass
  from typing import Any

  from starlette_admin.contrib.sqla.converters import register_converter
  from starlette_admin.fields import StringField


  @dataclass
  class MyGeoField(StringField): ...


  @register_converter("Geometry")
  def convert_geometry(*args: Any, **kwargs: Any) -> MyGeoField:
      return MyGeoField(*args, **kwargs)
  ```

* **Filter**: Rufen Sie `register_filters` auf, um Filterklassen an einen Feldtyp anzuhängen.

  ```python
  from starlette_admin.contrib.sqla.filters import register_filters

  register_filters(MyGeoField, WithinBoundingBoxFilter)
  ```

* **Storage**: Rufen Sie `register_storage` auf, um ein neues Backend bereitzustellen, etwa Azure oder GCS.

  ```python
  from starlette_admin.storage import register_storage

  register_storage(AzureBlobStorage())
  ```

* **Importer und Exporter**: Verwenden Sie `register_import_format` und `register_export_format`.

  ```python
  from starlette_admin.export import register_export_format

  register_export_format("pdf", PDFExporter())
  ```

Ein Plugin kann mehrere ORM-Backends unterstützen; importieren Sie daher bedingt innerhalb von `setup()`. Auf diese Weise lädt das Plugin weiterhin, auch wenn der Benutzer nur eines davon installiert hat:

```python
def setup(self, admin: "BaseAdmin") -> None:
    try:
        from starlette_admin_geospatial.contrib.sqla import register_sqla_converters

        register_sqla_converters()
    except ImportError:
        pass  # geoalchemy2 or sqlalchemy not installed
```

---

## Wie es weitergeht

* **[Eigene Themes](custom-themes.md):** Paketieren und teilen Sie ein vollständiges visuelles System – mit demselben Cookiecutter-Workflow.
* **[Events](events.md):** Die Subscriber-API, die ein Plugin über seinen `setup()`-Hook registriert.
* **[Erweiterungspunkte](extension-points.md):** Jede Registry und jede Basisklasse, in die ein Plugin eingreifen kann.
