# Admin Configurations 

Multiple options are available to customize your admin interface

```python
admin = Admin(
    title="SQLModel Admin",
    base_url="/admin",
    route_name="admin",
    statics_dir="statics/admin",
    templates_dir="templates/admin",
    logo_url="`https`://preview.tabler.io/static/logo-white.svg",
    login_logo_url="`https`://preview.tabler.io/static/logo.svg",
    index_view=CustomView(label="Home", icon="fa fa-home", path="/home", template_path="home.html"),
    auth_provider=MyAuthProvider(login_path="/sign-in", logout_path="/sign-out"),
    middlewares=[],
    debug=False,
)
```


## Parameters

* `title`: Admin title.
* `base_url`: Base URL for Admin interface.
* `route_name`: Mounted Admin name
* `logo_url`: URL of logo to be displayed instead of title.
* `login_logo_url`: If set, it will be used for login interface instead of logo_url.
* `statics_dir`: Templates dir for static files customisation
* `templates_dir`: Templates dir for customisation
* `index_view`: CustomView to use for index page.
* `auth_provider`: Authentication Provider
* `middlewares`: Starlette middlewares