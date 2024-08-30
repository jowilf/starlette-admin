# Custom Field

*Starlette-Admin* has a lot of built-in [fields][starlette_admin.fields.BaseField] available. But you can override or create your own field
according to your need.

!!! important

    Before creating a new field, try first to extend the existing ones. They are flexible enough to fit most use cases.

The first step is to define a new class, which derives from [BaseField][starlette_admin.fields.BaseField] or any others fields to customize it

```python
from starlette_admin import BaseField
from dataclasses import dataclass

@dataclass
class CustomField(BaseField):
    pass
```

## List Rendering

*Starlette-Admin* use [Datatables](https://datatables.net/) to render list. By default all fields will be render as text field.
To customize this behavior you need to write a javascript function to
render your column inside datatable instance. For more information on how to write your function
read [Datatables documentation](https://datatables.net/reference/option/columns.render).

* First, you need to provide a link to your custom javascript file in which you add additional render function, by overriding
the admin class

!!! Example

    This is simple example with SQLAlchemy backend

    ```python
    from starlette_admin.contrib.sqla import Admin as BaseAdmin

    class Admin(BaseAdmin):
        def custom_render_js(self, request: Request) -> Optional[str]:
            return request.url_for("statics", path="js/custom_render.js")

    admin = Admin(engine)
    admin.add_view(...)
    ```

    ```js title="statics/js/custom_render.js"
    Object.assign(render, {
      mycustomkey: function render(data, type, full, meta, fieldOptions) {
            ...
      },
    });
    ```

!!! note

    `fieldOptions` is your field as javascript object. Your field attributes is serialized into
    javascript object by using dataclass `asdict` function.

* Then, set `render_function_key` value

```python
from starlette_admin import BaseField
from dataclasses import dataclass

@dataclass
class CustomField(BaseField):
    render_function_key: str = "mycustomkey"
```

## Form

For form rendering, you should create a new html file under the directory `forms` in your templates dir.

These jinja2 variables are available:

* `field`: Your field instance
* `error`: Error message coming from `FormValidationError`
* `data`: current value. Will be available if it is edit or when validation error occur
* `action`: `EDIT` or `CREATE`

!!! Example

    ```html title="forms/custom.html"
    <div class="{%if error%}is-invalid{%endif%}">
        <input id="{{field.id}}" name="{{field.id}}" ... />
        {% if field.help_text %}
        <small class="form-hint">{{field.help_text}}</small>
        {%endif%}
    </div>
    {%if error %}
    <div class="invalid-feedback">{{error}}</div>
    {%endif%}
    ```

```python
from starlette_admin import BaseField
from dataclasses import dataclass

@dataclass
class CustomField(BaseField):
    render_function_key: str = "mycustomkey"
    form_template: str = "forms/custom.html"
```

## Detail Page

To render your field on detail page, you should create a new html file under the directory `displays` in your template dir.

These jinja2 variables are available:

* `field`: Your field instance
* `data`: value to display

!!! Example

    ```html title="displays/custom.html"
    <span>Hello {{data}}</span>
    ```

```python
from starlette_admin import BaseField
from dataclasses import dataclass

@dataclass
class CustomField(BaseField):
    render_function_key: str = "mycustomkey"
    form_template: str = "forms/custom.html"
    display_template: str = "displays/custom.html"
```

## Data processing

For data processing you will need to override two functions:

* `parse_form_data`:  Will be call when converting field value into python dict object
* `serialize_field_value`: Will be call when serializing value to send through the API. This is the same data
you will get in your *render* function

```python
from dataclasses import dataclass
from typing import Any, Dict

from requests import Request
from starlette.datastructures import FormData
from starlette_admin import BaseField


@dataclass
class CustomField(BaseField):
    render_function_key: str = "mycustomkey"
    form_template: str = "forms/custom.html"
    display_template: str = "displays/custom.html"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        return form_data.get(self.name)

    async def serialize_value(self, request: Request, value: Any, action: RequestAction) -> Any:
        return value

    def dict(self) -> Dict[str, Any]:
        return super().dict()

```

!!! important
    Override `dict` function to get control of the options which is available in javascript.
