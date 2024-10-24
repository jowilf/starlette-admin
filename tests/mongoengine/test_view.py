import base64
import datetime
import json
import tempfile
from enum import Enum
from typing import Any, Dict

import mongoengine as me
import pytest
from mongoengine import connect, disconnect
from requests import Request
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin.contrib.mongoengine import Admin, ModelView

from tests.mongoengine import MONGO_URL


class Brand(str, Enum):
    APPLE = "Apple"
    SAMSUNG = "Samsung"
    OPPO = "OPPO"
    HUAWEI = "Huawei"
    INFINIX = "Infinix"


class Product(me.Document):
    title = me.StringField(min_length=3, unique=True)
    description = me.StringField()
    price = me.DecimalField()
    brand = me.EnumField(Brand)
    manual = me.FileField()
    image = me.ImageField(thumbnail_size=(128, 128))
    created_at = me.DateTimeField(default_factory=datetime.datetime.utcnow)


class Store(me.Document):
    name = me.StringField(min_length=3)
    products = me.ListField(me.ReferenceField(Product))


class User(me.Document):
    name = me.StringField(min_length=3)
    store = me.ReferenceField("Store")


class ProductView(ModelView):
    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        assert isinstance(obj, Product)
        assert obj.id is None

    async def after_create(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None

    async def before_edit(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None

    async def after_edit(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None

    async def before_delete(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None

    async def after_delete(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None


class TestMongoBasic:
    def setup_method(self, method):
        connect(host=MONGO_URL, uuidRepresentation="standard")
        with open("./tests/data/products.json") as f:
            for product in json.load(f):
                Product(**product).save()

    def teardown_method(self, method):
        Product.drop_collection()
        Store.drop_collection()
        User.drop_collection()
        disconnect()

    @pytest.fixture
    def admin(self):
        admin = Admin()
        admin.add_view(ModelView(Store))
        admin.add_view(ProductView(Product))
        admin.add_view(ModelView(User))
        return admin

    @pytest.fixture
    def app(self, admin):
        app = Starlette()
        admin.mount_to(app)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app, base_url="http://testserver")

    @pytest.fixture
    def fake_image_content(self):
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAAHNJREFUKFOdkLEKwCAMRM/JwUFwdPb"
            "/v8RPEDcdBQcHJyUt0hQ6hGY6Li8XEhVjXM45aK3xVXNOtNagcs6LRAgB1toX23tHSgkUpEopyxhzGRw"
            "+EHljjBv03oM3KJYP1lofkJoHJs3T/4Gi1aJjxO+RPnwDur2EF1gNZukAAAAASUVORK5CYII="
        )

    @pytest.fixture
    def fake_image(self, fake_image_content):
        file = tempfile.NamedTemporaryFile(suffix=".png")
        file.write(fake_image_content)
        file.seek(0)
        return file

    def test_base(self, admin, app, client):
        assert len(admin._views) == 3
        assert (
            app.url_path_for("admin:api:file", db="db", col="col", pk="pk")
            == "/admin/api/file/db/col/pk"
        )
        response = client.get("/admin/api/file/default/fs/62fe037d39e3b3fc593094b3")
        assert response.status_code == 404

    def test_api(self, client):
        response = client.get(
            "/admin/api/product?skip=1&where={}&limit=2&order_by=title desc"
        )
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert [x["title"] for x in data["items"]] == ["OPPOF19", "IPhone X"]
        # Find by pks
        response = client.get(
            "/admin/api/product",
            params={"pks": [x["id"] for x in data["items"]]},
        )
        assert {"IPhone X", "OPPOF19"} == {x["title"] for x in response.json()["items"]}

    def test_api_fulltext(self, client):
        response = client.get(
            "/admin/api/product?limit=-1&where=IPhone&order_by=price asc"
        )
        data = response.json()
        assert data["total"] == 2
        assert [x["title"] for x in data["items"]] == ["IPhone 9", "IPhone X"]

    def test_api_query1(self, client):
        where = (
            '{"or": [{"title": {"eq": "IPhone 9"}}, {"price": {"between": [200,'
            " 500]}}]}"
        )
        response = client.get(f"/admin/api/product?where={where}&order_by=price asc")
        data = response.json()
        assert data["total"] == 3
        assert [x["title"] for x in data["items"]] == [
            "OPPOF19",
            "Huawei P30",
            "IPhone 9",
        ]

    def test_api_query2(self, client):
        where = (
            '{"and": [{"brand": {"eq": "Apple"}}, {"price": {"not_between": [500,'
            " 600]}}]}"
        )
        response = client.get(f"/admin/api/product?where={where}")
        data = response.json()
        assert data["total"] == 1
        assert [x["title"] for x in data["items"]] == ["IPhone X"]

    def test_api_query3(self, client):
        response = client.get("/admin/api/product?order_by=price desc&limit=2")
        data = response.json()
        assert data["total"] == 5
        assert [x["title"] for x in data["items"]] == ["Samsung Universe 9", "IPhone X"]

    def test_detail(self, client):
        id = Product.objects(title="IPhone 9").get().id
        response = client.get(f"/admin/product/detail/{id}")
        assert response.status_code == 200
        assert str(id) in response.text
        response = client.get("/admin/product/detail/invalid_id")
        assert response.status_code == 404

    def test_create(self, client):
        response = client.post(
            "/admin/product/create",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Product.objects.count() == 6
        assert Product.objects(title="Infinix INBOOK").get() is not None

    def test_create_validation_error(self, client):
        response = client.post(
            "/admin/product/create",
            data={
                "title": "In",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
            },
        )
        assert response.status_code == 422
        assert (
            '<div class="invalid-feedback">String value is too short</div>'
            in response.text
        )
        assert Product.objects.count() == 5
        with pytest.raises(me.DoesNotExist):
            Product.objects(brand="Infinix").get()

    def test_edit(self, client):
        id = Product.objects(title="IPhone 9").get().id
        response = client.post(
            f"/admin/product/edit/{id}",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Product.objects.count() == 5
        assert Product.objects(id=id).get().title == "Infinix INBOOK"
        with pytest.raises(me.DoesNotExist):
            Product.objects(title="IPhone 9").get()

    def test_edit_validation_error(self, client):
        id = Product.objects(title="IPhone 9").get().id
        response = client.post(
            f"/admin/product/edit/{id}",
            data={
                "title": "In",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
            },
        )
        assert response.status_code == 422
        assert (
            '<div class="invalid-feedback">String value is too short</div>'
            in response.text
        )
        assert Product.objects.count() == 5
        with pytest.raises(me.DoesNotExist):
            Product.objects(brand="Infinix").get()

    def test_delete(self, client):
        ids = [
            str(x.id)
            for x in Product.objects(title__in=["IPhone 9", "Huawei P30", "OPPOF19"])
        ]
        response = client.post(
            "/admin/api/product/action", params={"name": "delete", "pks": ids}
        )
        assert response.status_code == 200
        assert (
            Product.objects(title__in=["IPhone 9", "Huawei P30", "OPPOF19"]).count()
            == 0
        )

    def test_with_image(self, client, fake_image, fake_image_content):
        response = client.post(
            "/admin/product/create",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
            },
            files={"image": ("image.png", fake_image, "image/png")},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Product.objects.count() == 6
        assert (
            Product.objects(title="Infinix INBOOK").get().image.filename == "image.png"
        )

        # Test Serve file Api
        where = '{"title": {"eq": "Infinix INBOOK"}}'
        response = client.get(f"/admin/api/product?where={where}")
        url = response.json()["items"][0]["image"]["url"]
        response = client.get(url)
        assert response.status_code == 200

        # Test detail
        product = Product.objects(title="Infinix INBOOK").get()
        response = client.get(f"/admin/product/detail/{product.id}")
        assert response.status_code == 200
        assert (
            f'src="http://testserver/admin/api/file/default/images/{product.image.grid_id}"'
            in response.text
        )

        # Test editing
        fake_image.seek(0)
        id = Product.objects(title="Infinix INBOOK").get().id
        response = client.post(
            f"/admin/product/edit/{id}",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": "",
                "brand": "Infinix",
            },
            files={"image": ("image_edit.png", fake_image, "image/png")},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Product.objects.count() == 6
        assert (
            Product.objects(title="Infinix INBOOK").get().image.filename
            == "image_edit.png"
        )

        # Test delete
        id = Product.objects(title="Infinix INBOOK").get().id
        response = client.post(
            f"/admin/product/edit/{id}",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
                "_image-delete": "on",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Product.objects.count() == 6
        assert Product.objects(title="Infinix INBOOK").get().image.grid_id is None

    def test_relationships(self, client):
        response = client.post(
            "/admin/store/create",
            data={
                "name": "Jewelry store",
                "products": [
                    x["id"]
                    for x in Product.objects(title__in=["IPhone 9", "Huawei P30"])
                ],
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Store.objects.count() == 1
        store = Store.objects(name="Jewelry store").get()
        assert sorted(x["title"] for x in store.products) == [
            "Huawei P30",
            "IPhone 9",
        ]
        response = client.post(
            "/admin/user/create",
            data={
                "name": "John",
                "store": store.id,
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert User.objects.count() == 1
        user = User.objects(name="John").get()
        assert user.store.name == "Jewelry store"
