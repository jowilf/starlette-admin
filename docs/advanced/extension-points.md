---
title: Extension Points
description: An overview of all customizable hook methods, base classes, and configuration points available in starlette-admin.
---

# Extension Points

This page lists every pluggable surface in `starlette-admin` in one place. Find the class, hook, or decorator that matches what you want to change, then follow the link for the full guide.

| Extension point | API interface or hook | Documentation |
| --- | --- | --- |
| **Custom filter** | Subclass `BaseFilter` and override `get_filter_registry()` on a `ModelView`. | [Custom Filters](custom-filters.md) |
| **Custom exporter** | Subclass `BaseExporter`. | [Export and Import](../user-guide/export-import.md) |
| **Custom importer** | Subclass `BaseImporter`. | [Export and Import](../user-guide/export-import.md) |
| **Custom theme** | Subclass `BaseTheme`. | [Custom Themes](custom-themes.md) |
| **Custom authentication backend** | Subclass `BaseAuthProvider`. | [Authentication](../user-guide/auth.md) |
| **Custom file storage** | Subclass `BaseStorage`, which registers itself through its `name` attribute. | [File Storage](../user-guide/file-storage.md) |
| **Custom widget** | Subclass `BaseWidget`. | [Custom Views](../user-guide/custom-views.md) |
| **Extra routes on a custom view** | Apply the `@route("/path", methods=["GET"])` decorator to a `CustomView` method. | [Custom Views](../user-guide/custom-views.md) |
| **Plugin** | Subclass `BasePlugin` to bundle fields, views, assets, and more. | [Plugins](plugins.md) |

!!! tip
    To change the default Tabler theme colors, you don't need a custom theme. Pass a `TablerSettings` object into a `DefaultTheme` instance instead.

---

## What's next

* **[Concepts](../getting-started/concepts.md):** See how these pluggable pieces fit into the framework's architecture.
* **[Views](../user-guide/views.md):** Explore the core views that most of these extension points attach to.
