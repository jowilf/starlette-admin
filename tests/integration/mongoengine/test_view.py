import base64
import datetime
import json
import re
import tempfile
from enum import StrEnum
from typing import Any

import mongoengine as me
import pytest
from mongoengine import connect, disconnect
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin import StringField
from starlette_admin.contrib.mongoengine import Admin, ModelView

from tests.utils import CsrfTestClient


class Brand(StrEnum):
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
    sku = me.StringField(default="server-sku")


class Store(me.Document):
    name = me.StringField(min_length=3)
    products = me.ListField(me.ReferenceField(Product))


class User(me.Document):
    name = me.StringField(min_length=3)
    store = me.ReferenceField("Store")


class ProductView(ModelView):
    fields = [
        "id",
        "title",
        "description",
        "price",
        "brand",
        "manual",
        "image",
        "created_at",
        StringField("sku", read_only=True),
    ]

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        assert isinstance(obj, Product)
        assert obj.id is None

    async def after_create(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None

    async def before_edit(
        self, request: Request, data: dict[str, Any], obj: Any
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


def _list_total(html: str) -> int:
    m = re.search(r"Showing \d+ to \d+ of (\d+)", html)
    return int(m.group(1)) if m else 0


class TestMongoBasic:
    @pytest.fixture(autouse=True)
    def _db(self, mongo_url):
        connect(host=mongo_url, uuidRepresentation="standard")
        with open("./tests/data/products.json") as f:
            for product in json.load(f):
                Product(**product).save()
        yield
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
        return CsrfTestClient(app, base_url="http://testserver")

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

    def test_list(self, client):
        response = client.get("/admin/product/list")
        assert response.status_code == 200
        assert _list_total(response.text) == 5

    def test_list_fulltext(self, client):
        response = client.get("/admin/product/list", params={"q": "IPhone"})
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    def test_list_sort(self, client):
        response = client.get("/admin/product/list", params={"sort": "title__desc"})
        assert response.status_code == 200
        assert _list_total(response.text) == 5

    def test_list_find_by_pks_select2(self, client):
        pks = [str(x.id) for x in Product.objects(title__in=["IPhone 9", "Huawei P30"])]
        response = client.get(
            "/admin/_api/product/relation-lookup", params={"pks": pks}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    def test_detail(self, client):
        id = Product.objects(title="IPhone 9").get().id
        response = client.get(f"/admin/product/detail?pk={id}")
        assert response.status_code == 200
        assert str(id) in response.text
        response = client.get("/admin/product/detail?pk=invalid_id")
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
            f"/admin/product/edit?pk={id}",
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
            f"/admin/product/edit?pk={id}",
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

    def test_create_ignores_read_only_field(self, client):
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
                # The SKU is read-only; a submitted value must be ignored in favor
                # of the field's default.
                "sku": "hacked-sku",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        product = Product.objects(title="Infinix INBOOK").get()
        assert product.sku == "server-sku"

    def test_edit_ignores_read_only_field(self, client):
        id = Product.objects(title="IPhone 9").get().id
        response = client.post(
            f"/admin/product/edit?pk={id}",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
                # The SKU is read-only; attempting to change it via the edit form
                # must have no effect.
                "sku": "hacked-sku",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        product = Product.objects(id=id).get()
        assert product.title == "Infinix INBOOK"
        assert product.sku == "server-sku"

    def test_delete(self, client):
        ids = [
            str(x.id)
            for x in Product.objects(title__in=["IPhone 9", "Huawei P30", "OPPOF19"])
        ]
        response = client.post(
            "/admin/_api/product/action", params={"name": "delete", "pks": ids}
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
        product = Product.objects(title="Infinix INBOOK").get()
        assert product.image.filename == "image.png"
        assert product.image.thumbnail_id is not None

        # Test the Serve file API.
        url = (
            f"/admin/api/file/{product.image.db_alias}"
            f"/{product.image.collection_name}/{product.image.grid_id}"
        )
        response = client.get(url)
        assert response.status_code == 200

        # Test that the detail page renders the image.
        response = client.get(f"/admin/product/detail?pk={product.id}")
        assert response.status_code == 200
        assert (
            f'src="http://testserver/admin/api/file/default/images/{product.image.grid_id}"'
            in response.text
        )

        # Test that the list page renders the image thumbnail.
        response = client.get("/admin/product/list")
        assert response.status_code == 200
        assert (
            f"http://testserver/admin/api/file/default/images/{product.image.thumbnail_id}"
            in response.text
        )

        # Test that editing replaces the image.
        fake_image.seek(0)
        response = client.post(
            f"/admin/product/edit?pk={product.id}",
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

        # Test deleting the image using the delete checkbox.
        product_id = Product.objects(title="Infinix INBOOK").get().id
        response = client.post(
            f"/admin/product/edit?pk={product_id}",
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
                    str(x.id)
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
                "store": str(store.id),
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert User.objects.count() == 1
        user = User.objects(name="John").get()
        assert user.store.name == "Jewelry store"


class TestMongoFilters:
    """Filter system integration tests for the MongoEngine backend.

    Filter strings use the custom `field__op=value` syntax (see
    `BaseModelView._parse_filter_string`):
      - `field__op=value`: single rule
      - `field__op`: rule with no value (e.g., `is_null`)
      - `field__between=lo..hi`: range (lo and hi separated by `..`)
      - `field__in=v1,v2`: list (comma-separated)
      - `r1 AND r2`, `r1 OR r2`: combine two rules
      - `(AND r1 r2) OR r3`: nested groups
      - Values with spaces must be double-quoted: `title__eq="IPhone 9"`
    """

    @pytest.fixture(autouse=True)
    def _db(self, mongo_url):
        connect(host=mongo_url, uuidRepresentation="standard")
        past = datetime.datetime(2024, 1, 1)
        with open("./tests/data/products.json") as f:
            for product in json.load(f):
                Product(**product, created_at=past).save()
        yield
        Product.drop_collection()
        disconnect()

    @pytest.fixture
    def client(self):
        admin = Admin()
        admin.add_view(ProductView(Product))
        app = Starlette()
        admin.mount_to(app)
        return CsrfTestClient(app, base_url="http://testserver")

    def test_filter_string_contains(self, client):
        response = client.get(
            "/admin/product/list", params={"filter": "title__contains=IPhone"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    def test_filter_string_not_contains(self, client):
        response = client.get(
            "/admin/product/list", params={"filter": "title__not_contains=IPhone"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 3

    def test_filter_string_startswith(self, client):
        response = client.get(
            "/admin/product/list", params={"filter": "title__startswith=IPhone"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    def test_filter_string_endswith(self, client):
        # "IPhone 9", "Samsung Universe 9", and "OPPOF19" all end with "9".
        response = client.get(
            "/admin/product/list", params={"filter": "title__endswith=9"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 3

    def test_filter_string_eq(self, client):
        response = client.get(
            "/admin/product/list", params={"filter": 'title__eq="IPhone 9"'}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1

    def test_filter_string_neq(self, client):
        response = client.get(
            "/admin/product/list", params={"filter": 'title__neq="IPhone 9"'}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 4

    def test_filter_numeric_gt(self, client):
        # price > 500: IPhone 9 (549), IPhone X (899), Samsung Universe 9 (1249).
        response = client.get("/admin/product/list", params={"filter": "price__gt=500"})
        assert response.status_code == 200
        assert _list_total(response.text) == 3

    def test_filter_numeric_lt(self, client):
        # price < 500: OPPOF19 (280), Huawei P30 (499).
        response = client.get("/admin/product/list", params={"filter": "price__lt=500"})
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    def test_filter_numeric_gte(self, client):
        # price >= 549: IPhone 9 (549), IPhone X (899), Samsung Universe 9 (1249).
        response = client.get(
            "/admin/product/list", params={"filter": "price__gte=549"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 3

    def test_filter_numeric_lte(self, client):
        # price <= 499: OPPOF19 (280), Huawei P30 (499).
        response = client.get(
            "/admin/product/list", params={"filter": "price__lte=499"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    def test_filter_numeric_between(self, client):
        # 500 <= price <= 900: IPhone 9 (549), IPhone X (899).
        response = client.get(
            "/admin/product/list", params={"filter": "price__between=500..900"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    def test_filter_numeric_eq(self, client):
        response = client.get("/admin/product/list", params={"filter": "price__eq=549"})
        assert response.status_code == 200
        assert _list_total(response.text) == 1

    def test_filter_null_checks(self, client):
        # The description is set for all test products; none are null.
        response = client.get(
            "/admin/product/list", params={"filter": "description__is_null"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 0

        response = client.get(
            "/admin/product/list", params={"filter": "description__is_not_null"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 5

    def test_filter_enum_eq(self, client):
        response = client.get(
            "/admin/product/list", params={"filter": "brand__eq=Apple"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    def test_filter_enum_in(self, client):
        response = client.get(
            "/admin/product/list", params={"filter": "brand__in=Apple,Samsung"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 3

    def test_filter_enum_not_in(self, client):
        response = client.get(
            "/admin/product/list", params={"filter": "brand__not_in=Apple,Samsung"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    def test_filter_or_group(self, client):
        # brand == OPPO OR price > 1000: OPPOF19 + Samsung Universe 9.
        response = client.get(
            "/admin/product/list",
            params={"filter": "brand__eq=OPPO OR price__gt=1000"},
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    def test_filter_and_group(self, client):
        # brand == Apple AND price > 600: only IPhone X (899).
        response = client.get(
            "/admin/product/list",
            params={"filter": "brand__eq=Apple AND price__gt=600"},
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1

    def test_filter_combined_with_fulltext_search(self, client):
        # q=IPhone filters titles; brand__eq=Apple narrows to Apple only → 2 results.
        response = client.get(
            "/admin/product/list",
            params={"q": "IPhone", "filter": "brand__eq=Apple"},
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    def test_filter_nested_groups(self, client):
        # (brand == Apple AND price > 600) OR brand == Samsung.
        # → IPhone X (Apple, 899) + Samsung Universe 9.
        response = client.get(
            "/admin/product/list",
            params={
                "filter": "(brand__eq=Apple AND price__gt=600) OR brand__eq=Samsung"
            },
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    def test_filter_datetime_in_past(self, client):
        # All products have a 'created_at' timestamp set in the past.
        response = client.get(
            "/admin/product/list", params={"filter": "created_at__in_past"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 5

    def test_filter_datetime_in_future(self, client):
        # No products have a future 'created_at' timestamp.
        response = client.get(
            "/admin/product/list", params={"filter": "created_at__in_future"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 0

    def test_filter_objectid_eq(self, client):
        target_id = str(Product.objects(title="IPhone 9").get().id)
        response = client.get(
            "/admin/product/list", params={"filter": f"id__eq={target_id}"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1

    def test_filter_objectid_in(self, client):
        ids = ",".join(
            str(p.id) for p in Product.objects(title__in=["IPhone 9", "Huawei P30"])
        )
        response = client.get("/admin/product/list", params={"filter": f"id__in={ids}"})
        assert response.status_code == 200
        assert _list_total(response.text) == 2
