---
title: Mensajes flash
description: Envíe alertas efímeras de éxito, advertencia o error a los usuarios tras
  completar acciones en starlette-admin.
source_hash: 597d52f90701d02e1620bfc199dbd2bdebc85f958d6f79d8458d1f8d50a0f9ec
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/flash-messages/)
<!-- translation-notice:end -->

# Mensajes flash

Los mensajes flash proporcionan a los usuarios una retroalimentación temporal y de un solo uso después de que realizan una acción, como «Post created successfully» o «Invalid file type». Un mensaje sobrevive a una única redirección HTTP y el panel lo descarta después de mostrarlo.

`flash()` encola un mensaje en la solicitud actual. El panel muestra el mensaje en la siguiente página que el usuario ve y luego limpia la cola. Este patrón proviene de Flask-Admin.


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

Cada mensaje flash necesita una categoría. La categoría define el color del banner en el tema predeterminado, de modo que los usuarios puedan evaluar la gravedad de un vistazo.

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")
```

El argumento `category` tiene `"info"` como valor predeterminado. Debe ser exactamente uno de `success`, `info`, `warning` o `error`. Cualquier otro valor lanza una `ValueError`.

## Mensajes CRUD integrados

No necesita llamar a `flash()` para las operaciones CRUD estándar. El panel emite automáticamente un mensaje de tipo `success` cuando estas acciones finalizan:

| Acción | Mensaje predeterminado |
| --- | --- |
| **Create** | `The item "<repr>" was added successfully.` |
| **Edit** | `The item "<repr>" was changed successfully.` |
| **Delete (single)** | `The item "<repr>" was successfully deleted.` |
| **Delete (bulk)** | `%(count)d items were successfully deleted.` |

!!! note "A qué se resuelve `<repr>`"
    Los mensajes automáticos utilizan la representación de fila definida por `view.repr()`, no el nombre de la clase del modelo. Por ejemplo, al crear una publicación se muestra *«The item 'My First Post' was added successfully»* en lugar de un genérico *«Post was added successfully»*.

## Uso de mensajes flash en acciones personalizadas

Los manejadores de acciones personalizadas (`@action` y `@row_action`) devuelven `None` de forma predeterminada. Para dar retroalimentación al usuario, llame a `flash()` antes de que el manejador retorne.

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

* **Si omite `flash()`:** La acción se ejecuta igualmente, pero el usuario no recibe ninguna confirmación visual después de que la página se redirige.
* **Si la acción falla:** Cuando su acción personalizada lanza `ActionFailed`, el panel intercepta la excepción y muestra su cadena como un banner de error. No llame a `flash()` en una rama de `ActionFailed`, porque la solicitud no se redirige.

## Renderizado de mensajes en plantillas personalizadas

La plantilla base del panel extrae y renderiza los mensajes flash por usted. Solo necesita recuperarlos usted mismo si construye una [vista personalizada](custom-views.md) completa.

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]
```

Leer la cola de mensajes flash es **destructivo**. La primera llamada a `get_flashed_messages(request)` extrae y limpia la cola. Las llamadas posteriores durante la misma solicitud devuelven una lista vacía, `[]`.

!!! important "Mantenga los mensajes breves"
    Los mensajes flash se almacenan en una cookie firmada y `httponly` llamada `admin_flash`, no en la sesión del servidor. Los navegadores limitan el tamaño de las cookies a aproximadamente 4 KB, así que utilice los mensajes flash únicamente para retroalimentación breve. Evite cadenas largas y cargas de datos grandes. El enfoque basado en cookies también significa que los mensajes flash funcionan sin `SessionMiddleware`.

> Consulte [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions) para ver una aplicación ejecutable que llama a `flash()` desde hooks y acciones personalizadas.

---

## Próximos pasos

* **[Acciones](actions.md)**: Ejecute lógica de negocio desde acciones masivas o de fila.
* **[Seguridad](security.md)**: Vea cómo `secret_key` protege tanto la cookie de mensajes flash como los tokens CSRF.
* **[Plantillas](../advanced/templates.md)**: Renderice banners de mensajes flash dentro de sus propios diseños.
