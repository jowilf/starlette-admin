# 07: Dashboard (CustomView + SQLAlchemy)

A fully wired admin dashboard built with `CustomView` and a SQLAlchemy SQLite backend.

## What it shows

- **`CustomView` as the index page**: `DashboardView` is passed as `index_view` to `Admin`, so it replaces the default landing page.
- **`StatWidget`**: live counters with sparkline trend charts, colored indicators, and deep-links into filtered list views.
- **`ChartWidget`**: multiple chart types (line, area, radar, bar, horizontal bar, pie, donut, radialBar, treemap, scatter, heatmap) all fed by async callbacks that query SQLAlchemy directly.
- **`TableWidget`**: recent publishers, recent published posts, top posts by views, most active authors, oldest drafts.
- **`TabsWidget`**: splits the dashboard into an _Overview_ tab (stats + tables) and an _Analytics_ tab (charts).
- **`PanelWidget` with `collapsible=True` / `collapsed=True`**: panels that can be collapsed, including one pre-collapsed by default.
- **`GridWidget`**: responsive grid layout for chart groups.
- **`TextWidget` + `HtmlWidget`**: markdown intro text and a Bootstrap alert banner.
- **`DividerWidget`**: visual separator between sections.
- **Seed data**: 100 fake users with up to 5 posts each, generated once on first startup via Faker.

## Models

| Model  | Key fields                                      |
|--------|-------------------------------------------------|
| `User` | `id`, `name`, `email`, `created_at`             |
| `Post` | `id`, `title`, `body`, `status`, `views`, `created_at`, `author` |

`Status` is a `str` enum with values `draft`, `published`, `archived`.

## Run

```bash
cd examples/07-dashboard
uv run app.py
```

Then open <http://localhost:8000/admin/>.
