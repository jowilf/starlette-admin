---
title: Diseños de formularios
description: Diseñe diseños de formulario complejos y adaptables usando TabsWidget,
  FieldsetWidget y columnas de cuadrícula en starlette-admin.
source_hash: ab3f17593165b8c7e689af55be35a5b79b082aca4f984f7eb610c0b292763ea5
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/advanced/form-layout/)
<!-- translation-notice:end -->

# Diseños de formularios

De forma predeterminada, los formularios de creación y edición muestran todo lo que hay en `fields` como una lista plana. El atributo `form_layout` le permite organizar esos campos de entrada con los mismos widgets componibles que utiliza en los [dashboards](../user-guide/custom-views.md): filas lado a lado, paneles con título o plegables, pestañas, contenido estático y sus propios widgets personalizados.

## Uso básico

El diseño más simple no necesita ningún widget. Haga referencia a un campo por su nombre como cadena para mantenerlo en su propia línea, y agrupe varios nombres en una tupla para colocarlos lado a lado en una misma fila.

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        ("first_name", "last_name"),
        "email",
        ("salary", "notes"),
    ]
```

En el diseño anterior:

* `("first_name", "last_name")` crea una fila dividida equitativamente entre las dos entradas.
* `"email"` se muestra en su propia línea, justo debajo.
* `("salary", "notes")` crea una segunda fila con varias columnas.

Puede colocar cualquier cantidad de campos en una fila y combinar libremente filas de una sola columna con filas de varias columnas.

Los widgets contenedores expanden esta notación abreviada por sí mismos: `RowWidget`, `ColumnWidget`, `GridWidget`, `PanelWidget`, `FieldsetWidget`, `TabsWidget` y `Col` convierten tuplas en filas y listas en columnas apiladas al construirse. Por lo tanto, la notación abreviada también funciona dentro de atributos `children` anidados y dentro de un dashboard [`CustomView.widget`](../user-guide/custom-views.md).

## Agrupación de campos

### Paneles con título

Para dar un título a un grupo de campos, o hacerlo plegable, envuélvalo en un `PanelWidget`. Este widget acepta la misma notación abreviada de cadenas y tuplas que el nivel superior.

```python
from starlette_admin import PanelWidget


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        PanelWidget(
            title="Identity",
            children=[("first_name", "last_name"), "email"],
        ),
        PanelWidget(
            title="Compensation",
            children=["salary", "notes"],
            collapsible=True,
            collapsed=True,
        ),
    ]
```

`PanelWidget` acepta estos atributos:

| Atributo | Descripción |
| --- | --- |
| `title` | El encabezado mostrado en la tarjeta del panel. |
| `children` | Los widgets que se muestran dentro del panel, en orden. Acepta la notación abreviada descrita arriba o widgets anidados. Agregue un hijo `TextWidget(card=False)` para colocar texto explicativo debajo del título. |
| `collapsible` | Permite a los usuarios expandir y contraer el panel. |
| `collapsed` | Inicia el panel contraído. Se aplica solo cuando `collapsible=True`. |

Para un grupo que no necesita título, utilice `ColumnWidget` en su lugar. Apila sus hijos verticalmente sin envolverlos en una tarjeta con estilo.

### Fieldsets

`FieldsetWidget` agrupa campos de manera muy similar a `PanelWidget`, pero muestra un `<fieldset>` y `<legend>` HTML nativos en lugar de una tarjeta con estilo. Úselo cuando desee una agrupación más simple con bordes.

```python
from starlette_admin import FieldsetWidget

form_layout = [
    FieldsetWidget(
        legend="Identity",
        children=[("first_name", "last_name"), "email"],
    ),
    FieldsetWidget(
        legend="Compensation",
        children=["salary", "notes"],
        disabled=True,
    ),
]
```

El atributo `legend` establece el texto del elemento `<legend>`. `disabled=True` coloca el atributo HTML `disabled` en el contenedor, lo que deshabilita todos los controles de formulario anidados. `FieldsetWidget` admite la misma notación abreviada de `children` que `PanelWidget`, pero no las opciones específicas de panel como `collapsible` e `icon`.

## Anchos de columna explícitos

La notación abreviada con tuplas siempre divide una fila en partes iguales. Para tener un control más preciso sobre los anchos de columna, construya la fila explícitamente con `RowWidget`, `Col` y `FieldRef`:

```python
from starlette_admin import Breakpoints, Col, FieldRef, RowWidget

form_layout = [
    RowWidget(
        children=[
            Col(FieldRef("first_name"), Breakpoints(default=12, md=4)),
            Col(FieldRef("last_name"), Breakpoints(default=12, md=8)),
        ]
    ),
]
```

## Ocultar etiquetas de campos

Construir un `FieldRef` explícitamente le da acceso al parámetro `show_label`, que elimina el elemento `<label>` cuando el diseño circundante ya hace evidente el propósito del campo.

```python
from starlette_admin import FieldsetWidget, FieldRef

form_layout = [
    FieldsetWidget(legend="Email", children=[FieldRef("email", show_label=False)]),
]
```

`show_label` tiene el valor predeterminado `True`. Las notaciones abreviadas de cadena y tupla siempre muestran las etiquetas, porque no aceptan argumentos de palabra clave.

## Grupos de entrada

Los parámetros `prepend` y `append` adjuntan un [input group](https://docs.tabler.io/ui/forms/form-elements#input-group) a cualquiera de los lados de un campo de entrada. Cada uno acepta texto plano o HTML sin procesar, como un icono de Font Awesome.

```python
from starlette_admin import FieldRef

form_layout = [
    FieldRef("email", prepend="@"),
    FieldRef("phone", append='<i class="fa fa-phone"></i>'),
    FieldRef("salary", prepend="$", append="USD"),
]
```

Los addons funcionan en campos cuya plantilla de formulario muestra un elemento `<input>` nativo: `StringField`, `EmailField`, `URLField`, `PhoneField`, `PasswordField`, `ColorField`, `SlugField`, los campos numéricos (`IntegerField`, `DecimalField`, `FloatField`) y los campos de fecha y hora. Otros tipos, como `EnumField`, `TextAreaField` y `BooleanField`, los ignoran silenciosamente.

!!! warning
    Los valores de los addons se muestran sin escapar para que el HTML, como el marcado de iconos, funcione correctamente. Pase únicamente contenido confiable escrito por usted mismo, nunca datos proporcionados por el usuario.

## Pestañas

Para dividir secciones en una interfaz con pestañas, use `TabsWidget`. Recibe una lista de pares `(label, widgets)`.

```python
from starlette_admin import TabsWidget

form_layout = [
    TabsWidget(
        tabs=[
            ("Identity", [("first_name", "last_name"), "email"]),
            ("Compensation", ["salary", "notes"]),
        ]
    ),
]
```

## Contenido estático

Use `HtmlWidget` y `TextWidget` para mostrar contenido arbitrario en cualquier parte del diseño: instrucciones, advertencias o separadores.

```python
from starlette_admin import HtmlWidget, PanelWidget

form_layout = [
    HtmlWidget(html="<p class='text-warning'>Changes here are audited.</p>"),
    PanelWidget(title="Compensation", children=["salary", "notes"]),
]
```

## Widgets personalizados

Dado que `form_layout` comparte la jerarquía de `BaseWidget` con los dashboards, puede crear una subclase de `BaseWidget` para construir sus propios elementos. Esa es la vía de escape para todo lo que los widgets integrados no cubren, como vistas previas de solo lectura, gráficos incrustados o macros personalizadas.

Consulte [Custom Views & Widgets](../user-guide/custom-views.md) para conocer el patrón general, y la [Widgets API reference](../api/widgets.md) para ver los métodos que una subclase puede sobrescribir. Los widgets personalizados en `form_layout` siempre se muestran, independientemente de lo que indiquen las reglas de visibilidad de los campos.

## Control de acceso y visibilidad

`form_layout` respeta sus reglas de acceso a nivel de campo. Cada `FieldRef` pasa por la comprobación habitual de `can_access_field`, y `exclude_from_create`, `exclude_from_edit` y los permisos basados en roles siguen vigentes.

* **Expansión de filas:** Cuando un campo de una fila de varias columnas está oculto para una solicitud, los campos visibles restantes se expanden para llenar el espacio.
* **Contenedores vacíos:** Cuando todos los campos de un contenedor (fila, panel, fieldset, columna, grid o pestaña) están ocultos, el contenedor se omite, de modo que nunca obtendrá un cascarón vacío.
* **Renderizado estático:** Los componentes estáticos como `HtmlWidget`, `TextWidget` y las subclases personalizadas de `BaseWidget` siempre se muestran, porque no dependen de los campos del formulario.

## Manejo de campos omitidos

Un campo declarado en `fields` pero excluido de `form_layout` se agrega al final del formulario en orden de declaración, de modo que ningún campo se pierde silenciosamente.

Hacer referencia al mismo campo dos veces, o hacer referencia a un nombre que no está en `fields`, genera un `ValueError` cuando se construye la vista.

---

## Qué sigue

* **[Custom Views & Widgets](../user-guide/custom-views.md):** La jerarquía de widgets sobre la que se construye `form_layout`, y cómo escribir su propio widget.
* **[Templates](templates.md):** Sobrescriba `_form_group.html` para cambiar el marcado que muestra un grupo del diseño.
* **[Fields](../user-guide/fields.md):** Los tipos de campos y las reglas de visibilidad que organiza un diseño.
