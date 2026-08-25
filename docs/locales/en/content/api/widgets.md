---
title: Widgets API Reference
description: Complete API reference for dashboard and form-layout widgets in starlette-admin.
---

# Widgets

Full attribute and method reference for the widget system, generated from docstrings. For a
task-oriented walkthrough, see [Custom Views & Widgets](../user-guide/custom-views.md) and
[Form Layouts](../advanced/form-layout.md).

Widgets are composable, renderable building blocks used to construct UI elements dynamically. Every widget class listed below can be imported directly from `starlette_admin`.

The widget system serves two primary roles depending on the context:

* **Dashboards & Custom Pages:** Used as the `widget` attribute of [`CustomView`](views.md#starlette_admin.views.CustomView) to build standalone interfaces and metric boards.
* **Form Layouts:** Used as the `form_layout` attribute of [`BaseModelView`](views.md#starlette_admin.views.BaseModelView) to arrange and group inputs on create/edit forms.

---

## Base Class

All widgets inherit from a common base class that defines the standard rendering and asset-collection interface.

::: starlette_admin.widgets.BaseWidget

---

## Content Widgets

Content widgets act as the leaf nodes of your UI tree. Instead of holding other widgets, they display live data. Each content widget accepts an asynchronous callback that is invoked once per request, ensuring the rendered values are always up-to-date.

::: starlette_admin.widgets.StatWidget
::: starlette_admin.widgets.ChartWidget
::: starlette_admin.widgets.TableWidget
::: starlette_admin.widgets.TextWidget
::: starlette_admin.widgets.HtmlWidget
::: starlette_admin.widgets.DividerWidget

---

## Layout Widgets

Layout widgets are containers used to arrange their `children` (which can be content widgets, form fields, or other layout widgets).

**Automatic Asset Management:** Layout widgets recursively traverse their tree to collect `additional_css_links` and `additional_js_links` from their children. This ensures that deeply nested components automatically load their required CSS/JS assets without any manual wiring.

::: starlette_admin.widgets.RowWidget
::: starlette_admin.widgets.CardRowWidget
::: starlette_admin.widgets.ColumnWidget
::: starlette_admin.widgets.GridWidget
::: starlette_admin.widgets.PanelWidget
::: starlette_admin.widgets.FieldsetWidget
::: starlette_admin.widgets.TabsWidget

---

## Responsive Sizing

Utility classes dedicated to managing responsive grid behaviors, column widths, and breakpoints across different screen sizes.

::: starlette_admin.widgets.Breakpoints
::: starlette_admin.widgets.Col

---

## Form Layout References

Specialized widgets used exclusively within the context of model forms to reference specific database fields.

::: starlette_admin.widgets.FieldRef

---

## Shorthand & Normalization

To keep your layout code clean and highly readable, container widgets accept plain Python types in place of explicit widget class instantiations. During initialization (`__post_init__`), containers automatically resolve these shorthand values into their proper widget counterparts.

**Supported Shorthands:**

* `str`: Resolves into a field reference (`FieldRef`).
* `tuple`: Resolves into a side-by-side row (`RowWidget`).
* `list`: Resolves into a vertical stack (`ColumnWidget`).

::: starlette_admin.widgets.WidgetShorthand
::: starlette_admin.widgets.normalize_widget

---

## Helpers

Utility functions for rendering widgets within Jinja2 templates or custom contexts.

::: starlette_admin.widgets.render_widget
