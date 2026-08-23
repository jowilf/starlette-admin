---
title: Mensajes flash
description: Envíe alertas efímeras de éxito, advertencia o error a los usuarios después
  de completar acciones en starlette-admin.
source_hash: 597d52f90701d02e1620bfc199dbd2bdebc85f958d6f79d8458d1f8d50a0f9ec
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/flash-messages/)
<!-- translation-notice:end -->

# Mensajes flash

Los mensajes flash proporcionan a los usuarios una retroalimentación temporal de una sola vez después de que realizan una acción, como «Post created successfully» o «Invalid file type». Un mensaje sobrevive a una única redirección HTTP, y el panel de administración lo descarta después de mostrarlo.

`flash()` pone un mensaje en cola en la solicitud actual. El panel de administración renderiza el mensaje en la siguiente página que el usuario ve y, a continuación, limpia la cola. Este patrón proviene de Flask-Admin.


```python
from starlette.requests import Request
from starlette_admin import BaseModelView
from starlette_admin.flash import flash

class PostView(BaseModelView):
    async def before_create(self, request: Request, data: dict) -> None:
        if not data.get("title", "").strip():
            # Queue the message for the next page load
            flash(request, "Title cannot be blank.", category="error")
            raise ValueError("Title cannot be blank.")

```

## Categorías de mensajes

Cada mensaje flash necesita una categoría. La categoría establece el color del banner en el tema predeterminado, de modo que los usuarios puedan evaluar la gravedad de un vistazo.

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")

```

El argumento `category` tiene como valor predeterminado `"info"`. Debe ser exactamente uno de `success`, `info`, `warning` o `error`. Cualquier otro valor genera un `ValueError`.

## Mensajes CRUD integrados

No necesita llamar a `flash()` para las operaciones CRUD estándar. El panel de administración muestra automáticamente un mensaje `success` cuando estas acciones finalizan:

| Acción | Mensaje predeterminado |
| --- | --- |
| **Crear** | `The item "<repr>" was added successfully.` |
| **Editar** | `The item "<repr>" was changed successfully.` |
| **Eliminar (individual)** | `The item "<repr>" was successfully deleted.` |
| **Eliminar (por lotes)** | `%(count)d items were successfully deleted.` |

!!! note "A qué se resuelve `<repr>`"
    Los mensajes automáticos usan la representación de la fila que define `view.repr()`, no el nombre de la clase del modelo. Por ejemplo, al crear una publicación se muestra el mensaje flash *«The item 'My First Post' was added successfully»* en lugar de un genérico *«Post was added successfully»*.

## Uso de mensajes flash en acciones personalizadas

Los controladores de acciones personalizadas (`@action` y `@row_action`) devuelven `None` de forma predeterminada. Para dar retroalimentación al usuario, llame a `flash()` antes de que el controlador retorne.

```python
from starlette.requests import Request
from starlette_admin import BaseModelView, action, flash

class PostView(BaseModelView):
    @action(
        name="publish",
        text="Publish",
        confirmation="Publish the selected posts?",
    )
    async def publish_action(self, request: Request, pks: list) -> None:
        for pk in pks:
            obj = await self.find_by_pk(request, pk)
            obj.published = True
            await self.edit(request, pk, {"published": True})

        # Notify the user that the custom action succeeded
        flash(request, f"{len(pks)} post(s) published.", category="success")

```

* **Si omite `flash()`:** La acción se ejecuta de todos modos, pero el usuario no recibe ninguna confirmación visual después de que la página se redirige.
* **Si la acción falla:** Cuando su acción personalizada genera `ActionFailed`, el panel de administración intercepta la excepción y muestra la cadena de la excepción como un banner de error. No llame a `flash()` en una rama de `ActionFailed`, porque la solicitud no se redirige.

## Renderizado de mensajes en plantillas personalizadas

La plantilla base del panel de administración extrae y renderiza los mensajes flash por usted. Solo necesita recuperarlos por su cuenta cuando cree una [vista personalizada](custom-views.md) completa.

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]

```

Leer la cola de mensajes flash es una operación **destructiva**. La primera llamada a `get_flashed_messages(request)` extrae y limpia la cola. Las llamadas posteriores durante la misma solicitud devuelven una lista vacía, `[]`.

!!! important "Mantenga los mensajes cortos"
    Los mensajes flash se almacenan en una cookie firmada y `httponly` llamada `admin_flash`, no en la sesión del servidor. Los navegadores limitan el tamaño de las cookies a aproximadamente 4 KB, por lo que debe usar los mensajes flash solo para retroalimentación breve. Evite las cadenas largas y las cargas de datos de gran tamaño. El enfoque basado en cookies también significa que los mensajes flash funcionan sin `SessionMiddleware`.

> Consulte [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions) para ver una aplicación ejecutable que llama a `flash()` desde hooks y acciones personalizadas.

---

## Próximos pasos

* **[Acciones](actions.md)**: Active la lógica de negocio desde acciones por lotes o acciones de fila.
* **[Seguridad](security.md)**: Vea cómo `secret_key` protege tanto la cookie de mensajes flash como los tokens CSRF.
* **[Plantillas](../advanced/templates.md)**: Renderice banners de mensajes flash dentro de sus propias plantillas.
