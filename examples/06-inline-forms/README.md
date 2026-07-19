# 06: Inline Forms

An admin that demonstrates three patterns for embedding related records directly inside a parent form using `InlineModelView`.

## What it shows

- **Pattern 1: Auto-detected FK** (`CommentInline` on `ArticleView`): omit `fk_attr` entirely. starlette-admin inspects the SQLAlchemy relationship on the parent model (`Article.comments`) and resolves the foreign-key column (`article_id`) automatically. Zero config needed when a relationship is defined.
- **Pattern 2: Explicit FK** (`TaskInline` on `ProjectView`): set `fk_attr = "project_id"`. Use this when auto-detection is ambiguous or when no SQLAlchemy relationship is defined between the parent and child.
- **Pattern 3: Composite FK** (`OrderLineInline` on `OrderView`): set `fk_attr = ("order_store_id", "order_seq")` when the parent has a composite primary key and the child references all of its columns. The FK columns are filled in automatically by the inline; they do not need to appear in `fields`.

Each inline also shows `extra`: the number of blank rows pre-rendered on the create/edit form (1 extra for articles and orders, 2 for projects).

## Run

```bash
cd examples/06-inline-forms
uv run app.py
```

Then open <http://localhost:8000/admin/>.

Open any Article, Project, or Order in the edit view to see the embedded inline rows. Add, edit, or delete child records (Comments, Tasks, Order Lines) and save: the parent and all its children are persisted in a single form submit.
