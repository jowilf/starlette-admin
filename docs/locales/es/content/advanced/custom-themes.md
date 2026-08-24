---
title: Temas personalizados
description: Anule las variables CSS de Tabler, inyecte hojas de estilo personalizadas
  y modifique la estética general de su panel de control de starlette-admin.
source_hash: 385a0c0718253e051a98f4f310990ad32d3e3babcae40ccddf75e59b931fe937
prompt_hash: 4d252dd7142cde87a0a6edf7cc724709cd7913d618d80eb0687c4c9beddf15fb
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? warning "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/advanced/custom-themes/)
<!-- translation-notice:end -->

# Temas personalizados

Puede cambiar el estilo del panel de administración mediante la configuración de temas, plantillas personalizadas y archivos estáticos. `DefaultTheme` controla el aspecto predeterminado escribiendo atributos data en la etiqueta `<html>` a partir de un objeto `TablerSettings`. Para cambios más profundos, cree una subclase de `BaseTheme` para agrupar sus propias plantillas, recursos estáticos y conjuntos de iconos, o pase sus propios directorios de plantillas y archivos estáticos a `Admin`.

## Aplicar un tema

Use `TablerSettings` para establecer su paleta de colores, radio de borde y modo de color. Páselo a `DefaultTheme` y luego páselo al parámetro `theme` de su instancia de `Admin`.

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

Consulte [examples/08-themes](https://github.com/jowilf/starlette-admin/tree/main/examples/08-themes) para ver una aplicación ejecutable que selecciona un tema aleatorio en cada inicio.

Esta configuración aplica los atributos `data-bs-theme*` directamente al elemento raíz `<html>`:

```html
<html data-bs-theme="dark"
      data-bs-theme-base="slate"
      data-bs-theme-primary="blue"
      data-bs-theme-radius="2">

```

## Referencia de `TablerSettings`

| Atributo | Tipo | Valor predeterminado | Valores válidos |
| --- | --- | --- | --- |
| `mode` | `str` | `"light"` | `"light"`, `"dark"` |
| `base` | `str | None` | `"stone"` | `"slate"`, `"gray"`, `"zinc"`, `"neutral"`, `"stone"`, `"pink"` |
| `primary` | `str | None` | `"blue"` | `"blue"`, `"azure"`, `"indigo"`, `"purple"`, `"pink"`, `"red"`, `"orange"`, `"yellow"`, `"lime"`, `"green"`, `"teal"`, `"cyan"`, `"inverted"` |
| `radius` | `float | None` | `1` | `0`, `0.5`, `1`, `1.5`, `2` |

## Cambiar el estilo de los componentes con un mapa de clases

Las plantillas principales no codifican directamente el estilo de los componentes. Renderizan los atributos de clase mediante el helper de Jinja `cls('role.name')`, que resuelve un rol semántico como `form.save_button` o `list.table` en una cadena de clases CSS. El valor predeterminado de cada rol se encuentra en `starlette_admin.theme.CoreClasses`.

Para cambiar el estilo de un rol, escriba una subclase de `ClassMap`. Cualquier rol que no asigne recurre a `CoreClasses`, por lo que las anulaciones parciales son seguras. Tenga en cuenta que un rol de botón establece todo el atributo de clase del elemento, incluida la variante, el tamaño y el espaciado, por lo que asignar uno reemplaza por completo la apariencia del botón.

Los mapas de clases no requieren un tema completamente personalizado. Para ajustar el tema predeterminado, cree una subclase de `DefaultTheme` y devuelva su mapa desde `get_class_map()`:

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

Lea `CoreClasses.classes` en `starlette_admin/theme.py` para conocer el vocabulario completo de roles. Los roles cubren tres tipos de estilos:

* **Botones:** Un rol por ubicación de botón, que abarca pies de formulario, barras de herramientas de lista, barras de filtros, modales de acciones y edición en línea. El valor que establezca se convierte en todo el atributo de clase del botón.
* **Clases de componentes:** Clases específicas de un framework que otro framework CSS debe reemplazar, como `list.table`, `modal.base` o `filter.chip`.
* **Clases en tiempo de ejecución:** Clases que el JavaScript principal aplica dinámicamente, como `alert.success` o `import.status_badge`.

## Crear y compartir temas personalizados

Puede empaquetar un tema y publicarlo en PyPI, de manera similar a un plug-in. Cree una subclase de `BaseTheme` para construir un paquete de Python reutilizable que reemplace el diseño y el estilo del panel de administración en varios proyectos, o para compartir un sistema visual con otras personas.

### Crear la estructura con Cookiecutter

Comience a partir de la plantilla oficial de cookiecutter. Esta genera un paquete publicable con la estructura de directorios adecuada y los archivos de configuración necesarios.

Instale `cookiecutter` con su gestor de paquetes. Consulte la [guía oficial de instalación](https://cookiecutter.readthedocs.io/en/stable/README.html#installation) para obtener más detalles:

```bash
pip install cookiecutter

```

Luego ejecute la plantilla desde cualquier directorio:

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme

```

La plantilla le solicitará el nombre del tema, el slug del paquete, la versión y algunas otras variables. Cuando finalice, tendrá un paquete autónomo con:

* Un directorio `src/` que contiene la clase del tema, el conjunto de iconos y el mapa de clases.
* Carpetas `templates/`, `static/` y de traducciones preconfiguradas.
* Una suite de pruebas y una aplicación de ejemplo ejecutable.

### Arquitectura de `BaseTheme`

Un tema se encuentra en la raíz de la cadena de renderizado, y cada instancia de `Admin` tiene exactamente un tema activo. Una subclase de `BaseTheme` configura estos elementos:

* **Plantillas:** Plantillas de reemplazo en la carpeta `templates/` del paquete, usando rutas relativas simples como `base.html`, `layout.html` o `list.html`. El tema activo se sitúa encima de los plug-ins en la cadena de carga de Jinja, por lo que puede cambiar el estilo tanto de las plantillas principales como de las de los plug-ins.
* **Recursos estáticos:** Hojas de estilo, scripts e imágenes en el directorio `static/` del paquete.
* **Conjunto de iconos:** Una subclase personalizada de `IconSet` devuelta desde `get_icon_set()`, que asigna claves semánticas como `list.new` o `auth.logout` a clases CSS.
* **Mapa de clases:** Una subclase de `ClassMap` devuelta desde `get_class_map()`, como se describe en [Cambiar el estilo de los componentes con un mapa de clases](#cambiar-el-estilo-de-los-componentes-con-un-mapa-de-clases).
* **Variables globales de plantilla:** Variables globales expuestas a Jinja mediante la anulación de `template_globals()`.

### Paquete de tema de ejemplo

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

### Jerarquía del cargador de plantillas

El motor de plantillas resuelve los archivos en este orden:

1. Su `templates_dir`, que anula todo lo que está debajo.
2. El directorio `templates/` del tema activo, que cambia el estilo de las plantillas principales y de los plug-ins.
3. Los directorios `templates/` de los plug-ins con espacio de nombres.
4. Las plantillas predeterminadas principales de `starlette_admin`.

Para extender una plantilla de un tema desde una anulación de usuario o una subclase de tema, use el prefijo de Jinja `@theme`, por ejemplo `{% extends "@theme/layout.html" %}`.

## Directorio de plantillas personalizadas

Para anular el HTML predeterminado sin construir un tema completo, pase una ruta de directorio a `templates_dir`.

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

Cualquier archivo que coloque en ese directorio oculta la plantilla integrada en la misma ruta relativa, y el resto del árbol integrado sigue renderizándose como antes. Para ver la lista completa de plantillas que se pueden anular, consulte [Plantillas](templates.md).

## Directorio estático personalizado

Para añadir su propio CSS, JavaScript o imágenes sin construir un tema completo, pase una ruta de directorio a `static_dir`.

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

Los archivos de este directorio se sirven junto con los recursos integrados bajo `/admin/static/`. Por ejemplo, un archivo en `my_static/custom.css` queda disponible en `/admin/static/custom.css`.

Haga referencia a la hoja de estilo desde sus plantillas de esta manera:

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">

```

---

## Próximos pasos

* **[Plantillas](templates.md):** Anule una sola página, celda o widget sin bifurcar el árbol de plantillas completo.
* **[Puntos de extensión](extension-points.md):** Explore hooks y puntos de personalización más allá de los temas básicos.
* **[Inicio rápido](../getting-started/quickstart.md):** Construya una interfaz de administración funcional desde cero.
