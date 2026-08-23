---
title: Referencia de la API de widgets
description: Referencia completa de la API de los widgets de panel de control y diseño
  de formularios en starlette-admin.
source_hash: da6469e2d30b13afb7827dac861073c091225333cce9307a41dc3c1ff24913e5
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/api/widgets/)
<!-- translation-notice:end -->

# Widgets

Referencia completa de atributos y métodos del sistema de widgets, generada a partir de las docstrings. Para un recorrido orientado a tareas, consulte [Vistas personalizadas y widgets](../user-guide/custom-views.md) y [Diseños de formularios](../advanced/form-layout.md).

Los widgets son bloques de construcción componibles y renderizables que se utilizan para construir elementos de la interfaz de forma dinámica. Cada clase de widget que se enumera a continuación puede importarse directamente desde `starlette_admin`.

El sistema de widgets cumple dos funciones principales según el contexto:

* **Paneles de control y páginas personalizadas:** se usa como atributo `widget` de [`CustomView`](views.md#starlette_admin.views.CustomView) para construir interfaces independientes y paneles de métricas.
* **Diseños de formularios:** se usa como atributo `form_layout` de [`BaseModelView`](views.md#starlette_admin.views.BaseModelView) para organizar y agrupar los campos de entrada en los formularios de creación y edición.

---

## Clase base

Todos los widgets heredan de una clase base común que define la interfaz estándar de renderizado y recopilación de recursos.

::: starlette_admin.widgets.BaseWidget

---

## Widgets de contenido

Los widgets de contenido actúan como nodos hoja del árbol de la interfaz. En lugar de contener otros widgets, muestran datos en vivo. Cada widget de contenido acepta una callback asíncrona que se invoca una vez por solicitud, lo que garantiza que los valores renderizados estén siempre actualizados.

::: starlette_admin.widgets.StatWidget
::: starlette_admin.widgets.ChartWidget
::: starlette_admin.widgets.TableWidget
::: starlette_admin.widgets.TextWidget
::: starlette_admin.widgets.HtmlWidget
::: starlette_admin.widgets.DividerWidget

---

## Widgets de diseño

Los widgets de diseño son contenedores que se utilizan para disponer sus `children` (que pueden ser widgets de contenido, campos de formulario u otros widgets de diseño).

**Gestión automática de recursos:** los widgets de diseño recorren su árbol de forma recursiva para recopilar `additional_css_links` y `additional_js_links` de sus hijos. Esto garantiza que los componentes profundamente anidados carguen automáticamente sus recursos CSS/JS necesarios sin necesidad de cableado manual.

::: starlette_admin.widgets.RowWidget
::: starlette_admin.widgets.CardRowWidget
::: starlette_admin.widgets.ColumnWidget
::: starlette_admin.widgets.GridWidget
::: starlette_admin.widgets.PanelWidget
::: starlette_admin.widgets.FieldsetWidget
::: starlette_admin.widgets.TabsWidget

---

## Dimensionamiento responsivo

Clases de utilidad dedicadas a gestionar comportamientos de cuadrícula responsivos, anchos de columna y breakpoints en diferentes tamaños de pantalla.

::: starlette_admin.widgets.Breakpoints
::: starlette_admin.widgets.Col

---

## Referencias a campos de formulario

Widgets especializados que se usan exclusivamente en el contexto de formularios de modelos para hacer referencia a campos específicos de la base de datos.

::: starlette_admin.widgets.FieldRef

---

## Formas abreviadas y normalización

Para mantener su código de diseño limpio y muy legible, los widgets contenedores aceptan tipos de Python sencillos en lugar de instanciaciones explícitas de clases de widget. Durante la inicialización (`__post_init__`), los contenedores resuelven automáticamente estos valores abreviados en sus contrapartes de widget correspondientes.

**Formas abreviadas admitidas:**

* `str`: se resuelve en una referencia a un campo (`FieldRef`).
* `tuple`: se resuelve en una fila lado a lado (`RowWidget`).
* `list`: se resuelve en una pila vertical (`ColumnWidget`).

::: starlette_admin.widgets.WidgetShorthand
::: starlette_admin.widgets.normalize_widget

---

## Funciones auxiliares

Funciones de utilidad para renderizar widgets dentro de plantillas de Jinja2 o contextos personalizados.

::: starlette_admin.widgets.render_widget
