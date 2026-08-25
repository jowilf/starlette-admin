---
title: Campos personalizados
description: Aprenda a crear tipos de campos personalizados en starlette-admin para
  manejar tipos de datos especializados y widgets de interfaz personalizados.
source_hash: 5daa493733490d2421b0bacf11a0669eaad36b82cccc3dd0be3f7709e5681eb2
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/advanced/custom-fields/)
<!-- translation-notice:end -->

# Campos personalizados

Los campos integrados cubren la mayoría de las columnas que encontrará, pero cuando ninguno de ellos se ajusta a sus necesidades, puede crear el suyo propio heredando de [`BaseField`](../api/fields.md#starlette_admin.fields.BaseField). Un campo son tres métodos que mueven los datos entre su modelo y el navegador, más un conjunto de rutas de plantilla que lo renderizan. Puede heredar directamente de `BaseField`, o extender el campo integrado más cercano a lo que necesita (como `StringField` o `EnumField`) y sobrescribir únicamente las partes que difieren.

## Ejemplo mínimo

```python
from dataclasses import dataclass
from dataclasses import field as dc_field

from starlette_admin.fields import EnumField


@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    badge_class_by_value: dict[str, str] = dc_field(
        default_factory=lambda: {
            "Online": "badge bg-success-lt",
            "Busy": "badge bg-danger-lt",
            "Offline": "badge",
        }
    )
```

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

Apunte su instancia de `Admin` al directorio de plantillas y luego use el campo en su vista:

```python
from starlette_admin.contrib.sqla import Admin, ModelView

admin = Admin(engine, title="My Admin", templates_dir="templates/")
```

```python
class EmployeeView(ModelView):
    fields = [
        "id",
        "name",
        StatusBadgeField("status", choices=["Online", "Busy", "Offline"]),
    ]
```

Como `StatusBadgeField` hereda de `EnumField` en lugar de hacerlo de `BaseField`, obtiene `choices`, la validación del formulario contra esas opciones y la plantilla predeterminada `fields/form/enum.html` para los formularios de creación y edición. Nada de eso necesita cambiar, por lo que la clase solo sobrescribe los atributos de renderizado para las vistas de lista y detalle.

El resto de esta página cubre qué sobrescribir cuando un campo requiere algo más que un simple cambio de plantilla. Para ver el código completo funcional, junto con un segundo campo (`AvatarNameField`) que sí sobrescribe los métodos de datos, consulte [`examples/advanced/05-custom-fields`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/05-custom-fields).

## Los tres métodos de datos

| Método | Cuándo se llama | Firma |
| --- | --- | --- |
| `parse_form_data` | Se envía un formulario de creación/edición | `async def parse_form_data(self, request: Request, form_data: FormData) -> Any` |
| `parse_obj` | Se lee un valor de una instancia del modelo para mostrarlo | `async def parse_obj(self, request: Request, obj: Any) -> Any` |
| `serialize_value` | Se formatea un valor para el frontend (lista, detalle, API, exportación) | `async def serialize_value(self, request: Request, value: Any) -> Any` |

`StatusBadgeField` no sobrescribe ninguno de ellos, porque `EnumField` ya valida el valor enviado contra `choices` y lee la cadena original de `obj.status`. La insignia es solo presentación sobre esa cadena. Sobrescriba estos tres métodos cuando el valor deba calcularse o transformarse, no simplemente volver a renderizarse.

!!! tip "Hooks o herencia"
    Para un cambio puntual en un solo campo, rara vez necesita una subclase. En su lugar, pase los [hooks `getter`, `formatter` y `parser`](../user-guide/fields.md#computing-formatting-and-parsing-values) como argumentos del constructor, para gestionar la lectura, el formato de visualización y el análisis de la entrada.
    **Cuándo usar una subclase:** solo cuando necesite la misma lógica en más de una vista, o cuando necesite cambiar las plantillas.

`parse_form_data` recibe el `FormData` original (de `starlette.datastructures`) de la solicitud y devuelve los datos que `view.create()` o `view.edit()` deben recibir para este campo. La implementación predeterminada lee `form_data.get(self.id)` y lo devuelve sin cambios. La mayoría de los campos solo necesitan añadir una conversión de tipo:

```python
async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
    raw = form_data.get(self.id)
    return raw in ("on", "true", "yes")
```

`parse_obj` recibe la instancia del modelo y devuelve el valor que se debe mostrar. La implementación predeterminada devuelve `getattr(obj, self.name, None)`. Sobrescríbalo para campos que no se corresponden con un único atributo del modelo, como uno que combina dos columnas. Por ejemplo, `AvatarNameField` combina una cadena `name` con el avatar cargado de la fila:

```python
async def parse_obj(self, request: Request, obj: Any) -> Any:
    name = await super().parse_obj(request, obj)
    avatar_key = obj.avatar.get("key") if obj.avatar is not None else None
    return {"name": name, "avatar_key": avatar_key, "initials": self._initials(name)}
```

`serialize_value` recibe lo que produjo `parse_obj` (o la capa ORM) y lo formatea para la solicitud actual. Se llama por separado para la página de lista, la página de detalle, la API JSON y las exportaciones de datos, por lo que puede ramificar según `request.state.action` cuando la forma del valor debe diferir según el contexto. `AvatarNameField` solo necesita la imagen del avatar en la página de lista y recurre a texto plano en todos los demás casos:

```python
async def serialize_value(self, request: Request, value: Any) -> Any:
    name, avatar_key = value.get("name"), value.get("avatar_key")
    if request.state.action != RequestAction.LIST:
        return name
    if avatar_key is not None:
        value["avatar_url"] = await self.avatars_storage.url(request, avatar_key)
    return value
```

!!! warning
    Lo que `serialize_value` devuelva para `RequestAction.LIST` y `RequestAction.RELATION_LOOKUP` va directamente a una respuesta JSON, por lo que debe ser serializable a JSON.

## Rutas de plantilla

Cada campo incluye los atributos de plantilla siguientes. Cada uno es una ruta que el loader de Jinja2 del admin resuelve: primero comprueba su `templates_dir`, si ha definido uno, y luego recurre al directorio integrado `starlette_admin/templates/`. Consulte [Templates](templates.md) para conocer los detalles.

| Atributo | Predeterminado | Renderizado para |
| --- | --- | --- |
| `list_template` | `"fields/list/text.html"` | El valor de cada columna en cada fila de la página de lista |
| `detail_template` | `"fields/detail/text.html"` | La página de detalle de solo lectura |
| `form_template` | `"fields/form/input.html"` | El campo de entrada del formulario de creación/edición |
| `null_template` | `"fields/detail/_null.html"` | Las páginas de lista y detalle cuando el valor es `None` |
| `empty_template` | `"fields/detail/_empty.html"` | Las páginas de lista y detalle cuando el valor es una lista o tupla vacía |

Las cinco plantillas reciben la instancia `field` y el valor actual de `data`. Para `list_template` y `detail_template`, `data` nunca es `None` ni está vacío, porque esos casos se redirigen a `null_template` o `empty_template` antes de incluir la plantilla específica del tipo. La plantilla `form_template` también recibe `error` (el mensaje de un `FormValidationError`, si ocurrió alguno) y `action` (`RequestAction.CREATE`, `RequestAction.EDIT` o `RequestAction.INLINE_EDIT` cuando se renderiza dentro del popover de [edición en línea](../user-guide/inline-edit.md) de la página de lista). Las tres son acciones de formulario, por lo que `action.is_form()` devuelve `True`. El código del campo que necesite la representación del valor del formulario debe ramificar sobre eso en lugar de sobre `action == RequestAction.EDIT`.

Sobrescriba `null_template` y `empty_template` cuando un valor ausente deba verse diferente de las etiquetas predeterminadas atenuadas `-null-` y `-empty-`, por ejemplo, un icono de estado vacío o una insignia «No proporcionado» que coincida con el estilo propio del campo:

```python
@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    null_template: str = "employee/status_badge_null.html"
    empty_template: str = "employee/status_badge_null.html"
```

```html title="templates/employee/status_badge_null.html"
<span class="badge">Unknown</span>
```

Dado que `null_template` y `empty_template` son atributos de campo simples como `list_template`, se comparten entre la vista de lista, la de detalle y cualquier otra vista que renderice este campo, como la tabla en línea de una vista relacionada.

`StatusBadgeField` asigna la misma plantilla tanto a `list_template` como a `detail_template`, porque la misma insignia funciona en ambos contextos:

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

`AvatarNameField` solo sobrescribe `list_template`. La variable `data` en esta plantilla es el diccionario que construyó `parse_obj` y que reformateó `serialize_value`, en lugar de una cadena simple:

```html title="templates/employee/avatar_name.html"
<span class="avatar avatar-xs me-2"
      {% if data.avatar_url %}style="background-image: url({{ data.avatar_url }})"{% endif %}>
    {% if not data.avatar_url %}{{ data.initials }}{% endif %}
</span>
<span class="inline-edit-value">{{ data.name }}</span>

```

La clase `inline-edit-value` es el marcador opcional para el subrayado de la [edición en línea](../user-guide/inline-edit.md). Es inerte a menos que el campo sea editable en línea, por lo que aplicarla al nombre y no al avatar no tiene ningún coste aquí, mientras mantiene la indicación correctamente acotada si el campo llegara a ser editable.

Sobrescribir `list_template` y `detail_template` manteniendo el `form_template` predeterminado es exactamente lo que hace `StatusBadgeField` al extender `EnumField`. La plantilla predeterminada `fields/form/enum.html` renderiza un menú desplegable `<select>` poblado a partir de `field.choices`, por lo que editar un estado funciona sin ningún cambio adicional.

## Registro en el registro de convertidores

La lista `fields = [...]` de una vista acepta nombres de atributos simples además de objetos de campo. Cualquier elemento que aún no sea un `BaseField` pasa por un **registro de convertidores** que mapea el tipo de columna a una clase de campo. Cada backend de ORM incluye su propio registro (`starlette_admin.contrib.sqla.converters.ModelConverter` y sus equivalentes para `beanie`, `mongoengine` y `tortoise`), todos construidos sobre la misma base:

```python
from starlette_admin.converters import BaseModelConverter, converts
```

El decorador `@converts(*types)` marca un método como el convertidor para una o más claves de tipo. `BaseModelConverter.__init__` escanea la instancia en busca de estos métodos decorados y construye a partir de ellos su diccionario `converters`. Para el backend de SQLAlchemy, las claves de tipo son los **nombres** de los tipos de columna (`"String"`, `"Integer"`, `"Enum"`, etc.), porque SQLAlchemy no tiene una única clase base común entre dialectos.

Herede del convertidor del backend para añadir sus propias asignaciones. Este ejemplo dirige cada columna `Enum` a `StatusBadgeField` en lugar del `EnumField` predeterminado:

```python
from typing import Any

from starlette_admin.contrib.sqla.converters import ModelConverter
from starlette_admin.converters import converts
from starlette_admin.fields import BaseField


class MyModelConverter(ModelConverter):
    @converts("Enum")
    def conv_enum(self, *args: Any, **kwargs: Any) -> BaseField:
        _type = kwargs["type"]
        return StatusBadgeField(
            **self._field_common(*args, **kwargs), enum=_type.enum_class
        )
```

Pase la subclase a `ModelView(converter=...)` para que los nombres de campo como cadenas en `fields = [...]` se resuelvan a través de su convertidor en lugar del predeterminado:

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "name", "status"]


admin.add_view(EmployeeView(Employee, converter=MyModelConverter()))
```

Si siempre construye los campos explícitamente, como en el ejemplo mínimo anterior, puede omitir el registro de convertidores. Solo lo necesita cuando quiere que una entrada como `fields = ["status"]` produzca un `StatusBadgeField` a partir del tipo de columna subyacente.

---

## ¿Qué sigue?

* **[Fields](../user-guide/fields.md):** La referencia completa de los campos integrados y la tabla de atributos de `BaseField`.
* **[Templates](templates.md):** Cómo el loader de plantillas resuelve `list_template`, `detail_template`, `form_template`, `null_template` y `empty_template`.
* **[Extension Points](extension-points.md):** Todas las demás superficies conectables de `starlette-admin`.
