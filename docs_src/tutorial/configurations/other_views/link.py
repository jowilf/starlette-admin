from starlette_admin.views import Link


class StarletteAdminDocs(Link):
    label = "StarletteAdmin Docs"
    icon = "fa fa-book"
    url = "https://github.com/jowilf/starlette-admin"
    target = "_blank"
