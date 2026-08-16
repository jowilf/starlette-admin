---
title: Form Layouts
description: Design complex, responsive form layouts using TabsWidget, FieldsetWidget, and grid columns in starlette-admin.
---

# Form Layouts

By default, the create and edit forms render everything in `fields` as one flat list. The `form_layout` attribute lets you arrange those inputs with the same composable widgets you use for [dashboards](../user-guide/custom-views.md): side-by-side rows, titled or collapsible panels, tabs, static content, and your own custom widgets.

## Basic usage

The simplest layout needs no widgets at all. Reference a field by its string name to keep it on its own line, and group names into a tuple to put them side by side in one row.

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

In the layout above:

* `("first_name", "last_name")` creates one row split evenly between the two inputs.
* `"email"` renders on its own line directly below.
* `("salary", "notes")` creates a second multi-column row.

You can put any number of fields in a row and mix single-column and multi-column rows freely.

Container widgets expand this shorthand themselves: `RowWidget`, `ColumnWidget`, `GridWidget`, `PanelWidget`, `FieldsetWidget`, `TabsWidget`, and `Col` all turn tuples into rows and lists into stacked columns when constructed. The shorthand therefore works inside nested `children` attributes and inside a [`CustomView.widget`](../user-guide/custom-views.md) dashboard as well.

## Grouping fields

### Titled panels

To give a group of fields a title, or to make it collapsible, wrap it in a `PanelWidget`. The widget accepts the same string and tuple shorthand as the top level.

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

`PanelWidget` takes these attributes:

| Attribute | Description |
| --- | --- |
| `title` | The heading shown in the panel's card header. |
| `children` | The widgets rendered inside the panel, in order. Accepts the shorthand above or nested widgets. Add a `TextWidget(card=False)` child to put explanatory text below the title. |
| `collapsible` | Lets people expand and collapse the panel. |
| `collapsed` | Starts the panel collapsed. Applies only when `collapsible=True`. |

For a group that needs no title, use `ColumnWidget` instead. It stacks its children vertically without wrapping them in a styled card.

### Fieldsets

`FieldsetWidget` groups fields much like `PanelWidget`, but renders a native HTML `<fieldset>` and `<legend>` instead of a styled card. Use it when you want a simpler, bordered grouping.

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

The `legend` attribute sets the caption in the `<legend>` element. `disabled=True` puts the HTML `disabled` attribute on the container, which disables every nested form control. `FieldsetWidget` supports the same `children` shorthand as `PanelWidget`, but not panel-specific options such as `collapsible` and `icon`.

## Explicit column widths

The tuple shorthand always divides a row equally. For finer control over column widths, build the row explicitly with `RowWidget`, `Col`, and `FieldRef`:

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

## Hiding field labels

Constructing a `FieldRef` explicitly gives you the `show_label` parameter, which drops the `<label>` element when the surrounding layout already makes the field's purpose obvious.

```python
from starlette_admin import FieldsetWidget, FieldRef

form_layout = [
    FieldsetWidget(legend="Email", children=[FieldRef("email", show_label=False)]),
]
```

`show_label` defaults to `True`. The string and tuple shorthands always render labels, because they take no keyword arguments.

## Input groups

The `prepend` and `append` parameters attach an [input group](https://docs.tabler.io/ui/forms/form-elements#input-group) addon to either side of an input. Each one accepts plain text or raw HTML, such as a Font Awesome icon.

```python
from starlette_admin import FieldRef

form_layout = [
    FieldRef("email", prepend="@"),
    FieldRef("phone", append='<i class="fa fa-phone"></i>'),
    FieldRef("salary", prepend="$", append="USD"),
]
```

Addons work on fields whose form template renders a native `<input>` element: `StringField`, `EmailField`, `URLField`, `PhoneField`, `PasswordField`, `ColorField`, `SlugField`, the numeric fields (`IntegerField`, `DecimalField`, `FloatField`), and the date and time fields. Other types, such as `EnumField`, `TextAreaField`, and `BooleanField`, ignore them silently.

!!! warning
    Addon values render unescaped so that HTML such as icon markup works. Pass only trusted content you wrote yourself, never user input.

## Tabs

To split sections into a tabbed interface, use `TabsWidget`. It takes a list of `(label, widgets)` pairs.

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

## Static content

Use `HtmlWidget` and `TextWidget` to render arbitrary content anywhere in the layout: instructions, warnings, or dividers.

```python
from starlette_admin import HtmlWidget, PanelWidget

form_layout = [
    HtmlWidget(html="<p class='text-warning'>Changes here are audited.</p>"),
    PanelWidget(title="Compensation", children=["salary", "notes"]),
]
```

## Custom widgets

Because `form_layout` shares the `BaseWidget` hierarchy with dashboards, you can subclass `BaseWidget` to build your own elements. That's the escape hatch for anything the built-in widgets don't cover, such as read-only previews, embedded charts, or custom macros.

See [Custom Views & Widgets](../user-guide/custom-views.md) for the general pattern, and the [Widgets API reference](../api/widgets.md) for the methods a subclass can override. Custom widgets in `form_layout` always render, whatever the field visibility rules say.

## Access control and visibility

`form_layout` respects your field-level access rules. Every `FieldRef` goes through the usual `can_access_field` check, and `exclude_from_create`, `exclude_from_edit`, and role-based permissions all stay in force.

* **Row expansion:** When a field in a multi-column row is hidden for a request, the remaining visible fields expand to fill the space.
* **Empty containers:** When every field in a container (row, panel, fieldset, column, grid, or tab) is hidden, the container is omitted, so you never get an empty shell.
* **Static rendering:** Static components such as `HtmlWidget`, `TextWidget`, and custom `BaseWidget` subclasses always render, because they don't depend on form fields.

## Handling omitted fields

A field declared in `fields` but left out of `form_layout` is appended to the bottom of the form in declaration order, so no field is ever silently lost.

Referencing the same field twice, or referencing a name that isn't in `fields`, raises a `ValueError` when the view is constructed.

---

## What's next

* **[Custom Views & Widgets](../user-guide/custom-views.md):** The widget hierarchy `form_layout` builds on, and how to write your own widget.
* **[Templates](templates.md):** Override `_form_group.html` to change the markup a layout group renders.
* **[Fields](../user-guide/fields.md):** The field types and visibility rules a layout arranges.
