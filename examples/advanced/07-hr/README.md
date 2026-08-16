# Advanced 07: HR (SQLAlchemy)

An HR admin application ported from the [Filament demo](https://github.com/filamentphp/demo), demonstrating advanced dashboarding, custom detail views, soft deletion, and inline forms.

## Key Features

* **Custom Dashboard (`HRDashboardView`):** Replaces the default index with live database queries
* **Standard Widgets:** Utilizes `StatWidget` for KPIs, `ChartWidget` for analytics grouped in a `TabsWidget`, and `TableWidget` for quick summaries.
* **Custom Org Chart:** Implements `OrgChartWidget` using [ApexTree](https://apexcharts.com/apextree/) to render interactive department hierarchies.
* **Soft Deletion:** Applies `SoftDeleteMixin` and `SoftDeleteModelView` to hide deleted `Employee` and `Project` records by stamping a `deleted_at` timestamp.
* **Custom Detail Pages:** Overrides the `details_table` Jinja block to render a profile card for Employees and status cards for Projects.
* **Menu Grouping:** Consolidates Timesheets and Leave Requests under a unified "Time & Attendance" dropdown menu.
* **Inline Editing:** Manages `ExpenseLine` records inside `Expense` forms and `Task` records inside `Project` forms.

## Running the Application

```bash
cd examples/advanced/07-hr
uv run app.py

```

Access the admin interface at [http://localhost:8000/admin/](http://localhost:8000/admin/).

## Seeding Data

Populate the database with Faker. The script generates a fixed 26-department org chart and scales related entities. By default, running the script wipes the existing SQLite file and generated avatars.

```bash
uv run seed.py                # Standard dataset
uv run seed.py --scale 5      # 5x data volume
uv run seed.py --scale 0.2    # Minimal dataset for local testing
uv run seed.py --no-reset     # Append new data without wiping the database
```
