from collections.abc import Sequence

from tortoise.models import Model


def relation_source_field(model: type[Model], field_name: str) -> str:
    """Return the database column backing a to-one relation.

    For a `ForeignKeyField` or `OneToOneField` named `author`, Tortoise
    stores the raw key in a companion column (`author_id` by default).
    Null checks and sorting must target that column: Tortoise resolves
    `author__isnull` as a nested filter on the related model and rejects it.
    """
    source = model._meta.fields_map[field_name].source_field
    assert source is not None, f"{field_name} has no source field"
    return source


def default_field_names(model: type[Model]) -> list[str]:
    """Return the model's field names to expose when a view declares no `fields`.

    Backward relations are omitted (they live on the related model's form),
    and so are the raw key columns backing to-one relations (`author_id`),
    which are already covered by their relation field (`author`).
    """
    meta = model._meta
    backward = meta.backward_fk_fields | meta.backward_o2o_fields
    raw_sources = {
        meta.fields_map[name].source_field for name in meta.fk_fields | meta.o2o_fields
    }
    return [
        name
        for name in meta.fields_map
        if name not in backward and name not in raw_sources
    ]


def build_order_clauses(
    model: type[Model], sorts: Sequence[tuple[str, str]]
) -> list[str]:
    """Convert `(field, direction)` sort pairs into Tortoise `order_by` arguments.

    To-one relation names are remapped to their raw key column, since
    ordering by the relation name itself is not supported. The direction
    string `"desc"` (case-insensitive) yields a `-` prefix; any other value
    is treated as ascending.
    """
    meta = model._meta
    clauses = []
    for name, direction in sorts:
        if name in meta.fk_fields | meta.o2o_fields:
            name = relation_source_field(model, name)  # noqa: PLW2901
        clauses.append(f"-{name}" if direction.lower() == "desc" else name)
    return clauses
