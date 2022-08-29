from starlette_admin.contrib.mongoengine import Admin

admin = Admin(
    title="SQLModel Admin",
    base_url="/admin",
    route_name="admin",
    templates_dir="templates/admin",
    logo_url="https://preview.tabler.io/static/logo-white.svg",
    login_logo_url="https://preview.tabler.io/static/logo.svg",
    index_view=CustomIndexView,
    auth_provider=MyAuthProvider(),
    middlewares=[],
    debug=False,
)
