---
title: Plugins
description: Wiederverwendbare Admin-Funktionen und Erweiterungen als Drop-in-Plugins
  für starlette-admin paketieren.
source_hash: c9ecd9e51a7426d12b628b06c9c664579e5f269d456e93e9d985c4d2853ac758
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/plugins/)
<!-- translation-notice:end -->

# Plugins

Ein Plugin ist ein Python-Paket, das `starlette-admin` über ein einzelnes Konstruktorargument erweitert. Ein Plugin kann jede beliebige Kombination aus Feldern, Templates, statischen Assets, Modellkonvertern, Filtern, Import-/Exportformaten, Storage-Backends, Event-Subscribern, Views, Routes, Middlewares, Theme-Assets und Übersetzungskatalogen bündeln.

## Ein Plugin verwenden

Übergeben Sie Plugins über das Argument `plugins`, wenn Sie Ihre `Admin`-Instanz konstruieren:

```python
from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[GeospatialPlugin(default_zoom=13)])
```

Der Plugin-Konstruktor nimmt die Optionen entgegen, und die Liste geht direkt an `Admin`. Es gibt nichts weiter einzurichten oder zu registrieren. Die Optionen fließen vom Konstruktor hinunter zum Python-Backend, zu den Jinja-Templates und zum Frontend-JavaScript.

## Ein Plugin erstellen

Um ein Plugin zu schreiben, beginnen Sie mit dem offiziellen Cookiecutter-Template. Es erzeugt ein veröffentlichungsfähiges Paket mit der richtigen Verzeichnisstruktur und Konfiguration.

### Voraussetzungen

Installieren Sie `cookiecutter` mit Ihrem Paketmanager. Einzelheiten finden Sie in der [offiziellen Installationsanleitung](https://cookiecutter.readthedocs.io/en/stable/README.html#installation):

```bash
pip install cookiecutter
```

### Scaffolding

Führen Sie das Cookiecutter-Template von einem beliebigen Ort aus:

```bash
cookiecutter gh:jowilf/starlette-admin --directory plugins/cookiecutter-starlette-admin-plugin
```

Das Template fragt Sie nach dem Plugin-Namen, dem Paket-Slug, der Version und einigen weiteren Variablen. Wenn es fertig ist, haben Sie ein in sich geschlossenes Paket mit:

* Einem `src/`-Verzeichnis, das Ihre Plugin-Klasse und Felder enthält.
* Korrekt namespaceden Ordnern für `templates/`, `static/` und `translations/`.
* Einer vollständigen Testsuite.
* Einer lauffähigen Beispielanwendung.

## Die Plugin-API

Im Kern jedes Plugins steht eine Unterklasse von `BasePlugin` (`starlette_admin.plugins.BasePlugin`), die Ihnen Hooks zur Verfügung stellt, um Ihre Features zu registrieren, während `Admin` initialisiert wird.

```python
from starlette_admin.plugins import BasePlugin


class MyPlugin(BasePlugin):
    name = "my-plugin"
```

Das Attribut `name` ist ein eindeutiger Kebab-case-Identifier, der zugleich als Namespace für Ihre Templates und statischen Assets dient. Jedes Template und jede statische Datei, die Ihr Plugin ausliefert, muss unter `plugins/<name>/` liegen.

### Asset-Ordner

Ein Plugin kann genau drei Ordner im Root seines Pakets führen. Es gibt nichts zu registrieren, weil das Admin sie per Konvention findet:

* `templates/`: Jinja-Templates, die unter `templates/plugins/<name>/` liegen müssen.
* `static/`: Statische Assets wie CSS- und JS-Dateien, die unter `static/plugins/<name>/` liegen müssen.
* `translations/`: Babel-Übersetzungskataloge.

Wenn Sie sich innerhalb des `plugins/<name>/`-Namespaces halten, kollidieren Ihre Assets nicht mit Core-Dateien oder anderen Plugins, während sie weiterhin durch das eigene `templates_dir` oder `static_dir` des Users überschreibbar bleiben.

### Deklarative Hooks

Überschreiben Sie die deklarativen Hooks, um Assets einzuschleusen, Views zu registrieren oder Routes zu mounten.

* `css_links(self, request: Request) -> Sequence[str]`: Fügt Stylesheets zu jedem Admin-Seitenlayout hinzu.
* `js_links(self, request: Request) -> Sequence[str]`: Fügt Scripts zu jedem Admin-Seitenlayout hinzu.
* `views(self) -> Sequence[BaseView]`: Gibt die Views zurück, die in der Admin-Sidebar registriert werden sollen. Geben Sie ein `DropDown` zurück, um sie zu gruppieren.
* `routes(self) -> Sequence[Route | Mount]`: Gibt headless Endpoints zurück, die unter `/plugins/<name>/` gemountet werden, was sich gut für Webhooks und Proxy-Endpoints eignet.
* `middlewares(self) -> Sequence[Middleware]`: Fügt Starlette-Middlewares hinzu.
* `template_globals(self) -> dict[str, Any]`: Stellt Jinja-Globals bereit, mit dem Präfix `<name>_` versehen, damit sie nicht kollidieren können.
* `template_filters(self) -> dict[str, Callable]`: Stellt Jinja-Filter auf dieselbe Weise bereit, ebenfalls mit dem Präfix `<name>_`.

### Der setup-Hook

`setup(self, admin: BaseAdmin) -> None` integriert Ihr Plugin in die Core-Registries. Nutzen Sie ihn, um Modellkonverter, Filter, Import- und Exportformate, Storage-Backends und Event-Subscriber zu registrieren. Er läuft nach den deklarativen Hooks.

```python
def setup(self, admin: "BaseAdmin") -> None:
    admin.events.subscribe(MyEventSubscriber(self.config))
```

### Der Lifecycle-Hook

`on_mount(self, admin: BaseAdmin) -> None` läuft genau einmal, nachdem die Starlette-Sub-Anwendung gebaut und gemountet wurde. Die gebaute Anwendung ist als `admin.app` verfügbar.

## Templates und Overrides

Plugin-Templates treten der Loader-Kette automatisch bei. Ein User überschreibt eines, indem er eine Datei am passenden Pfad innerhalb seines eigenen `templates_dir` ablegt; dieser hat immer Vorrang. Um zum Beispiel `plugins/geospatial/fields/form/point.html` zu überschreiben, erstellt er `templates_dir/plugins/geospatial/fields/form/point.html`.

Damit ein User-Override das Original sicher erweitern kann, erhält jedes Plugin ein Präfix-Mapping `@<name>`, das genauso funktioniert wie das Präfix `@core`. Das Override beginnt mit `{% extends "@geospatial/fields/form/point.html" %}` und erweitert das Basis-Template des Plugins, ohne sich selbst rekursiv einzubinden.

## Frontend-JavaScript-Integration

Ein Plugin, das benutzerdefinierte Felder ausliefert, sollte seine Frontend-Scripts nach dem Field-Initializer-Vertrag paketieren. So funktionieren sie sowohl bei vollständigen Seitenladevorgängen als auch bei dynamisch eingefügten Fragmenten.

* **Lokal zielen:** Fragen Sie innerhalb des `container`-Elements ab, das Sie erhalten, niemals im globalen `document`.
* **Idempotent sein:** Der Core führt den Initializer beim DOM-ready-Ereignis aus und erneut, wann immer er Inline-Zeilen oder Fragmente einfügt.
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

## Extension Points über den setup-Hook

Plugins nutzen die bestehenden öffentlichen Registries statt eines eigenen separaten Erweiterungspfads.

* **Converter**: Rufen Sie `register_converter` auf, aus dem Contrib-Backend, auf das Sie abzielen, um ORM-Spaltentypen auf Ihre Feldklassen abzubilden. Definieren Sie das Feld selbst als gewöhnliche `StringField`-Unterklasse, die Geometrien als WKT-Text speichert und anzeigt:

  ```python
  from dataclasses import dataclass
  from typing import Any

  from starlette_admin.contrib.sqla.converters import register_converter
  from starlette_admin.fields import StringField


  @dataclass
  class MyGeoField(StringField):
    ...


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

Ein Plugin kann mehrere ORM-Backends unterstützen, importieren Sie diese daher bedingt innerhalb von `setup()`. Auf diese Weise lädt das Plugin weiterhin, wenn der User nur eines davon installiert hat:

```python
def setup(self, admin: "BaseAdmin") -> None:
    try:
        from starlette_admin_geospatial.contrib.sqla import register_sqla_converters

        register_sqla_converters()
    except ImportError:
        pass  # geoalchemy2 or sqlalchemy not installed
```

---

## Was kommt als Nächstes

* **[Custom Themes](custom-themes.md):** Ein komplettes visuelles System paketieren und teilen, mit demselben Cookiecutter-Workflow.
* **[Events](events.md):** Die Subscriber-API, die ein Plugin aus seinem `setup()`-Hook heraus registriert.
* **[Extension Points](extension-points.md):** Alle Registries und Basisklassen, in die sich ein Plugin einklinken kann.
