---
title: Plugins
description: Empaquete funciones y extensiones de administración reutilizables como
  plugins listos para usar en starlette-admin.
source_hash: c9ecd9e51a7426d12b628b06c9c664579e5f269d456e93e9d985c4d2853ac758
prompt_hash: 4d252dd7142cde87a0a6edf7cc724709cd7913d618d80eb0687c4c9beddf15fb
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? info "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/advanced/plugins/)
<!-- translation-notice:end -->

# Plugins

Un plugin es un paquete de Python que extiende `starlette-admin` mediante un único argumento de constructor. Un plugin puede incluir cualquier combinación de campos, plantillas, recursos estáticos, convertidores de modelos, filtros, formatos de importación/exportación, backends de almacenamiento, suscriptores de eventos, vistas, rutas, middleware, recursos de tema y catálogos de traducción.

## Usar un plugin

Pase los plugins mediante el argumento `plugins` cuando construya su instancia de `Admin`:

```python
from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[GeospatialPlugin(default_zoom=13)])
```

El constructor del plugin recibe las opciones, y la lista se pasa directamente a `Admin`. No hay nada más que configurar ni registrar. Las opciones fluyen desde el constructor hasta el backend de Python, las plantillas de Jinja y el JavaScript del frontend.

## Crear un plugin

Para escribir un plugin, parta de la plantilla oficial de cookiecutter. Esta genera un paquete publicable con la estructura de directorios y la configuración adecuadas.

### Requisitos previos

Instale `cookiecutter` con su gestor de paquetes. Consulte la [guía oficial de instalación](https://cookiecutter.readthedocs.io/en/stable/README.html#installation) para más detalles:

```bash
pip install cookiecutter
```

### Generar el proyecto

Ejecute la plantilla de cookiecutter desde cualquier ubicación:

```bash
cookiecutter gh:jowilf/starlette-admin --directory plugins/cookiecutter-starlette-admin-plugin
```

La plantilla le pedirá el nombre del plugin, el slug del paquete, la versión y algunas otras variables. Cuando termine, tendrá un paquete autocontenido con:

* Un directorio `src/` que contiene la clase de su plugin y los campos.
* Carpetas `templates/`, `static/` y `translations/` correctamente organizadas por espacio de nombres.
* Una suite de pruebas completa.
* Una aplicación de ejemplo ejecutable.

## La API de plugins

En el núcleo de cada plugin hay una subclase de `BasePlugin` (`starlette_admin.plugins.BasePlugin`), que le proporciona hooks para registrar sus funcionalidades mientras `Admin` se inicializa.

```python
from starlette_admin.plugins import BasePlugin


class MyPlugin(BasePlugin):
    name = "my-plugin"
```

El atributo `name` es un identificador único en kebab-case que sirve además como espacio de nombres para sus plantillas y recursos estáticos. Cada plantilla y archivo estático que incluya su plugin debe estar bajo `plugins/<name>/`.

### Carpetas de recursos

Un plugin puede llevar exactamente tres carpetas en la raíz de su paquete. No hay nada que registrar, porque la administración las encuentra por convención:

* `templates/`: plantillas de Jinja, que deben situarse bajo `templates/plugins/<name>/`.
* `static/`: recursos estáticos como archivos CSS y JS, que deben situarse bajo `static/plugins/<name>/`.
* `translations/`: catálogos de traducción de Babel.

Mantenerse dentro del espacio de nombres `plugins/<name>/` evita que sus recursos entren en conflicto con los archivos del núcleo o con otros plugins, a la vez que permite sobrescribirlos mediante el propio `templates_dir` o `static_dir` del usuario.

### Hooks declarativos

Sobrescriba los hooks declarativos para inyectar recursos, registrar vistas o montar rutas.

* `css_links(self, request: Request) -> Sequence[str]`: añade hojas de estilo al diseño de todas las páginas de administración.
* `js_links(self, request: Request) -> Sequence[str]`: añade scripts al diseño de todas las páginas de administración.
* `views(self) -> Sequence[BaseView]`: devuelve las vistas que se registran en la barra lateral de administración. Devuelva un `DropDown` para agruparlas.
* `routes(self) -> Sequence[Route | Mount]`: devuelve endpoints sin interfaz montados bajo `/plugins/<name>/`, lo cual resulta útil para webhooks y endpoints de proxy.
* `middlewares(self) -> Sequence[Middleware]`: añade middleware de Starlette.
* `template_globals(self) -> dict[str, Any]`: expone variables globales de Jinja, prefijadas con `<name>_` para que no puedan entrar en conflicto.
* `template_filters(self) -> dict[str, Callable]`: expone filtros de Jinja, prefijados con `<name>_` de la misma manera.

### El hook de configuración

`setup(self, admin: BaseAdmin) -> None` integra su plugin con los registros del núcleo. Úselo para registrar convertidores de modelos, filtros, formatos de importación y exportación, backends de almacenamiento y suscriptores de eventos. Se ejecuta después de aplicar los hooks declarativos.

```python
def setup(self, admin: "BaseAdmin") -> None:
    admin.events.subscribe(MyEventSubscriber(self.config))
```

### El hook del ciclo de vida

`on_mount(self, admin: BaseAdmin) -> None` se ejecuta exactamente una vez, después de que la subaplicación de Starlette se haya construido y montado. La aplicación construida está disponible como `admin.app`.

## Plantillas y sobrescrituras

Las plantillas de los plugins se incorporan automáticamente a la cadena de loaders. Un usuario puede sobrescribir una colocando un archivo en la ruta correspondiente dentro de su propio `templates_dir`, que siempre tiene prioridad. Para sobrescribir `plugins/geospatial/fields/form/point.html`, por ejemplo, debe crear `templates_dir/plugins/geospatial/fields/form/point.html`.

De modo que una sobrescritura del usuario pueda extender la plantilla original de forma segura, cada plugin dispone de un mapeo con el prefijo `@<name>` que funciona igual que el prefijo `@core`. La sobrescritura comienza con `{% extends "@geospatial/fields/form/point.html" %}` y extiende la plantilla base del plugin sin incluirse a sí misma recursivamente.

## Integración con el JavaScript del frontend

Un plugin que incluya campos personalizados debe empaquetar sus scripts de frontend conforme al contrato de inicializadores de campo. Esto garantiza que funcionen tanto en cargas de página completas como en fragmentos insertados dinámicamente.

* **Apunte localmente:** realice las consultas dentro del elemento `container` que se le proporciona, nunca sobre el `document` global.
* **Sea idempotente:** el núcleo ejecuta el inicializador cuando el DOM está listo y de nuevo cada vez que inserta filas o fragmentos en línea.
* **Use atributos data:** lea la configuración desde los atributos `data-*` renderizados en el elemento del campo.

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

## Puntos de extensión mediante el hook de configuración

Los plugins utilizan los registros públicos existentes en lugar de una vía de extensión propia independiente.

* **Convertidores**: llame a `register_converter`, desde el backend contrib al que apunte, para asignar tipos de columnas ORM a sus clases de campo. Defina el propio campo como una subclase ordinaria de `StringField`, que almacena y muestra las geometrías como texto WKT:

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

* **Filtros**: llame a `register_filters` para asociar clases de filtro a un tipo de campo.

  ```python
  from starlette_admin.contrib.sqla.filters import register_filters

  register_filters(MyGeoField, WithinBoundingBoxFilter)
  ```

* **Almacenamiento**: llame a `register_storage` para exponer un nuevo backend, como Azure o GCS.

  ```python
  from starlette_admin.storage import register_storage

  register_storage(AzureBlobStorage())
  ```

* **Importadores y exportadores**: use `register_import_format` y `register_export_format`.

  ```python
  from starlette_admin.export import register_export_format

  register_export_format("pdf", PDFExporter())
  ```

Un plugin puede admitir varios backends ORM, así que impórtelos condicionalmente dentro de `setup()`. De esta manera, el plugin sigue cargándose aunque el usuario solo haya instalado uno de ellos:

```python
def setup(self, admin: "BaseAdmin") -> None:
    try:
        from starlette_admin_geospatial.contrib.sqla import register_sqla_converters

        register_sqla_converters()
    except ImportError:
        pass  # geoalchemy2 or sqlalchemy not installed
```

---

## ¿Qué sigue?

* **[Temas personalizados](custom-themes.md):** empaquete y comparta un sistema visual completo, usando el mismo flujo de trabajo con cookiecutter.
* **[Eventos](events.md):** la API de suscriptores que un plugin registra desde su hook `setup()`.
* **[Puntos de extensión](extension-points.md):** todos los registros y clases base en los que un plugin puede integrarse.
