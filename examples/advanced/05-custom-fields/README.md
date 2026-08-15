# 05: Custom Fields

This example demonstrates how to build an employee directory using SQLAlchemy and **Starlette Admin**. It specifically highlights how to create, template, and integrate custom UI fields to enhance the admin interface.

All custom field logic for this example is defined in [`fields.py`](fields.py).

## What's Inside

### Custom Fields
- **`StatusBadgeField`**: An `EnumField` subclass that renders an employee's `status` as a colored Tabler badge (e.g., green for `Online`, red for `Busy`). It overrides the default rendering on both list and detail views using its own `list_template` and `detail_template`.
- **`AvatarNameField`**: A `StringField` subclass that visually combines the employee's `name` and `avatar` image into a single column on the list view. For all other views (detail, create, edit, and export), it gracefully falls back to rendering plain text.

### Standard Fields & Configuration
- **`avatar`**: Uses an `ImageField` backed by `LocalStorage`. Uploads are automatically validated and served securely through the admin interface's own file route.
- **`department`**: Uses a standard `EnumField` restricted to a fixed set of predefined choices.

### Templating
The custom Jinja templates referenced by the custom fields (`status_badge.html` and `avatar_name.html`) are located in the `templates/employee/` directory.

## Running the Example

1. Navigate to the example directory and start the application using `uv`:

```bash
cd examples/advanced/05-custom-fields
uv run app.py
