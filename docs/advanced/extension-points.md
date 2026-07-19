# Extension Points

This page provides a centralized reference for all pluggable surfaces in `starlette-admin`. Use the table below to identify the appropriate class, hook, or decorator for your use case and navigate to the in-depth documentation.

| Extension Point | API Interface / Hook | Documentation Reference |
| --- | --- | --- |
| **Custom filter** | Subclass `BaseFilter` and override `get_filter_registry()` on a `ModelView`. | [Custom Filters](custom-filters.md) |
| **Custom exporter** | Subclass `BaseExporter`. | [Export & Import](../user-guide/export-import.md) |
| **Custom importer** | Subclass `BaseImporter`. | [Export & Import](../user-guide/export-import.md) |
| **Custom theme** | Pass a `ThemeSettings` instance to `Admin(theme=...)`. | [Custom Themes](custom-themes.md) |
| **Custom authentication backend** | Subclass `BaseAuthProvider`. | [Authentication](../user-guide/auth.md) |
| **Custom file storage** | Subclass `BaseStorage` (automatically registered via its `name` attribute). | [File Storage](../user-guide/file-storage.md) |
| **Custom widget** | Subclass `BaseWidget`. | [Custom Views](../user-guide/custom-views.md) |
| **Extra routes on a custom view** | Apply the `@route("/path", methods=["GET"])` decorator to a `CustomView` method. | [Custom Views](../user-guide/custom-views.md) |

!!! note
    Unlike other extension points, themes do not rely on subclassing. `ThemeSettings` is a plain configuration object rather than a base class to extend. To customize a theme, construct an instance with your desired attribute values.

---

### Next Steps

* [Concepts](../getting-started/concepts.md): Learn how these pluggable pieces fit into the architecture of the framework as a whole.
* [Views](../user-guide/views.md): Explore the core views that most of these extension points attach to.