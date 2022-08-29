from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///example.db")
admin = Admin(
    engine,
    title="SQLModel Admin",
    base_url="/admin",
    route_name="admin",
    templates_dir="templates/admin",
    logo_url="https://preview.tabler.io/static/logo-white.svg",
    login_logo_url="https://preview.tabler.io/static/logo.svg",
    index_view=CustomIndexView,
    auth_provider=MyAuthProvider(login_path="/sign-in", logout_path="/sign-out"),
    middlewares=[],
    debug=False,
)
