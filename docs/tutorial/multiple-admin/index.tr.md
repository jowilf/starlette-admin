# Çoklu Admin

Uygulamanıza farklı veya aynı görünümlere sahip birden fazla yönetim arayüzü ekleyebilirsiniz. Bunu yönetmek için, farklı `base_url` ve `route_name` kullanmanız yeterlidir.

```python
from starlette.applications import Starlette
from starlette_admin import BaseAdmin as Admin
from starlette_admin.contrib.sqla import ModelView

app = Starlette()

admin1 = Admin(
    "Admin1", base_url="/admin1", route_name="admin1", templates_dir="templates/admin1"
)
admin1.add_view(ModelView(Report))
admin1.add_view(ModelView(Post))
admin1.mount_to(app)

admin2 = Admin(
    "Admin2", base_url="/admin2", route_name="admin2", templates_dir="templates/admin2"
)
admin2.add_view(ModelView(Post))
admin2.add_view(ModelView(User))
admin2.mount_to(app)

assert app.url_path_for("admin1:index") == "/admin1/"
assert app.url_path_for("admin2:index") == "/admin2/"

```
