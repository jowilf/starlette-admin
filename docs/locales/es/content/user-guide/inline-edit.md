---
title: Edición en línea
description: Permita que los usuarios editen los valores de los campos directamente
  en la tabla de la página de lista para acelerar la entrada de datos.
source_hash: eaec1e767aabf070c53dc837993958784bc8326597e2c008e52bf592dc1f1ae2
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/inline-edit/)
<!-- translation-notice:end -->

# Edición en línea

La edición en línea permite a los usuarios cambiar un solo campo directamente desde la página de lista. Al seleccionar una celda, se abre un pequeño popover, de modo que nadie tiene que abrir el formulario de edición completo. Utilícela para actualizaciones rápidas de un solo campo: corregir un título, cambiar un estado o ajustar una fecha. La interacción sigue el conocido patrón de [x-editable](https://vitalets.github.io/x-editable/).

Esta función es opcional y está desactivada de forma predeterminada. Activarla no modifica la página de edición estándar, que sigue siendo la interfaz principal para las ediciones complejas de varios campos.

> Para ver un ejemplo ejecutable con edición en línea, consulte [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

## Uso básico

Declare los nombres de los campos editables en la lista `inline_editable_fields`:

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "status", "views", "published_at"]
    inline_editable_fields = ["title", "status", "views", "published_at"]
```

Las celdas editables muestran entonces un subrayado discontinuo en la página de lista. Al seleccionar una celda, se abre un popover con el control de formulario estándar del campo, rellenado previamente con el valor actual.

El subrayado no se pinta sobre toda la celda. Cada plantilla de lista aplica la clase CSS `inline-edit-value` al elemento exacto que debe subrayarse, y el estilo se aplica solo dentro de una celda editable. Todas las plantillas de lista integradas ya incluyen la clase. Si escribe una `list_template` personalizada y desea la misma indicación visual, añada la clase usted mismo:

```html
<span class="avatar avatar-xs me-2">...</span>
<span class="inline-edit-value">{{ data.name }}</span>
```

Sin la clase, la celda sigue abriendo el popover, pero no muestra ningún subrayado.

- **Guardar:** Seleccione el botón de verificación o pulse <kbd>Enter</kbd> en un campo de entrada de una sola línea. El panel de administración valida el campo, guarda el cambio y actualiza la fila sin recargar la página.
- **Cancelar:** Seleccione el botón <kbd>x</kbd> o pulse <kbd>Esc</kbd> para descartar el cambio.

## Reglas de configuración

La aplicación valida `inline_editable_fields` al inicio, de modo que los errores de configuración se detectan de inmediato. Un nombre incluido en la lista genera un `ValueError` cuando cumple alguna de estas condiciones:

- No está declarado en `fields`.
- Es el campo de la clave primaria.
- Está excluido de la página de lista (`exclude_from_list`) o del formulario de edición (`exclude_from_edit`).
- Es un campo contenedor o de solo lectura: `CollectionField`, `ListField`, `ComputedField`, `FileField` o `ImageField`.

## Compatibilidad de campos

Cada campo editable muestra el mismo widget de formulario que utiliza en la página de edición. Los recursos de JavaScript y CSS de un campo, como select2, flatpickr, JSONEditor o TinyMCE, se cargan en la página de lista solo cuando ese campo es editable en línea. Las vistas sin edición en línea conservan su huella de página ligera actual.

| Tipo de campo                                                                        | Compatible | Widget del popover                    |
| ------------------------------------------------------------------------------------ | ---------- | ------------------------------------- |
| `StringField`, `EmailField`, `URLField`, `PhoneField`, `ColorField`, `PasswordField` | Sí         | Campo de entrada simple               |
| `SlugField`                                                                          | Sí         | Campo de entrada simple (sin campo de origen) |
| `TextAreaField`                                                                      | Sí         | Textarea                              |
| `IntegerField`, `DecimalField`, `FloatField`                                         | Sí         | Campo de entrada numérico             |
| `BooleanField`                                                                       | Sí         | Interruptor                           |
| `DateField`, `DateTimeField`, `TimeField`, `ArrowField`                              | Sí         | flatpickr                             |
| `EnumField`, `TimeZoneField`, `CountryField`, `CurrencyField`                        | Sí         | select2 o select nativo               |
| `TagsField`                                                                          | Sí         | Etiquetas de select2                  |
| `JSONField`                                                                          | Sí         | JSONEditor                            |
| `TinyMCEEditorField`                                                                 | Sí         | TinyMCE                               |
| `HasOne`, `HasMany`                                                                  | Sí         | select2 con búsqueda asíncrona        |
| `FileField`, `ImageField`                                                            | No         | Ninguno (requiere la página de edición) |
| `CollectionField`, `ListField`, `ComputedField`                                      | No         | Ninguno (contenedores de solo lectura) |

---

## Permisos

La edición en línea reutiliza el modelo de permisos existente. El popover aparece, y el panel de administración acepta la solicitud, solo cuando tanto `is_accessible(request)` como `can_edit(request)` devuelven `True`. Por lo tanto, sobrescribir `can_edit` también protege las ediciones en línea:

```python
class PostView(ModelView):
    inline_editable_fields = ["title", "status"]

    def can_edit(self, request: Request) -> bool:
        # También desactiva la edición en línea cuando es False
        return "edit:post" in request.state.admin_user.roles
```

---

## Validación

Un guardado en línea valida y escribe únicamente el campo editado.

- La comprobación de `required` del campo y la cadena de `validators` se ejecutan exactamente igual que en la página de edición.
- Los demás campos se omiten. Un guardado desde la página de lista no puede sobrescribir una edición simultánea de otro campo, y los datos no válidos en otro campo no impiden el guardado.

El hook `validate` de campos cruzados de la vista sigue ejecutándose, pero el diccionario `data` contiene únicamente el campo editado. Un hook que espera un envío de formulario completo genera un `KeyError` si accede directamente a claves inexistentes, así que verifique primero que la clave esté presente:

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    inline_editable_fields = ["title", "status", "published_at"]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}

        if "title" in data and (not data["title"] or len(data["title"]) < 3):
            errors["title"] = "Ensure this value has at least 3 characters"

        if (
            "published_at" in data
            and data.get("status") == "published"
            and data["published_at"] is None
        ):
            errors["published_at"] = "Required when status is published"

        if errors:
            raise FormValidationError(errors)

        await super().validate(request, data)
```

Cuando la validación falla, el popover permanece abierto con el valor enviado intacto. El mensaje del campo editado se muestra debajo del control, exactamente igual que en la página de edición. Un mensaje asociado a otro campo lleva como prefijo la etiqueta de ese campo.

Para detectar un guardado en línea dentro de un hook, compruebe `request.state.action == RequestAction.INLINE_EDIT`. Utilícelo para omitir los mensajes flash destinados a páginas renderizadas completas.

!!! warning
    Una regla de validación asociada a un campo que el usuario no editó no se ejecuta durante un guardado en línea. Si las invariantes de un campo dependen de valores que el usuario no puede ver ni modificar desde la página de lista, excluya ese campo de `inline_editable_fields`.

---

## Hooks de ciclo de vida y eventos

Los guardados en línea pasan por la ruta estándar `edit()` de la vista. Los hooks `before_edit`, `after_edit` y `after_edit_committed` se activan como de costumbre, y los [eventos](../advanced/events.md) correspondientes utilizan los tipos de contexto estándar. Las cargas útiles `data` y `old_data` contienen únicamente el campo editado, por lo que reflejan exactamente lo que afectó el guardado.

Para distinguir un guardado en línea dentro de un detector de eventos, compruebe `ctx.extra["inline"]`, que es `True` para las ediciones en línea:

```python
from starlette_admin import AdminEvent
from starlette_admin.events import AfterEditContext


@admin.events.on(AdminEvent.AFTER_EDIT)
async def audit(ctx: AfterEditContext) -> None:
    source = "list page" if ctx.extra.get("inline") else "edit page"
    logger.info("updated %s pk=%s from the %s", ctx.view_key, ctx.pk, source)
```

---

## Campos personalizados

Los campos personalizados admiten la edición en línea automáticamente cuando siguen el contrato estándar de `BaseField`. Dado que `RequestAction.INLINE_EDIT` es una acción de formulario, `action.is_form()` devuelve `True`. Si su campo personalizado comprueba `action == RequestAction.EDIT` para construir una representación del valor del formulario, cámbiela para usar `action.is_form()`, de modo que el popover reciba la representación correcta. Para conocer el contrato completo de los campos, consulte [Campos personalizados](../advanced/custom-fields.md).
