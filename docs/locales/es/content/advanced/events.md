---
title: Eventos
description: Suscríbase a eventos globales del ciclo de vida como AFTER_CREATE para
  construir registros de auditoría, webhooks y flujos de trabajo asíncronos.
source_hash: e066fc5f57c4f38a189d1a2889e1aa3463d726bf0b7b986068937f673c067a6f
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/advanced/events/)
<!-- translation-notice:end -->

# Eventos

Un hook de método como `before_create` solo se ejecuta en la vista que lo define. El sistema de eventos permite que el código fuera de esa vista reaccione a lo que ocurre dentro de ella, de modo que un registro de auditoría, un webhook o una invalidación de caché pueden vivir en un único lugar en lugar de copiarse y pegarse en cada `ModelView` que usted escriba.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def notify_slack(ctx: AfterCreateContext) -> None:
    print(f"New {ctx.view_key} created: pk={ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, notify_slack)
```

Registre esto una sola vez junto a su instancia `admin` y el endpoint de creación de todas las vistas lo llamará, incluidas las vistas que añada más adelante.

## Vista frente a nivel de administración

Cada vista tiene un atributo `events` al que puede suscribirse directamente, con alcance limitado a esa vista. La instancia `Admin` también tiene uno, que alcanza a todas las vistas registradas en ella, o a un subconjunto si pasa `keys=`.

* **`view.events.on(...)`**: se activa solo para esa vista.
* **`admin.events.on(...)`**: se activa para cada vista actual y futura, salvo que la restrinja con `keys=`.

Puede registrarse en `admin.events` antes o después de llamar a `admin.add_view(...)`. El orden no importa: un manejador registrado primero se adjunta igualmente a la vista cuando la añade.

## Hooks de método frente a suscripciones a eventos

Ambos se activan en el mismo punto del ciclo de vida de la solicitud. Se diferencian en dónde vive el código y a cuántas vistas alcanza.

| Característica | Hook de método (`before_create`, ...) | Suscripción a evento (`view.events` / `admin.events`) |
| --- | --- | --- |
| **Dónde vive el código** | Dentro de la clase de la vista | En cualquier lugar, por ejemplo en una función a nivel de módulo o en una clase suscriptora |
| **Alcance** | Esa vista específica | Una vista (`view.events`) o todas las vistas (`admin.events`) |
| **Adecuado para** | Lógica específica de ese recurso (convertir un título en slug, sellar una marca de tiempo) | Preocupaciones transversales (registros de auditoría, notificaciones, plugins) |
| **¿Se permiten varios?** | No, un método por vista | Sí, cualquier cantidad de manejadores por evento, ordenados por prioridad |

Use un hook de método cuando la lógica sea intrínseca al modelo. Use una suscripción a evento cuando no pertenezca a ninguna vista concreta, o cuando la distribuya como una pieza reutilizable entre varias instancias de administración.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    # Belongs to this view only, stays here
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")
```

## Valores de AdminEvent

`AdminEvent` es un enum de cadenas. Estos son los miembros emitidos activamente por el ciclo de vida de las vistas:

| Evento | Se emite cuando | Clase de contexto |
| --- | --- | --- |
| `BEFORE_CREATE` / `AFTER_CREATE` | Se crea un registro | `BeforeCreateContext` / `AfterCreateContext` |
| `AFTER_CREATE_COMMITTED` | Se confirma la transacción de creación | `AfterCreateContext` |
| `BEFORE_EDIT` / `AFTER_EDIT` | Se actualiza un registro | `BeforeEditContext` / `AfterEditContext` |
| `AFTER_EDIT_COMMITTED` | Se confirma la transacción de edición | `AfterEditContext` |
| `BEFORE_DELETE` / `AFTER_DELETE` | Se elimina un registro | `BeforeDeleteContext` / `AfterDeleteContext` |
| `AFTER_DELETE_COMMITTED` | Se confirma la transacción de eliminación | `AfterDeleteContext` |
| `BEFORE_ACTION` / `AFTER_ACTION` | Se ejecuta una acción por lotes o de fila | `BeforeActionContext` / `AfterActionContext` |
| `BEFORE_EXPORT` / `AFTER_EXPORT` | Se desencadena una exportación | `BeforeExportContext` / `AfterExportContext` |
| `BEFORE_IMPORT` / `AFTER_IMPORT` | Se desencadena una importación | `BeforeImportContext` / `AfterImportContext` |
| `AFTER_LOGIN` | El inicio de sesión tiene éxito | `AfterLoginContext` |

`AFTER_CREATE_COMMITTED`, `AFTER_EDIT_COMMITTED` y `AFTER_DELETE_COMMITTED` solo se emiten en backends que difieren la confirmación hasta el final de la solicitud, lo cual hoy significa el backend SQLAlchemy. Consulte [Vistas](../user-guide/views.md#hooks-del-ciclo-de-vida) para conocer los métodos de hook `after_create_committed`, `after_edit_committed` y `after_delete_committed` que los emiten.

Para `AFTER_DELETE_COMMITTED`, `ctx.obj` es una instancia desvinculada (detached): sus atributos ya cargados siguen siendo legibles, pero leer un atributo que no se cargó antes de la eliminación lanza una excepción, porque la fila que lo respalda ya no existe.

Cada contexto es una dataclass que hereda de `EventContext`, la cual contiene los campos comunes a todos los eventos:

| Atributo | Tipo | Descripción |
| --- | --- | --- |
| `event` | `AdminEvent` o `str` | El evento emitido |
| `request` | `Request` | La solicitud en curso |
| `view_key` | `str` | La clave (`key`) de la vista |
| `extra` | `dict` | Vacío de forma predeterminada; disponible para almacenar datos libremente en una cadena personalizada de manejadores |

Cada subclase añade los campos pertinentes a su evento.

Los eventos de edición emitidos por una [edición integrada](../user-guide/inline-edit.md) desde la página de lista incluyen `extra["inline"] = True`, y sus cargas útiles `data` / `old_data` contienen únicamente el campo editado. Todo lo demás es idéntico a una edición regular, por lo que los manejadores existentes no requieren cambios.

## Suscribirse con un decorador

`view.events.on()` funciona tanto como decorador como mediante una llamada directa a la función:

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext
from starlette_admin.contrib.sqla import ModelView

logger = logging.getLogger(__name__)


class OrderView(ModelView):
    fields = ["id", "customer_name", "total", "status"]


order_view = OrderView(Order, icon="fa fa-shopping-cart")


@order_view.events.on(AdminEvent.BEFORE_DELETE)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("Deleting order pk=%s", ctx.pk)
```

Registrado de esta manera, `log_deletion` se ejecuta solo para `order_view`, y no para otras vistas de la administración. El método `on()` también acepta el manejador directamente, sin la forma de decorador:

```python
order_view.events.on(AdminEvent.BEFORE_DELETE, log_deletion)
```

## AdminEventSubscriber: agrupar manejadores

Cuando una misma preocupación reacciona a varios eventos, `AdminEventSubscriber` los mantiene en una única clase en lugar de dispersar funciones a nivel de módulo. Decore los métodos con `@on(AdminEvent.X)` —el `on` a nivel de módulo de `starlette_admin.events`, no el método del bus— y luego llame a `subscribe()` una vez:

```python
import logging
from starlette_admin.events import (
    AdminEvent,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    on,
)

logger = logging.getLogger(__name__)


class AuditSubscriber(AdminEventSubscriber):
    """Logs every create, update, or delete, on any view."""

    @on(AdminEvent.AFTER_CREATE)
    async def record_create(self, ctx: AfterCreateContext) -> None:
        logger.info("created %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_EDIT)
    async def record_update(self, ctx: AfterEditContext) -> None:
        logger.info("updated %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_DELETE)
    async def record_delete(self, ctx: AfterDeleteContext) -> None:
        logger.info("deleted %s pk=%s", ctx.view_key, ctx.pk)


admin.events.subscribe(AuditSubscriber())
```

`subscribe()` está disponible tanto en `view.events` como en `admin.events`. Llámelo sobre `view.events` para limitar el suscriptor a una única vista.

Un mismo método puede manejar varios eventos: `@on(AdminEvent.AFTER_CREATE, AdminEvent.AFTER_EDIT)` registra el mismo método para ambos.

## admin.events: delegar en las vistas

`admin.events.on()` acepta los mismos argumentos que `view.events.on()`, además de `keys=`, una lista de claves de vista a las que restringir la suscripción. Si lo deja sin establecer (`None`, el valor predeterminado), todas las vistas de modelos actuales y futuras recibirán el manejador:

```python
import httpx
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])
async def notify_new_order(ctx: AfterCreateContext) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"New order: {ctx.pk}"})
```

Solo la vista registrada con `key="order"`, o cuya clave predeterminada resuelve a `"order"`, llama a este manejador. Un `AFTER_CREATE` en cualquier otra vista no lo activará.

`admin.events.subscribe()` también acepta `keys=`, de modo que puede limitar un `AdminEventSubscriber` a un subconjunto de vistas de la misma forma:

```python
admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

`keys=` solo afecta a los eventos del ciclo de vida de las vistas de la tabla anterior: creación, edición, eliminación, acciones, exportación e importación. Así decide `admin.events` a qué vistas aplica un manejador. `AFTER_LOGIN` es de nivel de administración y no está ligado a ninguna vista, por lo que `keys=` no tiene ningún efecto sobre él.

## Prioridad

`on()` acepta la palabra clave `priority`, un entero cuyo valor predeterminado es `0`. Los manejadores del mismo evento se ejecutan en orden descendente de prioridad, de modo que un número mayor se ejecuta primero:

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext

logger = logging.getLogger(__name__)


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=10)
async def validate_can_delete(ctx: BeforeDeleteContext) -> None:
    if ctx.obj.status == "shipped":
        raise ValueError("Cannot delete a shipped order")  # runs first


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=0)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("deleting order pk=%s", ctx.pk)  # runs second
```

Los manejadores con la misma prioridad se ejecutan en orden de registro. Los métodos de `AdminEventSubscriber` reciben una prioridad mediante `@on(AdminEvent.X, priority=10)`, que se reenvía de la misma manera.

!!! warning
    Un manejador `BEFORE_DELETE`, o cualquier manejador `BEFORE_*`, que lance una excepción detiene la operación, y los manejadores posteriores de ese evento no se ejecutan. Un manejador `AFTER_*` que lance una excepción convierte un cambio ya confirmado en una solicitud fallida. Si un fallo no debe mostrarse como un error de administración, envuelva la lógica arriesgada, como llamadas de red o APIs de terceros, en su propio bloque `try`/`except` dentro del manejador.

## Ejemplo ampliado

[`examples/05-events`](https://github.com/jowilf/starlette-admin/tree/main/examples/05-events) ejecuta juntos todos los patrones de esta página: sobrescrituras de hooks en `PostView`, un `AuditSubscriber` registrado en `admin.events` para todas las vistas, registro directo de manejadores para avisos de eliminación, exportación e importación, un manejador limitado a `post_view.events` y un `CommentModerationSubscriber` limitado a `comment_view.events`. Ejecútelo para observar cómo interactúan la prioridad y el alcance en una sola aplicación.

---

## ¿Qué sigue?

* **[Vistas](../user-guide/views.md)**: los hooks de método `before_*` y `after_*` en los que se basa esta página.
* **[Acciones](../user-guide/actions.md)**: acciones por lotes y de fila, que emiten `BEFORE_ACTION` / `AFTER_ACTION`.
* **[Formularios integrados](../user-guide/inline-forms.md)**: registros anidados creados junto a un elemento padre.
