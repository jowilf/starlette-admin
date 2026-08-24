---
title: Acciones
description: Ejecute operaciones por lotes y a nivel de fila con confirmaciones y
  formularios personalizados directamente desde la vista de lista.
source_hash: 91835b28170a6a3e07ed477b89c2b03aabc37254d3037ef4e47467e6ee240fca
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/actions/)
<!-- translation-notice:end -->

# Acciones

Las acciones le ofrecen una forma directa de trabajar con sus registros de base de datos desde la interfaz de administración, de modo que los usuarios puedan ejecutar operaciones como eliminaciones masivas, actualizaciones en lote y envíos de correos electrónicos.

## Comprender `ActionSelection`

`ActionSelection` es el objeto central de la API de acciones. En lugar de una lista simple de claves primarias, su handler recibe una instancia de `ActionSelection`.

El objeto se resuelve de forma perezosa y se comporta igual tanto si el usuario marcó las filas una por una como si utilizó la opción «seleccionar todas las coincidencias». También expone los filtros activos de la página de lista a su handler.

### Referencia de la API de `ActionSelection`

| Método o propiedad        | Descripción                                                                                   |
| ------------------------- | --------------------------------------------------------------------------------------------- |
| `await selection.rows()`  | Recupera las filas objetivo. Se obtienen una sola vez y luego se almacenan en caché.          |
| `await selection.pks()`   | Recupera las claves primarias de las filas objetivo.                                          |
| `await selection.count()` | Devuelve el número total de filas a las que la acción apunta.                                 |
| `selection.is_select_all` | Un valor booleano que indica si el usuario eligió «seleccionar todas las coincidencias».      |
| `selection.filters`       | El `FilterGroup` activo, idéntico a `ListParams.filters`.                                     |
| `selection.q`             | El término de búsqueda de texto completo activo, o `None` cuando la búsqueda está inactiva.   |

## Acciones por lotes

De forma predeterminada, los usuarios actualizan un objeto seleccionándolo en la página de lista y editándolo individualmente. Para aplicar el mismo cambio a muchos objetos a la vez, añada una **acción por lotes** personalizada.

!!! note
    `starlette-admin` añade una acción por lotes `delete` de forma predeterminada.

Para añadir una acción por lotes personalizada a su `ModelView`, escriba una función asíncrona con su lógica y envuélvala con el decorador `@action`.

!!! important
    Los nombres de las acciones por lotes deben ser únicos dentro de un `ModelView`.

### Ejemplo de acción por lotes

```python
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from starlette_admin import ActionSelection, action, flash
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    actions = [
        "make_published",
        "redirect",
        "delete",
    ]

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")
        articles = await selection.rows()

        # TODO: Implement database update logic here

        if not articles:
            raise ActionFailed("Sorry, we cannot process this action right now.")

        flash(
            request,
            f"{len(articles)} articles were successfully marked as published.",
            "success",
        )

    @action(
        name="redirect",
        text="Redirect",
        custom_response=True,
        confirmation="Fill the form",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="value" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def redirect_action(
        self, request: Request, selection: ActionSelection
    ) -> Response:
        data = await request.form()
        return RedirectResponse(f"https://example.com/?value={data['value']}")

```

## Acciones globales

Una acción por lotes estándar requiere una selección activa: el menú desplegable **With selected** solo aparece cuando al menos una fila está marcada. Cuando una acción apunta a toda la colección, como una sincronización completa de la base de datos, conviértala en una acción global.

Establezca `allow_empty_selection=True` en el decorador `@action`. Las acciones globales se muestran en un menú desplegable **Actions** siempre visible y se ejecutan sin selección de filas.

**Comportamiento del handler con las acciones globales:**

- **Selección vacía:** El objeto `selection` puede resolverse a cero filas.
- **Selecciones incidentales:** Si el usuario tiene filas marcadas cuando desencadena una acción global, el handler sigue recibiendo esas filas. Ignore explícitamente `selection` cuando su lógica apunte a toda la colección.

Todos los demás parámetros (`confirmation`, `form`, `custom_response` e `is_action_allowed`) funcionan exactamente igual que en una acción por lotes estándar.

**Botones dedicados en la barra de herramientas:** Añada `dedicated_button=True` para mostrar una acción global como su propio botón de la barra de herramientas en lugar de una entrada del menú desplegable **Actions**. La acción de exportación integrada utiliza esta opción. Combinar `dedicated_button=True` con una acción que requiera selección genera un error al arrancar.

### Ejemplo de acción global

```python
class ArticleView(ModelView):
    actions = ["purge_drafts", "make_published", "delete"]

    @action(
        name="purge_drafts",
        text="Purge drafts",
        confirmation="Delete every draft article? This cannot be undone.",
        submit_btn_text="Yes, delete them",
        submit_btn_class="btn btn-danger",
        allow_empty_selection=True,
    )
    async def purge_drafts_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        # Executes without a selection; ignores the selection object entirely
        drafts = await delete_all_draft_articles()
        flash(request, f"{len(drafts)} draft article(s) were purged.", "success")

```

### La función «seleccionar todas las coincidencias»

Cuando un usuario marca todas las filas de la página actual y hay más filas que coinciden con el filtro en otras páginas, la interfaz ofrece seleccionar todas las filas coincidentes.

Esa opción envía `all=1` a la API de acciones en lugar de una lista de claves primarias. Utilice `selection.is_select_all` para bifurcar su lógica, o deje que `selection.rows()` resuelva los datos en cualquier caso:

```python
    @action(name="archive", text="Archive")
    async def archive_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        if selection.is_select_all:
            await self.bulk_archive_where(request, selection.filters, selection.q)
        else:
            await self.bulk_archive_pks(request, await selection.pks())

```

!!! important "Límites de materialización"
    En modo select-all, `selection.rows()`, `pks()` y `count()` están limitados por `action_select_all_limit`, cuyo valor predeterminado es 1000. Superar el límite genera una excepción `ActionFailed`. Un handler que solo lee `selection.filters` y `selection.q` no materializa nada, por lo que el límite no se aplica.

## Acciones de fila {#row-actions}

Las acciones de fila permiten a los usuarios operar sobre un único elemento directamente desde la vista de lista. `starlette-admin` incluye tres acciones de fila de forma predeterminada: `view`, `edit` y `delete`.

Para añadir una acción de fila personalizada, escriba su lógica y aplique el decorador `@row_action`. Cuando la acción únicamente redirige al usuario a otra URL, utilice en su lugar el decorador `@link_row_action`. Este incrusta el enlace en el atributo HTML `href` y omite la API de acciones.

!!! important
    Los nombres de las acciones de fila deben ser únicos dentro de un `ModelView`.

### Ejemplo de acción de fila

```python
from typing import Any
from starlette.datastructures import FormData
from starlette.requests import Request

from starlette_admin import flash, RowActionsDisplayType
from starlette_admin.actions import link_row_action, row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    row_actions = [
        "view",
        "edit",
        "go_to_example",
        "make_published",
        "delete",
    ]
    row_actions_display_type = RowActionsDisplayType.ICON_LIST

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        action_btn_class="btn btn-info",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")

        # TODO: Implement database update logic here

        flash(request, "The article was successfully marked as published", "success")

    @link_row_action(
        name="go_to_example",
        text="Go to example.com",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, request: Request, pk: Any) -> str:
        return f"https://example.com/?pk={pk}"

```

### Restricción de las acciones de fila

Dos hooks determinan si una acción de fila está disponible. Ambos permiten la acción de forma predeterminada.

1. **`is_row_action_allowed(request, name)`**: Se ejecuta una vez por nombre de acción. Utilícelo para restricciones que no dependen de la fila, como el control de acceso basado en roles.
2. **`is_row_action_allowed_for_obj(request, name, obj)`**: Se ejecuta una vez por fila, para las acciones que superaron la primera comprobación. Utilícelo para restricciones que dependen de los datos, como ocultar el botón **Publish** en un artículo ya publicado.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView

class ArticleView(ModelView):
    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "publish" in request.state.admin_user.roles
        return await super().is_row_action_allowed(request, name)

    async def is_row_action_allowed_for_obj(
        self, request: Request, name: str, obj: Any
    ) -> bool:
        if name == "make_published":
            return not obj.is_published
        return await super().is_row_action_allowed_for_obj(request, name, obj)

```

!!! warning
    Llame siempre a `super()` para los nombres de acción que su sobrescritura no gestiona. De lo contrario, desactivará silenciosamente las comprobaciones de permisos de las acciones integradas.

## Configuración de la interfaz para las acciones de fila

### Tipos de visualización

El parámetro `row_actions_display_type` define cómo aparecen las acciones en la página de lista. Las acciones de la página de detalle siempre se muestran como botones completos.

| Tipo de visualización | Descripción                                                                       |
| --------------------- | --------------------------------------------------------------------------------- |
| `ICON_LIST`           | Muestra una lista horizontal de botones con solo iconos.                          |
| `DROPDOWN`            | Agrupa las acciones en un menú desplegable con etiqueta.                          |
| `KEBAB`               | Agrupa las acciones en un menú desplegable que se abre mediante un icono `⋮`.     |
| `INLINE_LINKS`        | Muestra la etiqueta de la acción debajo del icono, separada por un punto medio.   |

### Posicionamiento de la columna

De forma predeterminada, la columna de acciones se muestra antes de sus columnas de datos. Para moverla al lado derecho de la tabla, utilice `RowActionsPosition`:

```python
from starlette_admin.types import RowActionsPosition

class ArticleView(ModelView):
    row_actions_position = RowActionsPosition.AFTER_COLUMNS

```

## Formularios de acción dinámicos

El parámetro `form` de los decoradores `@action` y `@row_action` acepta un callable, lo que le permite generar el HTML en tiempo de solicitud.

El callable puede ser síncrono o asíncrono, y debe devolver una cadena.

- **Firma de `@action`**: `(request) -> str`
- **Firma de `@row_action`**: `(request, obj) -> str`

Utilice un callable cuando quiera rellenar previamente las entradas del formulario con los valores actuales de una fila.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.actions import ActionSelection, action, row_action
from starlette_admin.contrib.sqla import ModelView


def build_publish_form(request: Request) -> str:
    return """
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="note" placeholder="Publication note">
        </div>
    </form>
    """


def build_rename_form(request: Request, obj: Any) -> str:
    return f"""
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="title" value="{escape(obj.title)}">
        </div>
    </form>
    """


class ArticleView(ModelView):
    actions = ["make_published"]
    row_actions = ["rename", "delete"]

    @action(
        name="make_published",
        text="Publish selected",
        confirmation="Are you sure?",
        form=build_publish_form,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        pass

    @row_action(
        name="rename",
        text="Rename",
        confirmation="Rename this article?",
        form=build_rename_form,
    )
    async def rename_row_action(self, request: Request, pk: Any) -> None:
        data = await request.form()
        article = await self.find_by_pk(request, pk)
        article.title = data["title"]

```

!!! important
    El callable de formulario de una acción de fila se ejecuta una vez por fila en la página de lista. Manténgalo rápido y evite consultas a la base de datos dentro de él. Los datos de la fila que necesita ya están disponibles mediante el parámetro `obj`.
