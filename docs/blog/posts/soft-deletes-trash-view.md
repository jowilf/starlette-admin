# Building Soft Deletes and a Trash View in FastAPI Using Starlette Admin

_2026-07-10_

A standard `DELETE` operation is unforgiving. If an operator misclicks or an automated cleanup job runs against the wrong filter, the data is gone unless you perform a complex database restore. Implementing a "soft delete" mitigates this risk by flagging a record as deleted instead of permanently removing it from the database. This approach turns data recovery into a simple update operation.

This guide demonstrates how to implement the soft delete pattern in a FastAPI application using `starlette-admin`. We will build a complete solution utilizing:

- A single database model
- Two distinct administrative views
- A `deleted_at` timestamp
- A dedicated Trash interface for restoring or permanently purging records

**View the complete runnable code:** [`examples/advanced/01-soft-delete`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/01-soft-delete).

## The Model

Add a nullable timestamp column to the table you want to protect. A `NULL` value indicates an active record, while a populated timestamp indicates a deleted record:

```python title="app.py" hl_lines="8"
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

This approach requires no separate trash table or external soft-delete mixin library. A single column manages the entire state machine.

## Hiding Deleted Rows from the Active View

The `ModelView` class builds its list, count, and detail queries using overridable methods. `get_detail_query` defaults to `get_list_query`, so filtering the list query also filters the detail page, direct URLs included. `get_count_query` is independent and must be filtered separately. By filtering these queries to include only records where `deleted_at IS NULL`, you can effectively hide soft-deleted rows from the list page, pagination counts, and direct detail links:

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

You must also exclude `deleted_at` from the create and edit forms. Operators should never set this field manually; it should only be modified programmatically by the `delete()` method and the restore action.

!!! warning
Missing `get_count_query` creates a data visibility leak: pagination and search-result totals will include deleted rows even though they do not render in the list. `get_detail_query` does not need a separate override here, since it defaults to `get_list_query` and inherits the same filter automatically. If you do give a view a custom `get_detail_query`, it stops inheriting from `get_list_query` and must filter `deleted_at` itself.

## Redefining Delete

Both the built-in batch delete action and the row-level delete button invoke `ModelView.delete()`. Overriding this method redefines the deletion behavior globally across all entry points without requiring additional configuration:

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

The `_emit_before_delete` and `_emit_after_delete` calls ensure the [event bus](../../advanced/events.md) fires exactly as it would for a hard delete. Consequently, an `AdminEvent.AFTER_DELETE` subscriber (such as an audit log or a webhook) does not need to know the deletion was soft. The impact changes at the database row level, but the lifecycle events remain consistent.

### AFTER_DELETE_COMMITTED Needs Its Own Wire

The `BEFORE_DELETE` and `AFTER_DELETE` events do not represent the complete lifecycle. The base SQLAlchemy `ModelView.delete()` method also registers an `on_commit` callback. This callback fires the `AFTER_DELETE_COMMITTED` event once the transaction successfully commits, allowing subscribers to safely assume the row is durably removed.

Because the `PostView` example completely overrides `delete()`, the default `on_commit` registration is bypassed. Consequently, a handler listening for `AdminEvent.AFTER_DELETE_COMMITTED` on a soft-deletable view will fail to fire silently.

To restore this functionality, you must manually register the same callback used by the base implementation:

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

The `_make_after_delete_committed` helper function accepts `obj` and `pk` as standard parameters. It is called once per row using that specific row's values. This structure is critical. If you built a lambda directly inside the loop body, it would close over the loop variables themselves rather than their values at that specific iteration. As a result, every callback would fire using the final values of `obj` and `pk` after the loop completes. Passing them as arguments to an outer function captures their exact state at call time.

One advantage of soft deletes applies here. A hard delete requires detaching the object (`session.expunge`) before scheduling its committed callback. Because a hard-deleted row is gone by commit time, accessing an unloaded attribute raises an `ObjectDeletedError`. Since a soft delete never removes the row, the object remains attached and all attributes are safely readable inside the callback.

However, the primary rule of `on_commit` still applies: the callback must not write to the database using `request.state.session`. That session is already complete. Anything flushed to that session starts a new transaction that is discarded when the session closes.

## A Second View for the Same Table

The `TrashView` targets the same `Post` model but registers under a unique `key`. This configuration instructs `starlette-admin` to treat it as a distinct resource with a separate URL and menu entry:

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

These queries are the exact inverse of the `PostView` queries, filtering for `IS NOT NULL` instead of `IS NULL`. `get_detail_query` again defaults to `get_list_query`, so trashed records resolve correctly on their detail page without a separate override. The `can_create` and `can_edit` methods return `False` because operators should never create or edit records directly within the trash. Records can only enter the trash via `PostView.delete()` and exit via a restore action or a permanent purge.

## Restoring, and the Case for a Real Delete

The `TrashView` retains the built-in `delete` action in its `actions` list and does not override it. Within the trash view, executing a `delete` performs a standard SQL `DELETE`. This acts as a permanent purge. Once a row is removed from the trash, it is gone entirely.

Restoring a record requires a small [custom action](../../user-guide/actions.md) that clears the `deleted_at` timestamp:

```python title="app.py" hl_lines="12"
@action(
    name="restore",
    text="Restore",
    confirmation="Restore the selected posts?",
    submit_btn_text="Yes, restore",
    submit_btn_class="btn-success",
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

Setting `deleted_at = None` immediately restores the row to the active `PostView` list on the subsequent request, as the primary view only queries for `NULL` values.

## Wiring Both Views to the Same Table

```python title="app.py" hl_lines="2"
admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Posts"))
admin.add_view(TrashView(Post, key="trash", icon="fa fa-trash"))
```

This configuration establishes two separate administrative views for a single database table. A single column dictates which view displays each specific row.

## Where This Pattern Breaks Down

- **Unique constraints:** A `UNIQUE` constraint on a field like `slug` prevents operators from recreating an active post with the same slug while the soft-deleted version remains in the trash. To resolve this, either exclude `deleted_at IS NOT NULL` rows from the unique index using a partial index (if supported by your database engine) or include the `deleted_at` column in the unique constraint itself.
- **Foreign keys:** A soft-deleted `Post` remains a valid row for foreign key relationships in other tables. Child records will continue to resolve to it. While this is often the desired behavior, cascading a soft delete to related rows requires explicit custom logic. The database will not automatically handle this the way it does with `ON DELETE CASCADE` for hard deletes.
- **Query discipline:** Every new database query targeting the `Post` model must explicitly include the `deleted_at IS NULL` filter. If a raw query, an export job, or a secondary admin view omits this filter, deleted data will leak into active workflows.
- **Database growth:** Soft-deleted rows continue to consume table and index space. If your application purges most soft-deleted rows instead of restoring them, consider implementing a scheduled background job. This job can hard-delete records older than a specific retention window to prevent unbounded database growth.

## Extending to Other Backends

The core principles of this pattern are not exclusive to SQLAlchemy. You can implement this approach on any backend that allows overriding list, count, and detail queries alongside the `delete()` method. For instance, if you are using Beanie, MongoEngine, or Tortoise ORM, the equivalent overrides will filter the query on a `deleted_at` field in the exact same manner. The specific query syntax changes, but the architectural pattern remains identical.

---

## What's Next

- **[Events](../../advanced/events.md):** Understand how `_emit_before_delete` and `_emit_after_delete` connect to external subscribers outside the view.
- **[Actions](../../user-guide/actions.md):** Explore the decorator behind `restore_action`, including how to implement confirmation dialogs and flash-message helpers.
- **[Views](../../user-guide/views.md):** Review the complete set of query and permission hooks available within `ModelView`.
