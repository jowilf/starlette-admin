from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette_admin import BaseAdmin, route
from starlette_admin.views import CustomView

from tests.utils import CsrfTestClient


class SimpleCustomView(CustomView):
    def __init__(self):
        super().__init__(menu_label="Simple", path="/simple")

    @route("/data", methods=["GET"])
    async def data_endpoint(self, request: Request) -> Response:
        return JSONResponse({"items": [1, 2, 3]})

    @route("/submit", methods=["POST"])
    async def submit_endpoint(self, request: Request) -> Response:
        form = await request.form()
        return JSONResponse({"received": form.get("name", "")})


class NestedPathCustomView(CustomView):
    def __init__(self):
        super().__init__(menu_label="Nested", path="/dashboard")

    @route("/stats/visitors", methods=["GET"])
    async def visitors(self, request: Request) -> Response:
        return JSONResponse({"visitors": 100})

    @route("/stats/hits", methods=["GET"])
    async def hits(self, request: Request) -> Response:
        return JSONResponse({"hits": 500})


class TestCustomRoutes:
    def test_extra_route_get(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(SimpleCustomView())
        admin.mount_to(app)
        client = CsrfTestClient(app)
        assert client.get("/admin/simple/data").status_code == 200
        assert client.get("/admin/simple/data").json() == {"items": [1, 2, 3]}

    def test_extra_route_post(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(SimpleCustomView())
        admin.mount_to(app)
        client = CsrfTestClient(app)
        response = client.post("/admin/simple/submit", data={"name": "test"})
        assert response.status_code == 200
        assert response.json() == {"received": "test"}

    def test_extra_route_method_not_allowed(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(SimpleCustomView())
        admin.mount_to(app)
        client = CsrfTestClient(app)
        assert client.post("/admin/simple/data").status_code == 405

    def test_extra_route_not_found(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(SimpleCustomView())
        admin.mount_to(app)
        client = CsrfTestClient(app)
        assert client.get("/admin/simple/nonexistent").status_code == 404

    def test_nested_sub_path(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(NestedPathCustomView())
        admin.mount_to(app)
        client = CsrfTestClient(app)
        assert client.get("/admin/dashboard/stats/visitors").status_code == 200
        assert client.get("/admin/dashboard/stats/visitors").json() == {"visitors": 100}
        assert client.get("/admin/dashboard/stats/hits").status_code == 200
        assert client.get("/admin/dashboard/stats/hits").json() == {"hits": 500}

    def test_primary_route_still_works(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(SimpleCustomView())
        admin.mount_to(app)
        client = CsrfTestClient(app)
        assert client.get("/admin/simple").status_code == 200

    def test_view_without_extra_routes(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(CustomView(menu_label="Plain", path="/plain"))
        admin.mount_to(app)
        client = CsrfTestClient(app)
        assert client.get("/admin/plain").status_code == 200


class RestrictedCustomView(CustomView):
    def __init__(self):
        super().__init__(menu_label="Restricted", path="/restricted")

    def is_accessible(self, request: Request) -> bool:
        return False

    @route("/data", methods=["GET"])
    async def data_endpoint(self, request: Request) -> Response:
        return JSONResponse({"items": [1, 2, 3]})


class TestCustomViewAccessibility:
    def test_primary_route_returns_403_when_not_accessible(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(RestrictedCustomView())
        admin.mount_to(app)
        client = CsrfTestClient(app)
        assert client.get("/admin/restricted").status_code == 403

    def test_extra_route_returns_403_when_not_accessible(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(RestrictedCustomView())
        admin.mount_to(app)
        client = CsrfTestClient(app)
        assert client.get("/admin/restricted/data").status_code == 403


class TestRouteDecoratorAttributes:
    def test_decorator_sets_attributes(self):
        @route("/test", methods=["POST"], name="test-route")
        async def my_handler(self, request):
            pass

        assert my_handler._route_path == "/test"
        assert my_handler._route_methods == ["POST"]
        assert my_handler._route_name == "test-route"

    def test_decorator_defaults(self):
        @route("/default")
        async def my_handler(self, request):
            pass

        assert my_handler._route_path == "/default"
        assert my_handler._route_methods == ["GET"]
        assert my_handler._route_name is None


class TestRouteNameCollision:
    def test_multiple_custom_views_with_different_routes(self):
        class ViewA(CustomView):
            @route("/data", methods=["GET"], name="view-a-data")
            async def data_endpoint(self, request: Request) -> Response:
                return JSONResponse({"view": "a"})

        class ViewB(CustomView):
            @route("/data", methods=["GET"], name="view-b-data")
            async def data_endpoint(self, request: Request) -> Response:
                return JSONResponse({"view": "b"})

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(ViewA(menu_label="View A", path="/view-a"))
        admin.add_view(ViewB(menu_label="View B", path="/view-b"))
        admin.mount_to(app)
        client = CsrfTestClient(app)

        assert client.get("/admin/view-a/data").json() == {"view": "a"}
        assert client.get("/admin/view-b/data").json() == {"view": "b"}
