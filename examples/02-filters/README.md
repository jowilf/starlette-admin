# 02: Filters

**What this demonstrates:**

- Default filter sets work out-of-the-box for every field type (`name`, `status`).
- Per-field `filters=[...]` override narrows or extends the available operations (`price`).
- `TagsField` has no default registry entry: `filters=[...]` is required to expose any filters.
- A custom `BaseFilter` subclass needs only `name`, `label`, `data_type`, and `apply` (`ActiveThisMonthFilter`).
- The filter builder serialises to bookmarkable URLs (see sample below).

## Run

```bash
cd examples/02-filters
uv run app.py
```

Then open <http://localhost:8000/admin/>.

## Key code

### Per-field filter override: `app.py`

```python
class ProductView(ModelView):
    fields = [
        StringField("name"),                       # default: contains, startswith, eq, …
        EnumField("status", enum=ProductStatus),   # default: eq, in, is_null, …
        DecimalField("price", filters=[            # override: only 3 of the 7 numeric ops
            GreaterThanFilter, BetweenFilter, NumericEqualFilter,
        ]),
        TagsField("tags", filters=[                # no default → must set explicitly
            IsNullFilter, IsNotNullFilter,
        ]),
        DateTimeField("created_at", filters=[      # built-ins + custom filter
            DateTimeBetweenFilter, DateInPastFilter, ActiveThisMonthFilter,
        ]),
    ]
```

### Custom filter: `filters.py`

```python
class ActiveThisMonthFilter(BaseFilter):
    name = "this_month"
    label = "Created this month"
    data_type = FilterDataType.NONE   # no value input needed

    def apply(self, ctx: FilterApplyContext) -> Any:
        now = datetime.utcnow()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        col = getattr(ctx.view.model, ctx.field_name)
        return col.between(start, now)
```

`data_type = NONE` tells the filter builder to render no value input for this rule.
The `apply` method returns a standalone SQLAlchemy boolean clause; it doesn't
touch `ctx.query` directly. The view combines all clauses with `and_`/`or_` before
hitting the database.

## Bookmarkable filter URLs

The filter state serialises to a compact string in the `filter` query parameter
using the format `field__operator[=value]`, with multiple rules joined by `+AND+`
or `+OR+`. Groups can be nested using parentheses. Sorting uses a separate `sort`
parameter (`field__asc` / `field__desc`).
You can copy a URL from the browser and share it: the same filter set will be
active when the link is opened.

**Example: products priced over 50, status ACTIVE:**

```
/admin/product/list?filter=price__gt=50+AND+status__eq=ACTIVE
```

**Example: products created this month, id > 15, sorted by date descending:**

```
/admin/product/list?filter=created_at__this_month+AND+id__gt=15&sort=created_at__desc
```

**Nested group: created this month, status in a set, AND a price sub-group:**

```
/admin/product/list?filter=created_at__this_month+AND+status__in=OUT_OF_STOCK,DISCONTINUED+AND+(price__gt=12+OR+price__eq=8)&sort=created_at__desc
```

## Notes

- The seed data (`seed.py`) inserts 50 products only when the database is empty,
  spread across the last ~90 days so date filters produce non-trivial result sets.
- To use Postgres or MySQL, swap the `create_engine` URL: no other changes are needed.
- To add a filter for a field type that has no registry entry (like `TagsField`),
  set `filters=[...]` on the field: any `BaseFilter` subclass with a working
  `apply()` will be accepted.
