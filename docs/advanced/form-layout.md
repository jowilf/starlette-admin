---
title: Form Layouts
description: Design complex, responsive form layouts using TabsWidget, FieldsetWidget, and grid columns in starlette-admin.
---

# Form Layouts

By default, the create and edit forms render every property defined in `fields` as a single, flat list. The `form_layout` attribute allows you to arrange these inputs using the same composable widgets available for [dashboards][starlette_admin.views.CustomView.widget]. You can create side-by-side rows, titled or collapsible panels, tabs, and static content. You can even integrate your own custom widgets.

## Basic Usage

The simplest layout requires no widgets at all. To keep a field on its own line, reference it by its string name. To place multiple fields side by side in a single row, group their names into a tuple.

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        ("first_name", "last_name"),
        "email",
        ("salary", "notes"),
    ]
```

In the layout defined above:

* `("first_name", "last_name")` creates a single row split evenly between the two inputs.
* `"email"` renders on its own line directly below.
* `("salary", "notes")` creates a second multi-column row.

You can place any number of fields into a single row and freely mix single-column and multi-column rows throughout your list.

This shorthand expansion is a built-in property of container widgets like `RowWidget`, `ColumnWidget`, `GridWidget`, `PanelWidget`, `FieldsetWidget`, `TabsWidget`, and `Col`. When constructed, these widgets automatically expand tuples into rows and lists into stacked columns. This means the shorthand works natively within nested `children` attributes or inside a [`CustomView.widget`][starlette_admin.views.CustomView.widget] dashboard.

## Grouping Fields

### Titled Panels

To group fields with a title or make them collapsible, wrap them in a `PanelWidget`. This widget accepts the same string and tuple shorthand as the top level.

```python
from starlette_admin import PanelWidget


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        PanelWidget(
            title="Identity",
            children=[("first_name", "last_name"), "email"],
        ),
        PanelWidget(
            title="Compensation",
            children=["salary", "notes"],
            collapsible=True,
            collapsed=True,
        ),
    ]
```

**PanelWidget Configuration**

| Attribute | Description |
| --- | --- |
| `title` | The heading shown in the panel's card header. |
| `children` | The widgets rendered inside the panel in sequence. This accepts the shorthand syntax described above or nested widgets. Use `TextWidget(card=False)` as a child element to add explanatory text below the title. |
| `collapsible` | Enables expanding and collapsing the panel in the UI. |
| `collapsed` | Sets the default state to collapsed. This is only applied when `collapsible=True`. |

For a grouped section that does not need a title, use `ColumnWidget` instead. It stacks its children vertically without wrapping them in a styled card.

### Fieldsets

The `FieldsetWidget` groups fields similarly to a `PanelWidget`, but it renders a native HTML `<fieldset>` and `<legend>` instead of a styled card. Use this for a simpler, bordered grouping.

```python
from starlette_admin import FieldsetWidget

form_layout = [
    FieldsetWidget(
        legend="Identity",
        children=[("first_name", "last_name"), "email"],
    ),
    FieldsetWidget(
        legend="Compensation",
        children=["salary", "notes"],
        disabled=True,
    ),
]
```

The `legend` attribute sets the caption shown in the `<legend>` element. Setting `disabled=True` applies the HTML `disabled` attribute to the container, disabling every nested form control. `FieldsetWidget` supports the same `children` shorthand as `PanelWidget`, but it omits panel-specific options like `collapsible` and `icon`.

## Explicit Column Widths

The tuple shorthand always divides rows equally. For granular control over column widths, build rows explicitly using `RowWidget`, `Col`, and `FieldRef`:

```python
from starlette_admin import Breakpoints, Col, FieldRef, RowWidget

form_layout = [
    RowWidget(
        children=[
            Col(FieldRef("first_name"), Breakpoints(default=12, md=4)),
            Col(FieldRef("last_name"), Breakpoints(default=12, md=8)),
        ]
    ),
]
```

## Hiding Field Labels

Constructing a `FieldRef` explicitly exposes the `show_label` parameter. This is useful for suppressing the `<label>` element when the surrounding layout already makes the field's purpose obvious.

```python
from starlette_admin import FieldsetWidget, FieldRef

form_layout = [
    FieldsetWidget(legend="Email", children=[FieldRef("email", show_label=False)]),
]
```

The `show_label` parameter defaults to `True`. The standard string and tuple shorthands always render labels because they do not accept keyword arguments.

## Input Groups

The `prepend` and `append` parameters attach an [input group](https://docs.tabler.io/ui/forms/form-elements#input-group) addon to either side of an input. Each accepts plain text or raw HTML, such as a Font Awesome icon.

```python
from starlette_admin import FieldRef

form_layout = [
    FieldRef("email", prepend="@"),
    FieldRef("phone", append='<i class="fa fa-phone"></i>'),
    FieldRef("salary", prepend="$", append="USD"),
]
```

Addons are honored by fields whose form template renders a native `<input>` element: `StringField`, `EmailField`, `URLField`, `PhoneField`, `PasswordField`, `ColorField`, `SlugField`, the numeric fields (`IntegerField`, `DecimalField`, `FloatField`), and the date and time fields. Other field types, such as `EnumField`, `TextAreaField`, and `BooleanField`, silently ignore them.

!!! warning

    Addon values are rendered unescaped so that HTML like icon markup works. Only pass trusted, developer-authored content, never user input.

## Tabs

To organize sections into a tabbed interface, use `TabsWidget`. This widget requires a list of `(label, widgets)` pairs.

```python
from starlette_admin import TabsWidget

form_layout = [
    TabsWidget(
        tabs=[
            ("Identity", [("first_name", "last_name"), "email"]),
            ("Compensation", ["salary", "notes"]),
        ]
    ),
]
```

## Static Content

You can render arbitrary content, instructions, warnings, or dividers anywhere in the layout using `HtmlWidget` and `TextWidget`.

```python
from starlette_admin import HtmlWidget, PanelWidget

form_layout = [
    HtmlWidget(html="<p class='text-warning'>Changes here are audited.</p>"),
    PanelWidget(title="Compensation", children=["salary", "notes"]),
]
```

## Custom Widgets

Because `form_layout` shares the `BaseWidget` hierarchy with dashboards, you can subclass `BaseWidget` to create custom elements. This provides an escape hatch for features not covered by built-in widgets, such as read-only previews, embedded charts, or custom macros.

Refer to [CustomView.widget][starlette_admin.views.CustomView.widget] for the general pattern. Note that custom widgets placed in `form_layout` always render, regardless of field visibility rules.

## Access Control and Visibility

The `form_layout` attribute strictly respects your existing field-level access rules. Every `FieldRef` goes through the standard `can_access_field` check. Properties like `exclude_from_create`, `exclude_from_edit`, and role-based permissions remain fully active.

* **Row Expansion:** If a field within a multi-column row is hidden during a request, the remaining visible fields automatically expand to fill the empty space.
* **Empty Containers:** If all fields within a container (row, panel, fieldset, column, grid, or tab) are hidden, the entire container is omitted to prevent empty UI elements.
* **Static Rendering:** Static components like `HtmlWidget`, `TextWidget`, or custom `BaseWidget` subclasses always render because they are independent of form fields.

## Handling Omitted Fields

If a field is declared in your primary `fields` list but omitted from `form_layout`, it is automatically appended to the bottom of the form in declaration order. This ensures fields are never silently lost.

Referencing the same field multiple times, or referencing a name that does not exist in the `fields` list, will raise a `ValueError` during view construction.
