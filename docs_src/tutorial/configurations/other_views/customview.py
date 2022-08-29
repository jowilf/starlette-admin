from starlette.requests import Request
from starlette.responses import Response
from starlette.templating import Jinja2Templates
from starlette_admin import CustomView


class ReportView(CustomView):
    label = "Report"
    icon = "fa fa-report"
    path = "/report"
    template_path = "report.html"
    name = "report"


class HomeView(CustomView):
    label = "Home"
    icon = "fa fa-home"

    async def render(self, request: Request, templates: Jinja2Templates) -> Response:
        return templates.TemplateResponse(
            "home.html", {"request": request, "latest_posts": ..., "top_users": ...}
        )
