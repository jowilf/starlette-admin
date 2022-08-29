# CustomView, Link and DropDown

*Starlette-Admin* come with a couple of other views to help you build a great admin backend

## CustomView

To add custom views to the Admin interface, inherit [CustomView][starlette_admin.views.CustomView]

```python
from starlette_admin import CustomView


class ReportView(CustomView):
    label = "Report"
    icon = "fa fa-report"
    path = "/report"
    template_path = "report.html"
    name = "report"
```

or override the render methods

```python
from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin import CustomView


class HomeView(CustomView):
    label = "Home"
    icon = "fa fa-home"
    path = "/home"

    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        return templates.TemplateResponse(
            "home.html", {"request": request, "latest_posts": ..., "top_users": ...}
        )

```

## Link

Display a menu with a link.
```python
from starlette_admin.views import Link


class StarletteAdminDocs(Link):
    label = "StarletteAdmin Docs"
    icon = "fa fa-book"
    url = "https://github.com/jowilf/starlette-admin"
    target = "_blank"
```

## DropDown

Group views inside a dropdown in menu structure

```python
from starlette_admin.views import DropDown

class Blog(DropDown):
    label = "Blog"
    icon = "fa fa-blog"
    views = [UserView, PostView, CommentView]
```

## Add views

When defined, you can easily add your views to admin interface

```python
admin.add_view(ReportView)
admin.add_view(StarletteAdminDocs)
admin.add_view(Blog)
```