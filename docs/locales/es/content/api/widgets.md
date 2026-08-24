---
title: Referencia de la API de Widgets
description: Referencia completa de la API para los widgets de dashboard y de diseño
  de formularios en starlette-admin.
source_hash: da6469e2d30b13afb7827dac861073c091225333cce9307a41dc3c1ff24913e5
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
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

Referencia completa de atributos y métodos del sistema de widgets, generada a partir de las docstrings. Para una guía orientada a tareas, consulte [Custom Views & Widgets](../user-guide/custom-views.md) y
[Form Layouts](../advanced/form-layout.md).

Los widgets son bloques de construcción componibles y renderizables que se utilizan para construir elementos de interfaz de forma dinámica. Cada clase de widget que se enumera a continuación puede importarse directamente desde `starlette_admin`.

El sistema de widgets cumple dos funciones principales según el contexto:

* **Dashboards y páginas personalizadas:** Se utiliza como el atributo `widget` de [`CustomView`](views.md#starlette_admin.views.CustomView) para construir interfaces independientes y paneles de métricas.
* **Diseños de formularios:** Se utiliza como el atributo `form_layout` de [`BaseModelView`](views.md#starlette_admin.views.BaseModelView) para organizar y agrupar los campos de entrada en los formularios de creación y edición.

---

## Clase base

Todos los widgets heredan de una clase base común que define la interfaz estándar de renderizado y recopilación de recursos.

::: starlette_admin.widgets.BaseWidget

---

## Widgets de contenido

Los widgets de contenido actúan como los nodos hoja de su árbol de interfaz. En lugar de contener otros widgets, muestran datos en tiempo real. Cada widget de contenido acepta un callback asíncrono que se invoca una vez por solicitud, lo que garantiza que los valores renderizados estén siempre actualizados.

::: starlette_admin.widgets.StatWidget
::: starlette_admin.widgets.ChartWidget
::: starlette_admin.widgets.TableWidget
::: starlette_admin.widgets.TextWidget
::: starlette_admin.widgets.HtmlWidget
::: starlette_admin.widgets.DividerWidget

---

## Widgets de diseño

Los widgets de diseño son contenedores que se utilizan para organizar sus `children` (que pueden ser widgets de contenido, campos de formulario u otros widgets de diseño).

**Gestión automática de recursos:** Los widgets de diseño recorren recursivamente su árbol para recopilar los `additional_css_links` y `additional_js_links` de sus hijos. Esto garantiza que los componentes profundamente anidados carguen automáticamente los recursos CSS/JS que necesitan, sin necesidad de cableado manual.

::: starlette_admin.widgets.RowWidget
::: starlette_admin.widgets.CardRowWidget
::: starlette_admin.widgets.ColumnWidget
::: starlette_admin.widgets.GridWidget
::: starlette_admin.widgets.PanelWidget
::: starlette_admin.widgets.FieldsetWidget
::: starlette_admin.widgets.TabsWidget

---

## Dimensionamiento responsivo

Clases de utilidad dedicadas a gestionar comportamientos de cuadrícula responsiva, anchos de columna y breakpoints en diferentes tamaños de pantalla.

::: starlette_admin.widgets.Breakpoints
::: starlette_admin.widgets.Col

---

## Referencias de campos en diseños de formularios

Widgets especializados que se utilizan exclusivamente en el contexto de formularios de modelos para hacer referencia a campos específicos de la base de datos.

::: starlette_admin.widgets.FieldRef

---

## Abreviaturas y normalización

Para mantener su código de diseño limpio y altamente legible, los widgets contenedores aceptan tipos simples de Python en lugar de instanciaciones explícitas de clases de widget. Durante la inicialización (`__post_init__`), los contenedores resuelven automáticamente estos valores abreviados en sus contrapartes de widget correspondientes.

**Abreviaturas admitidas:**

* `str`: Se resuelve en una referencia de campo (`FieldRef`).
* `tuple`: Se resuelve en una fila lado a lado (`RowWidget`).
* `list`: Se resuelve en una pila vertical (`ColumnWidget`).

::: starlette_admin.widgets.WidgetShorthand
::: starlette_admin.widgets.normalize_widget

---

## Funciones auxiliares

Funciones de utilidad para renderizar widgets dentro de plantillas Jinja2 o contextos personalizados.

::: starlette_admin.widgets.render_widget
