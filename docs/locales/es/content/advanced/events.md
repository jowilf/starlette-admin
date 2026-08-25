---
title: Eventos
description: Suscríbase a eventos globales del ciclo de vida como AFTER_CREATE para
  construir registros de auditoría, webhooks y flujos de trabajo asíncronos.
source_hash: e066fc5f57c4f38a189d1a2889e1aa3463d726bf0b7b986068937f673c067a6f
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/advanced/events/)
<!-- translation-notice:end -->

# Eventos

Un hook de método como `before_create` solo se ejecuta en la vista que lo define. El sistema de eventos permite que código externo a esa vista reaccione a lo que ocurre dentro de ella; esto significa que un registro de auditoría, un webhook o una invalidación de caché pueden vivir en un único lugar en lugar de copiarse y pegarse en cada `ModelView` que usted escriba.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def notify_slack(ctx: AfterCreateContext) -> None:
    print(f"New {ctx.view_key} created: pk={ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, notify_slack)
```

Registre esto una sola vez junto a su instancia de `admin` y el endpoint de creación de cada vista lo llamará, incluidas las vistas que añada más adelante.

## Nivel de vista frente a nivel de admin

Cada vista tiene un atributo `events` al que puede suscribirse directamente, con alcance limitado únicamente a esa vista. La instancia de `Admin` también tiene uno, que alcanza a todas las vistas registradas en ella, o a un subconjunto si pasa `keys=`.

* **`view.events.on(...)`**: Se dispara solo para esa vista.
* **`admin.events.on(...)`**: Se dispara para todas las vistas actuales y futuras, salvo que lo restrinja con `keys=`.

Puede registrarse en `admin.events` antes o después de llamar a `admin.add_view(...)`. El orden no importa: un handler registrado primero seguirá adjuntándose a la vista cuando la añada.

## Hooks de método frente a suscripciones de eventos

Ambos se disparan en el mismo punto del ciclo de vida de la petición. Se diferencian en dónde reside el código y a cuántas vistas alcanza.

| Característica | Hook de método (`before_create`, ...) | Suscripción de evento (`view.events` / `admin.events`) |
| --- | --- | --- |
| **Dónde reside el código** | Dentro de la clase de la vista | En cualquier lugar, por ejemplo una función a nivel de módulo o una clase suscriptora |
| **Alcance** | Esa vista concreta | Una vista (`view.events`) o todas las vistas (`admin.events`) |
| **Adecuado para** | Lógica específica de ese recurso (generar un slug para un título, estampar una marca de tiempo) | Preocupaciones transversales (registros de auditoría, notificaciones, plugins) |
| **¿Se permiten varios?** | No, un método por vista | Sí, cualquier cantidad de handlers por evento, ordenados por prioridad |

Use un hook de método cuando la lógica sea intrínseca al modelo. Use una suscripción de evento cuando no pertenezca a ninguna vista en particular, o cuando vaya a distribuirlo como una pieza reutilizable entre varios admins.

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

| Evento | Cuándo se dispara | Clase de contexto |
| --- | --- | --- |
| `BEFORE_CREATE` / `AFTER_CREATE` | Registro creado | `BeforeCreateContext` / `AfterCreateContext` |
| `AFTER_CREATE_COMMITTED` | Transacción de creación confirmada | `AfterCreateContext` |
| `BEFORE_EDIT` / `AFTER_EDIT` | Registro actualizado | `BeforeEditContext` / `AfterEditContext` |
| `AFTER_EDIT_COMMITTED` | Transacción de edición confirmada | `AfterEditContext` |
| `BEFORE_DELETE` / `AFTER_DELETE` | Registro eliminado | `BeforeDeleteContext` / `AfterDeleteContext` |
| `AFTER_DELETE_COMMITTED` | Transacción de eliminación confirmada | `AfterDeleteContext` |
| `BEFORE_ACTION` / `AFTER_ACTION` | Acción por lotes o por fila ejecutada | `BeforeActionContext` / `AfterActionContext` |
| `BEFORE_EXPORT` / `AFTER_EXPORT` | Exportación iniciada | `BeforeExportContext` / `AfterExportContext` |
| `BEFORE_IMPORT` / `AFTER_IMPORT` | Importación iniciada | `BeforeImportContext` / `AfterImportContext` |
| `AFTER_LOGIN` | Inicio de sesión exitoso | `AfterLoginContext` |

`AFTER_CREATE_COMMITTED`, `AFTER_EDIT_COMMITTED` y `AFTER_DELETE_COMMITTED` solo se disparan en backends que difieren el commit hasta el final de la petición, lo cual hoy significa el backend de SQLAlchemy. Consulte [Views](../user-guide/views.md#lifecycle-hooks) para conocer los métodos de hook `after_create_committed`, `after_edit_committed` y `after_delete_committed` que los emiten.

Para `AFTER_DELETE_COMMITTED`, `ctx.obj` es una instancia detached: sus atributos ya cargados siguen siendo legibles, pero leer un atributo que no se cargó antes de la eliminación genera un error, porque la fila que lo respalda ya no existe.

Cada contexto es una dataclass que hereda de `EventContext`, la cual contiene campos comunes a todos los eventos:

| Atributo | Tipo | Descripción |
| --- | --- | --- |
| `event` | `AdminEvent` o `str` | El evento que se disparó |
| `request` | `Request` | La petición en curso |
| `view_key` | `str` | El `key` de la vista |
| `extra` | `dict` | Vacío por defecto, disponible para que usted almacene datos en una cadena de handlers personalizada |

Cada subclase añade los campos relevantes para su evento.

Los eventos de edición disparados por una [edición en línea](../user-guide/inline-edit.md) desde la página de lista incluyen `extra["inline"] = True`, y sus payloads `data` / `old_data` contienen únicamente el campo editado. Todo lo demás es idéntico a una edición normal, por lo que los handlers existentes no requieren cambios.

## Suscripción mediante decorador

`view.events.on()` funciona tanto como decorador como llamada directa de función:

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

Registrado de esta manera, `log_deletion` se dispara únicamente para `order_view`, no para otras vistas del admin. El método `on()` también acepta el handler directamente, sin la forma de decorador:

```python
order_view.events.on(AdminEvent.BEFORE_DELETE, log_deletion)
```

## AdminEventSubscriber: agrupación de handlers

Cuando una misma preocupación reacciona a varios eventos, `AdminEventSubscriber` los mantiene en una única clase en lugar de dispersar funciones a nivel de módulo. Decore los métodos con `@on(AdminEvent.X)`, el `on` a nivel de módulo de `starlette_admin.events` y no el método del bus, y luego llame a `subscribe()` una vez:

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

`subscribe()` está disponible tanto en `view.events` como en `admin.events`. Llámelo sobre `view.events` para limitar el alcance del suscriptor a una sola vista.

Un mismo método puede manejar varios eventos: `@on(AdminEvent.AFTER_CREATE, AdminEvent.AFTER_EDIT)` registra el mismo método para ambos.

## admin.events: delegación hacia las vistas

`admin.events.on()` acepta los mismos argumentos que `view.events.on()`, además de `keys=`, una lista de claves de vista para restringir la suscripción. Si lo deja sin establecer (`None`, el valor predeterminado), todas las vistas de modelo actuales y futuras recibirán el handler:

```python
import httpx
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])
async def notify_new_order(ctx: AfterCreateContext) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"New order: {ctx.pk}"})
```

Solo la vista registrada con `key="order"`, o cuya clave predeterminada resuelve a `"order"`, llama a este handler. Un `AFTER_CREATE` en cualquier otra vista no lo activará.

`admin.events.subscribe()` también acepta `keys=`, de modo que puede limitar el alcance de un `AdminEventSubscriber` a un subconjunto de vistas de la misma manera:

```python
admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

`keys=` solo afecta a los eventos del ciclo de vida de las vistas de la tabla anterior: creación, edición, eliminación, acción, exportación e importación. Así es como `admin.events` decide a qué vistas aplica un handler. `AFTER_LOGIN` es de nivel de admin y no está vinculado a ninguna vista, por lo que `keys=` no tiene efecto sobre él.

## Prioridad

`on()` acepta un argumento de palabra clave `priority`, un entero cuyo valor predeterminado es `0`. Los handlers de un mismo evento se ejecutan en orden descendente de prioridad, de modo que un número mayor se dispara primero:

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

Los handlers con la misma prioridad se ejecutan en orden de registro. Los métodos de `AdminEventSubscriber` reciben una prioridad mediante `@on(AdminEvent.X, priority=10)`, que se reenvía de la misma manera.

!!! warning
    Un handler de `BEFORE_DELETE`, o cualquier handler `BEFORE_*`, que lance una excepción detiene la operación, y los handlers posteriores de ese evento no se ejecutan. Un handler `AFTER_*` que lance una excepción convierte un cambio ya confirmado en una petición fallida. Si un fallo no debe manifestarse como un error del admin, envuelva la lógica riesgosa, como llamadas de red o APIs de terceros, en su propio bloque `try`/`except` dentro del handler.

## Ejemplo ampliado

[`examples/05-events`](https://github.com/jowilf/starlette-admin/tree/main/examples/05-events) ejecuta juntos todos los patrones de esta página: overrides de hooks en `PostView`, un `AuditSubscriber` registrado en `admin.events` para todas las vistas, registro directo de handlers para advertencias de eliminación, exportación e importación, un handler con alcance limitado a `post_view.events` y un `CommentModerationSubscriber` con alcance limitado a `comment_view.events`. Ejecútelo para observar cómo interactúan la prioridad y el alcance en una sola aplicación.

---

## ¿Qué sigue?

* **[Views](../user-guide/views.md)**: Los hooks de método `before_*` y `after_*` sobre los que se basa esta página.
* **[Actions](../user-guide/actions.md)**: Acciones por lotes y por fila, que emiten `BEFORE_ACTION` / `AFTER_ACTION`.
* **[Inline Forms](../user-guide/inline-forms.md)**: Registros anidados creados junto a un elemento padre.
