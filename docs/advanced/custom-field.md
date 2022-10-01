# Custom Field

*Starlette-Admin* has a lot of [fields][starlette_admin.fields.BaseField] available. But you can create your own field
according to your need.

First you need to define a new class, which derives from [BaseField][starlette_admin.fields.BaseField]

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

* First, override the static file `js/render.js` and put your own function inside the `render` object

```js title="statics/js/render.js"
const render = {
    ...
    mycustomkey: function render(data, type, full, meta, fieldOptions){
        return `<span>Hello ${escape(data)}</span>`;
    }
}

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
* `action`: Will be `EDIT` or `CREATE`

!!! Example
    ```html title="forms/custom.html"
    <input id="{{field.id}}" name="{{field.id}}" type="text" class="form-control {%if error%}is-invalid{%endif%}"
        placeholder="{{field.label}}" value="{{data or '' }}" {%if field.required%}required{%endif%} />
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
    display_template = "displays/custom.html"
```

## Data processing 

For data processing you will need to override two functions:

* `process_form_data`:  Will be call when converting field value into python dict object
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
    display_template = "displays/custom.html"

    async def parse_form_data(self, request: Request, form_data: FormData) -> Any:
        return form_data.get(self.name)

    async def serialize_value(self, request: Request, value: Any, action: RequestAction) -> Any:
        return value

    def dict(self) -> Dict[str, Any]:
        return super().dict()

```


!!! important
    Override `dict` function to get control of the options which is available in javascript.