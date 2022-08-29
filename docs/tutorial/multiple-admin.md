# Multiple Admin

You can add multiple admin to your app with different or same views. To handle that, just give different `base_url`
and `route_name`

```python
from starlette.applications import Starlette
from starlette_admin import BaseAdmin as Admin

app = Starlette()

admin1 = Admin(
    "Admin1", base_url="/admin1", route_name="admin1", templates_dir="templates/admin1"
)
admin1.add_view(ReportView)
admin1.add_view(PostView)
admin1.mount_to(app)

admin2 = Admin(
    "Admin2", base_url="/admin2", route_name="admin2", templates_dir="templates/admin2"
)
admin2.add_view(PostView)
admin2.add_view(UserView)
admin2.mount_to(app)

assert app.url_path_for("admin1:index") == "/admin1/"
assert app.url_path_for("admin2:index") == "/admin2/"

```