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

## Type

The most important property is `type` which should be unique.

```python
from starlette_admin import BaseField


class CustomField(BaseField):
    type = "custom"
```

## List Rendering

*Starlette-Admin* use [Datatables](https://datatables.net/) to render list. You need to write a javascript function to
render your column inside datatable instance. For more information on how to write your function
read [Datatables documentation](https://datatables.net/reference/option/columns.render).

Put your file inside your custom templates directory under `dt/render/`. The filename is the concatenation of
the field type and `.js`. For our example, you should create `dt/render/custom.js` and put your logic.

You can add jinja2 syntax inside your javascript function. You field intance will be available under the variable `field`

!!! example
    ```js title="dt/render/custom.js"
    dt_columns.push({
        name: "{{field.name}}",
        data: "{{field.name}}",
        orderable: columns["{{field.name}}"].orderable,
        searchBuilderType: "{{field.search_builder_type}}",
        render: function (data, type, full, meta) {
        return '<span>' + data +  '</span>';
    });
    ```
## Form

For form rendering, you should create a new html file under the directory `forms`. If you
need to add javascript function to your field, you can write a javascript function under the directory  `forms/js`.
For our example, you need to create `forms/custom.html` and if you have to write javascript function, you can
create it under `forms/js/custom.js`

These jinja2 variables are available:

* `field`: Your field instance
* `error`: Error message coming from `FormValidationError`
* `data`: Field value. Will be available if it is edit or when validation error occur
* `action`: Will be `EDIT` or `CREATE`
* `is_form_value`: True when validation error occur. This means the data are same value send 
from your input not database value.

!!! Example
    ```html title="forms/custom.html"
    <input id="{{field.name}}" name="{{field.name}}" type="{{field.input_type}}" class="form-control {%if error%}is-invalid{%endif%}"
        placeholder="{{field.label}}" value="{{data or '' }}" {%if field.required%}required{%endif%} />
    ```

    ```js title="forms/js/custom.js"
    var unique_variable_name = $("#{{field.name}}")
    // Do whatever you want
    ```

## Detail Page

To render your field on detail page, you should create a new html file under the directory `displays`. If you
need to add javascript function to your field, you can write a javascript function under the directory  `displays/js`.
For our example, you need to create `displays/custom.html` and if you have to write javascript function, you can
create it under `displays/js/custom.js`

These jinja2 variables are available:

* `field`: Your field instance
* `data`: Field value. Will be available if it is edit or when validation error occur


!!! Example
    ```html title="displays/custom.html"
    <div id="{{field.name}}">{{data}}</div>
    ```

    ```js title="displays/js/custom.js"
    $("#{{field.name}}").append(...)
    ```

