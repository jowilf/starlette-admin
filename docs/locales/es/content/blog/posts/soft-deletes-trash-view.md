---
source_hash: 407757442fad75a534f382375e48ae12d4b0d56b21f2b5c4ee126b8d6ce698c7
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/blog/posts/soft-deletes-trash-view/)
<!-- translation-notice:end -->

# Eliminación lógica y una vista de papelera con FastAPI y starlette-admin

_2026-07-10_

Una operación `DELETE` estándar es implacable. Si un operador hace clic por error o un trabajo automatizado de limpieza se ejecuta con un filtro equivocado, los datos desaparecen, a menos que realice una restauración compleja de la base de datos. Implementar una eliminación lógica mitiga este riesgo al marcar un registro como eliminado en lugar de eliminarlo permanentemente de la base de datos. Este enfoque convierte la recuperación de datos en una simple operación de actualización.

Esta guía demuestra cómo implementar el patrón de eliminación lógica en una aplicación FastAPI usando `starlette-admin`. Construiremos una solución completa que utiliza:

- Un único modelo de base de datos
- Dos vistas de administración distintas
- Una marca de tiempo `deleted_at`
- Una interfaz de papelera dedicada para restaurar o purgar permanentemente registros

**Vea el código completo y ejecutable:** [`examples/advanced/01-soft-delete`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/01-soft-delete).

## El modelo

Añada una columna de marca de tiempo anulable a la tabla que desee proteger. Un valor `NULL` indica un registro activo, mientras que una marca de tiempo poblada indica un registro eliminado:

```python title="app.py" hl_lines="8"
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

Este enfoque no requiere una tabla de papelera separada ni una librería externa de mixins para la eliminación lógica. Una sola columna gestiona toda la máquina de estados.

## Ocultar filas eliminadas de la vista activa

La clase `ModelView` construye sus consultas de lista, conteo y detalle mediante métodos sobrescribibles. `get_detail_query` toma como valor predeterminado `get_list_query`, por lo que filtrar la consulta de lista también filtra la página de detalle, incluidas las URL directas. `get_count_query` es independiente y debe filtrarse por separado. Al filtrar estas consultas para incluir solo registros donde `deleted_at IS NULL`, puede ocultar eficazmente las filas con eliminación lógica de la página de lista, los conteos de paginación y los enlaces directos de detalle:

```python title="app.py" hl_lines="7-8 10-11"
class PostView(ModelView):
    exclude_fields_from_list = ["deleted_at"]
    exclude_fields_from_create = ["deleted_at", "created_at"]
    exclude_fields_from_edit = ["deleted_at", "created_at"]
    fields_default_sort = [("created_at", True)]

    def get_list_query(self, request: Request):
        return super().get_list_query(request).where(Post.deleted_at.is_(None))

    def get_count_query(self, request: Request):
        return super().get_count_query(request).where(Post.deleted_at.is_(None))
```

También debe excluir `deleted_at` de los formularios de creación y edición. Los operadores nunca deben establecer este campo manualmente; debe modificarse únicamente de manera programática mediante el método `delete()` y la acción de restauración.

!!! warning
Si falta `get_count_query`, se produce una fuga de visibilidad de datos: la paginación y los totales de resultados de búsqueda incluirán filas eliminadas aunque no se muestren en la lista. `get_detail_query` no necesita una sobrescritura separada aquí, ya que toma como valor predeterminado `get_list_query` e hereda el mismo filtro automáticamente. Si asigna a una vista un `get_detail_query` personalizado, deja de heredar de `get_list_query` y debe filtrar `deleted_at` por sí misma.

## Redefinir la eliminación

Tanto la acción integrada de eliminación por lotes como el botón de eliminación a nivel de fila invocan `ModelView.delete()`. Al sobrescribir este método, se redefine el comportamiento de eliminación globalmente en todos los puntos de entrada sin necesidad de configuración adicional:

```python title="app.py" hl_lines="6-7 11"
async def delete(self, request: Request, pks: list[Any]) -> int | None:
    session: Session = request.state.session
    objs: list[Post] = await self.find_by_pks(request, pks)
    now = datetime.utcnow()
    for obj in objs:
        await self._emit_before_delete(request, obj.id, obj)
        obj.deleted_at = now
        session.add(obj)
    session.flush()
    for obj in objs:
        await self._emit_after_delete(request, obj.id, obj)
    return len(objs)
```

Las llamadas `_emit_before_delete` y `_emit_after_delete` garantizan que el [bus de eventos](../../advanced/events.md) se active exactamente como lo haría para una eliminación física. En consecuencia, un suscriptor de `AdminEvent.AFTER_DELETE` (como un registro de auditoría o un webhook) no necesita saber que la eliminación fue lógica. El impacto cambia a nivel de fila de la base de datos, pero los eventos del ciclo de vida siguen siendo consistentes.

### AFTER_DELETE_COMMITTED necesita su propio cable

Los eventos `BEFORE_DELETE` y `AFTER_DELETE` no representan el ciclo de vida completo. El método base `ModelView.delete()` de SQLAlchemy también registra un callback `on_commit`. Este callback activa el evento `AFTER_DELETE_COMMITTED` una vez que la transacción se confirma correctamente, lo que permite a los suscriptores asumir con seguridad que la fila se ha eliminado de forma duradera.

Debido a que el ejemplo de `PostView` sobrescribe completamente `delete()`, el registro predeterminado de `on_commit` queda omitido. En consecuencia, un controlador que escuche `AdminEvent.AFTER_DELETE_COMMITTED` en una vista con eliminación lógica no se activará de forma silenciosa.

Para restaurar esta funcionalidad, debe registrar manualmente el mismo callback utilizado por la implementación base:

```python title="app.py" hl_lines="16-17 20 22"
from collections.abc import Callable

from starlette_admin.helpers import on_commit


async def delete(self, request: Request, pks: list[Any]) -> int | None:
    session: Session = request.state.session
    objs: list[Post] = await self.find_by_pks(request, pks)
    now = datetime.utcnow()
    for obj in objs:
        await self._emit_before_delete(request, obj.id, obj)
        obj.deleted_at = now
        session.add(obj)
    session.flush()

    def _make_after_delete_committed(obj: Post, pk: Any) -> Callable[[], Any]:
        return lambda: self._emit_after_delete_committed(request, pk, obj)

    for obj in objs:
        pk = obj.id
        await self._emit_after_delete(request, pk, obj)
        on_commit(request, _make_after_delete_committed(obj, pk))
    return len(objs)
```

La función auxiliar `_make_after_delete_committed` acepta `obj` y `pk` como parámetros estándar. Se llama una vez por fila utilizando los valores de esa fila específica. Esta estructura es fundamental. Si construyera una lambda directamente dentro del cuerpo del bucle, cerraría sobre las variables del bucle mismas en lugar de sobre sus valores en esa iteración concreta. Como resultado, cada callback se activaría utilizando los valores finales de `obj` y `pk` después de que el bucle termine. Pasarlos como argumentos a una función externa captura su estado exacto en el momento de la llamada.

Una ventaja de la eliminación lógica aplica aquí. Una eliminación física requiere desconectar el objeto (`session.expunge`) antes de programar su callback de confirmación. Como una fila físicamente eliminada ya no existe en el momento de la confirmación, acceder a un atributo no cargado genera un `ObjectDeletedError`. Dado que una eliminación lógica nunca elimina la fila, el objeto permanece conectado y todos sus atributos se pueden leer de forma segura dentro del callback.

Sin embargo, la regla principal de `on_commit` sigue aplicando: el callback no debe escribir en la base de datos utilizando `request.state.session`. Esa sesión ya está completa. Cualquier cosa enviada a esa sesión inicia una nueva transacción que se descarta cuando la sesión se cierra.

## Una segunda vista para la misma tabla

La `TrashView` apunta al mismo modelo `Post` pero se registra bajo una `key` única. Esta configuración instruye a `starlette-admin` a tratarla como un recurso distinto con una URL separada y una entrada de menú propia:

```python title="app.py" hl_lines="8 11"
class TrashView(ModelView):
    menu_label = "Trash"
    icon = "fa fa-trash"
    fields_default_sort = [("deleted_at", True)]
    actions = ["restore", "delete"]

    def get_list_query(self, request: Request):
        return select(Post).where(Post.deleted_at.isnot(None))

    def get_count_query(self, request: Request):
        return select(func.count()).select_from(Post).where(Post.deleted_at.isnot(None))

    def can_create(self, request: Request) -> bool:
        return False

    def can_edit(self, request: Request) -> bool:
        return False
```

Estas consultas son la inversa exacta de las consultas de `PostView`, filtrando por `IS NOT NULL` en lugar de `IS NULL`. De nuevo, `get_detail_query` toma como valor predeterminado `get_list_query`, por lo que los registros en la papelera se resuelven correctamente en su página de detalle sin una sobrescritura separada. Los métodos `can_create` y `can_edit` devuelven `False` porque los operadores nunca deben crear ni editar registros directamente dentro de la papelera. Los registros solo pueden entrar en la papelera mediante `PostView.delete()` y salir mediante una acción de restauración o una purga permanente.

## Restaurar y el caso de una eliminación real

La `TrashView` conserva la acción integrada `delete` en su lista `actions` y no la sobrescribe. Dentro de la vista de papelera, ejecutar un `delete` realiza un SQL `DELETE` estándar. Esto actúa como una purga permanente. Una vez que una fila se elimina de la papelera, desaparece por completo.

Restaurar un registro requiere una pequeña [acción personalizada](../../user-guide/actions.md) que borra la marca de tiempo `deleted_at`:

```python title="app.py" hl_lines="12"
@action(
    name="restore",
    text="Restore",
    confirmation="Restore the selected posts?",
    submit_btn_text="Yes, restore",
    submit_btn_class="btn btn-success",
)
async def restore_action(self, request: Request, pks: list[Any]) -> None:
    session: Session = request.state.session
    objs = await self.find_by_pks(request, pks)
    for obj in objs:
        obj.deleted_at = None
        session.add(obj)
    session.flush()
    count = len(objs)
    flash(request, f"{count} post{'s' if count != 1 else ''} restored.", "success")
```

Establecer `deleted_at = None` restaura inmediatamente la fila a la página de lista activa de `PostView` en la solicitud siguiente, ya que la vista principal solo consulta valores `NULL`.

## Conectar ambas vistas a la misma tabla

```python title="app.py" hl_lines="2"
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))
admin.add_view(TrashView(Post, key="trash", icon="fa fa-trash"))
```

Esta configuración establece dos vistas de administración independientes para una única tabla de base de datos. Una sola columna determina qué vista muestra cada fila específica.

## Dónde falla este patrón

- **Restricciones únicas:** una restricción `UNIQUE` sobre un campo como `slug` impide que los operadores vuelvan a crear una publicación activa con el mismo slug mientras la versión con eliminación lógica permanece en la papelera. Para resolver esto, excluya las filas con `deleted_at IS NOT NULL` del índice único mediante un índice parcial (si su motor de base de datos lo admite) o incluya la columna `deleted_at` en la propia restricción única.
- **Claves externas:** una `Post` con eliminación lógica sigue siendo una fila válida para relaciones de clave externa en otras tablas. Los registros hijos seguirán resolviéndose hacia ella. Aunque este suele ser el comportamiento deseado, propagar una eliminación lógica a filas relacionadas requiere lógica personalizada explícita. La base de datos no gestionará esto automáticamente como lo hace con `ON DELETE CASCADE` para las eliminaciones físicas.
- **Disciplina en las consultas:** toda nueva consulta de base de datos dirigida al modelo `Post` debe incluir explícitamente el filtro `deleted_at IS NULL`. Si una consulta directa, un trabajo de exportación o una vista de administración secundaria omiten este filtro, los datos eliminados se filtrarán en los flujos de trabajo activos.
- **Crecimiento de la base de datos:** las filas con eliminación lógica siguen consumiendo espacio de tabla e índices. Si su aplicación purga la mayoría de las filas con eliminación lógica en lugar de restaurarlas, considere implementar un trabajo programado en segundo plano. Este trabajo puede eliminar físicamente los registros anteriores a una ventana de retención específica para evitar un crecimiento ilimitado de la base de datos.

## Extender a otros backends

Los principios fundamentales de este patrón no son exclusivos de SQLAlchemy. Puede implementar este enfoque en cualquier backend que permita sobrescribir las consultas de lista, conteo y detalle junto con el método `delete()`. Por ejemplo, si está usando Beanie, MongoEngine u ORM Tortoise, las sobrescrituras equivalentes filtrarán la consulta por un campo `deleted_at` exactamente de la misma manera. La sintaxis específica de consulta cambia, pero el patrón arquitectónico permanece idéntico.

---

## Próximos pasos

- **[Eventos](../../advanced/events.md):** comprenda cómo `_emit_before_delete` y `_emit_after_delete` se conectan con suscriptores externos fuera de la vista.
- **[Acciones](../../user-guide/actions.md):** explore el decorador detrás de `restore_action`, incluyendo cómo implementar diálogos de confirmación y funciones auxiliares para mensajes flash.
- **[Vistas](../../user-guide/views.md):** revise el conjunto completo de hooks de consulta y permisos disponibles dentro de `ModelView`.
