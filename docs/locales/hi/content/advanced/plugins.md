---
title: प्लगइन
description: starlette-admin के लिए reusable admin features और extensions को drop-in
  प्लगइन के रूप में package करें।
source_hash: c9ecd9e51a7426d12b628b06c9c664579e5f269d456e93e9d985c4d2853ac758
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "पर्यवेक्षित मशीन अनुवाद"

    यह सामग्री मानव-निर्मित शब्दावलियों और शैली गाइडों के मार्गदर्शन में
    मशीन जनरेशन द्वारा अनुवादित की गई है। चूँकि इस पाठ की समीक्षा
    लाइन-दर-लाइन मैन्युअल रूप से नहीं की गई है, इसलिए कभी-कभी त्रुटियाँ या
    अनाड़ी वाक्य-रचना हो सकती है।

    किसी भी विसंगति की स्थिति में, मूल अंग्रेज़ी संस्करण ही प्रामाणिक स्रोत
    है।

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/advanced/plugins/)
<!-- translation-notice:end -->

# प्लगइन {#plugins}

प्लगइन एक Python package है जो एक single constructor argument के ज़रिए `starlette-admin` को extend करता है। एक प्लगइन fields, templates, static assets, model converters, filters, import/export formats, storage backends, event subscribers, views, routes, middlewares, theme assets, और translation catalogs — इनमें से किसी भी combination को bundle कर सकता है।

## प्लगइन का उपयोग करना {#using-a-plugin}

अपना `Admin` instance बनाते समय प्लगइन को `plugins` argument के ज़रिए pass करें:

```python
from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[GeospatialPlugin(default_zoom=13)])
```

Plugin constructor options लेता है, और list सीधे `Admin` तक चली जाती है। Setup या register करने की कोई और ज़रूरत नहीं। Options constructor से Python backend, Jinja templates, और frontend JavaScript तक flow होते हैं।

## प्लगइन बनाना {#building-a-plugin}

प्लगइन लिखने के लिए official cookiecutter template से शुरुआत करें। यह सही directory structure और configuration वाला publishable package generate करता है।

### Prerequisites

`cookiecutter` को अपने package manager से install करें। विवरण के लिए [official installation guide](https://cookiecutter.readthedocs.io/en/stable/README.html#installation) देखें:

```bash
pip install cookiecutter
```

### Scaffolding

Cookiecutter template को किसी भी location से run करें:

```bash
cookiecutter gh:jowilf/starlette-admin --directory plugins/cookiecutter-starlette-admin-plugin
```

Template आपसे plugin का नाम, package slug, version, और कुछ अन्य variables पूछता है। यह पूरा होने पर आपके पास एक self-contained package होता है, जिसमें शामिल हैं:

* आपकी plugin class और fields रखने वाली एक `src/` directory।
* सही ढंग से namespaced `templates/`, `static/`, और `translations/` folders।
* एक complete test suite।
* Run करने योग्य एक example application।

## Plugin API {#the-plugin-api}

हर प्लगइन के केंद्र में `BasePlugin` (`starlette_admin.plugins.BasePlugin`) का एक subclass होता है, जो `Admin` के initialize होते समय आपकी features register करने के hooks देता है।

```python
from starlette_admin.plugins import BasePlugin


class MyPlugin(BasePlugin):
    name = "my-plugin"
```

`name` attribute एक unique kebab-case identifier है जो आपके templates और static assets के namespace का भी काम करता है। आपका plugin ship की गई हर template और static file `plugins/<name>/` के अंतर्गत होनी चाहिए।

### Asset folders

एक plugin अपने package की root पर ठीक तीन folders रख सकता है। Register करने की कुछ ज़रूरत नहीं, क्योंकि admin उन्हें convention से ढूँढ लेता है:

* `templates/`: Jinja templates, जो `templates/plugins/<name>/` के अंतर्गत होने चाहिए।
* `static/`: CSS और JS files जैसे static assets, जो `static/plugins/<name>/` के अंतर्गत होने चाहिए।
* `translations/`: Babel translation catalogs।

`plugins/<name>/` namespace के भीतर रहने से आपके assets core files या अन्य plugins से टकराते नहीं, साथ ही वे user की अपनी `templates_dir` या `static_dir` के ज़रिए override करने योग्य भी बने रहते हैं।

### Declarative hooks

Assets inject करने, views register करने, या routes mount करने के लिए declarative hooks को ओवरराइड करें।

* `css_links(self, request: Request) -> Sequence[str]`: हर admin page layout में stylesheets जोड़ता है।
* `js_links(self, request: Request) -> Sequence[str]`: हर admin page layout में scripts जोड़ता है।
* `views(self) -> Sequence[BaseView]`: Admin sidebar में register होने वाले views return करता है। उन्हें group करने के लिए एक `DropDown` return करें।
* `routes(self) -> Sequence[Route | Mount]`: `/plugins/<name>/` के अंतर्गत mounted headless endpoints return करता है, जो webhooks और proxy endpoints के लिए handy है।
* `middlewares(self) -> Sequence[Middleware]`: Starlette middlewares जोड़ता है।
* `template_globals(self) -> dict[str, Any]`: Jinja globals expose करता है, जो `<name>_` prefixed होते हैं ताकि टकराव न हो।
* `template_filters(self) -> dict[str, Callable]`: उसी तरह `<name>_` prefixed Jinja filters expose करता है।

### Setup hook {#the-setup-hook}

`setup(self, admin: BaseAdmin) -> None` आपके plugin को core registries के साथ integrate करता है। इसका उपयोग model converters, filters, import और export formats, storage backends, तथा event subscribers register करने के लिए करें। यह declarative hooks apply होने के बाद run होता है।

```python
def setup(self, admin: "BaseAdmin") -> None:
    admin.events.subscribe(MyEventSubscriber(self.config))
```

### Lifecycle hook {#the-lifecycle-hook}

`on_mount(self, admin: BaseAdmin) -> None` ठीक एक बार run होता है, Starlette sub-application के build और mount होने के बाद। Built application `admin.app` के रूप में available होता है।

## Templates और overrides {#templates-and-overrides}

Plugin templates loader chain में अपने-आप शामिल हो जाते हैं। User कोई template override करने के लिए matching path पर अपनी `templates_dir` के अंदर फ़ाइल रखता है, जिसकी हमेशा priority रहती है। उदाहरण के लिए, `plugins/geospatial/fields/form/point.html` को override करने के लिए वह `templates_dir/plugins/geospatial/fields/form/point.html` बनाता है।

User override मूल template को safely extend कर सके, इसके लिए हर plugin को एक `@<name>` prefix mapping मिलती है, जो `@core` prefix की तरह काम करती है। Override `{% extends "@geospatial/fields/form/point.html" %}` से शुरू होता है और base plugin template को recursively include किए बिना उसे extend करता है।

## Frontend JavaScript integration

Custom fields ship करने वाला plugin अपनी frontend scripts को field initializer contract के अनुसार package करे। इससे वे full page loads और dynamically insert किए गए fragments दोनों में काम करती रहती हैं।

* **Locally target करें:** Query हमेशा दिए गए `container` element के अंदर करें, global `document` पर कभी नहीं।
* **Idempotent बनें:** Core initializer को DOM ready पर चलाता है और जब भी inline rows या fragments insert करता है, दोबारा चलाता है।
* **Data attributes का उपयोग करें:** Field element पर render किए गए `data-*` attributes से configuration पढ़ें।

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

## Setup hook के ज़रिए extension points {#extension-points-via-the-setup-hook}

Plugins अपना अलग extension path बनाने के बजाय existing public registries का उपयोग करते हैं।

* **Converters**: ORM column types को अपनी field classes में map करने के लिए, जिस contrib backend को target कर रहे हैं उसका `register_converter` call करें। Field को खुद एक ordinary `StringField` subclass के रूप में define करें, जो geometries को WKT text के रूप में store और display करता है:

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

* **Filters**: किसी field type से filter classes attach करने के लिए `register_filters` call करें।

  ```python
  from starlette_admin.contrib.sqla.filters import register_filters

  register_filters(MyGeoField, WithinBoundingBoxFilter)
  ```

* **Storage**: Azure या GCS जैसा नया backend expose करने के लिए `register_storage` call करें।

  ```python
  from starlette_admin.storage import register_storage

  register_storage(AzureBlobStorage())
  ```

* **Importers और Exporters**: `register_import_format` और `register_export_format` का उपयोग करें।

  ```python
  from starlette_admin.export import register_export_format

  register_export_format("pdf", PDFExporter())
  ```

एक plugin कई ORM backends को support कर सकता है, इसलिए उन्हें `setup()` के अंदर conditionally import करें। इससे plugin तब भी load होता रहता है जब user ने उनमें से केवल एक ही install किया हो:

```python
def setup(self, admin: "BaseAdmin") -> None:
    try:
        from starlette_admin_geospatial.contrib.sqla import register_sqla_converters

        register_sqla_converters()
    except ImportError:
        pass  # geoalchemy2 or sqlalchemy not installed
```

---

## आगे क्या {#whats-next}

* **[कस्टम थीम](custom-themes.md):** उसी cookiecutter workflow का उपयोग करके एक पूरा visual system package और share करें।
* **[इवेंट](events.md):** Subscriber API जिसे plugin अपने `setup()` hook से register करता है।
* **[एक्सटेंशन पॉइंट्स](extension-points.md):** हर registry और base class जिसमें plugin hook कर सकता है।
