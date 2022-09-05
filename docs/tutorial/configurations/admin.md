#Admin Configurations
Multiple options are available to customise your admin interface

=== "SQLAlchemy"
    ```Python
    from sqlalchemy import create_engine
    from starlette_admin.contrib.sqla import Admin
    
    engine = create_engine("`sqlite`:///example.db")
    admin = Admin(
        engine,
        title="SQLModel Admin",
        base_url="/admin",
        route_name="admin",
        statics_dir="statics/admin",
        templates_dir="templates/admin",
        logo_url="`https`://preview.tabler.io/static/logo-white.svg",
        login_logo_url="`https`://preview.tabler.io/static/logo.svg",
        index_view=CustomIndexView,
        auth_provider=MyAuthProvider(login_path="/sign-in", logout_path="/sign-out"),
        middlewares=[],
        debug=False,
    )
    ```
=== "MongoEngine"
    ```Python
    from starlette_admin.contrib.mongoengine import Admin
    
    from starlette_admin.contrib.mongoengine import Admin
    
    admin = Admin(
        title="SQLModel Admin",
        base_url="/admin",
        route_name="admin",
        statics_dir="statics/admin",
        templates_dir="templates/admin",
        logo_url="`https`://preview.tabler.io/static/logo-white.svg",
        login_logo_url="`https`://preview.tabler.io/static/logo.svg",
        index_view=CustomIndexView,
        auth_provider=MyAuthProvider(),
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
* `index_view`: CustomView to use for index page. Default to [DefaultAdminIndexView][starlette_admin.views.DefaultAdminIndexView]
* `auth_provider`: Authentication Provider
* `middlewares`: Starlette middlewares