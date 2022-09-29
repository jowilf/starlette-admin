import base64
import enum
import json
import tempfile

import pytest
import sqlalchemy_file as sf
from async_asgi_testclient import TestClient as AsyncTestClient
from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    select,
)
from sqlalchemy.orm import Session, declarative_base, relationship
from sqlalchemy_file.processors import ThumbnailGenerator
from sqlalchemy_file.storage import StorageManager
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.view import ModelView

from tests.sqla.utils import get_test_container, get_test_engine

engine = get_test_engine()
Base = declarative_base()


class Brand(str, enum.Enum):
    APPLE = "Apple"
    SAMSUNG = "Samsung"
    OPPO = "OPPO"
    HUAWEI = "Huawei"
    INFINIX = "Infinix"


class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    price = Column(Float)
    brand = Column(Enum(Brand))
    in_stock = Column(Boolean)
    image = Column(sf.ImageField(processors=[ThumbnailGenerator()]))
    user_name = Column(String(100), ForeignKey("user.name"))
    user = relationship("User", back_populates="products")


class User(Base):
    __tablename__ = "user"
    name = Column(String(100), primary_key=True)
    files = Column(sf.FileField(multiple=True))
    products = relationship("Product", back_populates="user")


class UserView(ModelView, model=User):
    form_include_pk = True


class ProductView(ModelView, model=Product):
    pass


class TestSQLABasic:
    def setup(self) -> None:
        Base.metadata.create_all(engine)
        StorageManager._clear()
        StorageManager.add_storage("test", get_test_container("test-sqla"))
        with Session(engine) as session:
            for product in json.load(open("./tests/data/products.json")):
                session.add(Product(**product))
            session.commit()

    def teardown(self):
        for obj in StorageManager.get().list_objects():
            obj.delete()
        StorageManager.get().delete()
        Base.metadata.drop_all(engine)

    @pytest.fixture
    def admin(self):
        admin = Admin(engine)
        admin.add_view(UserView)
        admin.add_view(ProductView)
        return admin

    @pytest.fixture
    def app(self, admin):
        app = Starlette()
        admin.mount_to(app)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    @pytest.fixture
    def async_client(self, app):
        return AsyncTestClient(app)

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

    @pytest.fixture
    def fake_invalid_image(self):
        file = tempfile.NamedTemporaryFile(suffix=".png")
        file.write(b"Pass through content type validation")
        file.seek(0)
        return file

    @pytest.fixture
    def fake_empty_file(self):
        file = tempfile.NamedTemporaryFile()
        file.seek(0)
        return file

    def test_base(self, admin, app, client):
        assert len(admin._views) == 2
        assert (
            app.url_path_for("admin:api:file", storage="test", file_id="test_id")
            == "/admin/api/file/test/test_id"
        )
        response = client.get("/admin/api/file/test/test_id")
        assert response.status_code == 404

    def test_api(self, client):
        response = client.get("/admin/api/product?skip=1&limit=2&order_by=title desc")
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert ["OPPOF19", "IPhone X"] == [x["title"] for x in data["items"]]
        # Find by pks
        response = client.get(
            "/admin/api/product",
            params={"pks": [x["id"] for x in data["items"]]},
        )
        assert {"OPPOF19", "IPhone X"} == {x["title"] for x in response.json()["items"]}

    def test_api_fulltext(self, client):
        response = client.get(
            "/admin/api/product?limit=-1&where=IPhone&order_by=price asc"
        )
        data = response.json()
        assert data["total"] == 2
        assert ["IPhone 9", "IPhone X"] == [x["title"] for x in data["items"]]

    def test_api_query1(self, client):
        where = (
            '{"or": [{"in_stock": {"neq": true}},{"in_stock": {"eq": false}}, {"title":'
            ' {"eq": "IPhone 9"}}, {"price": {"between": [200, 500]}}]}'
        )
        response = client.get(f"/admin/api/product?where={where}&order_by=price asc")
        data = response.json()
        assert data["total"] == 3
        assert ["OPPOF19", "Huawei P30", "IPhone 9"] == [
            x["title"] for x in data["items"]
        ]

    def test_api_query2(self, client):
        where = (
            '{"and": [{"description": {"contains": "App"}}, {"price": {"not_between":'
            " [500, 600]}}]}"
        )
        response = client.get(f"/admin/api/product?where={where}")
        data = response.json()
        assert data["total"] == 1
        assert ["IPhone X"] == [x["title"] for x in data["items"]]

    def test_api_query3(self, client):
        where = (
            '{"and": [{"description": {"not": {"endsWith": "Universe"}}}, {"title":'
            ' {"not": {"startsWith":"IPhone"}}}]}'
        )
        response = client.get(f"/admin/api/product?where={where}&order_by=price asc")
        data = response.json()
        assert data["total"] == 2
        assert ["OPPOF19", "Huawei P30"] == [x["title"] for x in data["items"]]

    def test_api_query4(self, client):
        response = client.get("/admin/api/product", params={"pks": [1, 2, 3]})
        data = response.json()
        assert data["total"] == 3
        assert sorted([x["id"] for x in data["items"]]) == [1, 2, 3]

    def test_api_query5(self, client):
        where = (
            '{"and":[{"id":{"neq":5}}],"or":[{"id":{"neq":null,"in":[0,10],"not_in":[0,10],"lt":0,'
            '"le":-1,"gt":5,"ge":6}},{"in_stock":{"eq":null}}]} '
        )
        response = client.get(f"/admin/api/product?where={where}&order_by=price asc")
        data = response.json()
        assert data["total"] == 4

    @pytest.mark.asyncio
    async def test_detail(self, async_client):
        response = await async_client.get("/admin/product/detail/1")
        assert response.status_code == 200
        response = await async_client.get("/admin/product/detail/9")
        assert response.status_code == 404

    def test_create(self, client):
        response = client.post(
            "/admin/product/create",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey – 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        with Session(engine) as session:
            stmt = select(Product).where(Product.title == "Infinix INBOOK")
            product = session.execute(stmt).scalar_one()
            assert product is not None

    def test_edit(self, client):
        data = {
            "title": "Infinix INBOOK",
            "description": (
                "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey – 1 Year Warranty"
            ),
            "price": 1049,
            "brand": "Infinix",
        }
        response = client.post(
            "/admin/product/edit/1", data=data, follow_redirects=False
        )
        assert response.status_code == 303
        with Session(engine) as session:
            product = session.get(Product, 1)
            assert product is not None
            assert product.title == data["title"]
            assert product.description == data["description"]
            assert product.price == data["price"]
            assert product.brand == data["brand"]

    def test_delete(self, client):
        response = client.delete("/admin/api/product", params={"pks": [1, 3, 5]})
        assert response.status_code == 204
        stmt = select(func.count(Product.id)).where(Product.id.in_([1, 3, 5]))
        with Session(engine) as session:
            assert session.execute(stmt).scalars().unique().all()[0] == 0

    def test_with_image(self, client, async_client, fake_image, fake_image_content):
        response = client.post(
            "/admin/product/create",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey – 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
            },
            files={"image": ("image.png", fake_image, "image/png")},
            follow_redirects=False,
        )
        assert response.status_code == 303

        with Session(engine) as session:
            stmt = select(Product).where(Product.title == "Infinix INBOOK")
            product = session.execute(stmt).scalar_one()
            assert product.image.filename == "image.png"

        # Test Serve file Api
        where = '{"id": {"eq": %d}}' % product.id
        response = client.get(f"/admin/api/product?where={where}")
        url = response.json()["items"][0]["image"]["url"]
        response = client.get(url)
        assert response.status_code == 200

        # Test editing
        fake_image.seek(0)
        response = client.post(
            f"/admin/product/edit/{product.id}",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey – 1 Year"
                    " Warranty"
                ),
                "price": "",  # None input
                "brand": "Infinix",
            },
            files={"image": ("image_edit.png", fake_image, "image/png")},
            follow_redirects=False,
        )
        assert response.status_code == 303
        with Session(engine) as session:
            stmt = select(Product).where(Product.title == "Infinix INBOOK")
            product = session.execute(stmt).scalar_one()
            assert product.image.filename == "image_edit.png"

        # Test editing without delete
        fake_image.seek(0)
        response = client.post(
            f"/admin/product/edit/{product.id}",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey – 1 Year"
                    " Warranty"
                ),
                "price": "",  # None input
                "brand": "Infinix",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303

        with Session(engine) as session:
            stmt = select(Product).where(Product.title == "Infinix INBOOK")
            product = session.execute(stmt).scalar_one()
            assert product.image.filename == "image_edit.png"

        # Test delete
        response = client.post(
            f"/admin/product/edit/{product.id}",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey – 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
                "_image-delete": "on",
            },
            follow_redirects=False,
        )
        with Session(engine) as session:
            stmt = select(Product).where(Product.title == "Infinix INBOOK")
            product = session.execute(stmt).scalar_one()
            assert product.image is None

    @pytest.mark.asyncio
    async def test_file_validation_error(
        self, async_client, fake_invalid_image, fake_empty_file
    ):
        with Session(engine) as session:
            response = await async_client.post(
                "/admin/product/create",
                files={
                    "title": "Infinix INBOOK",
                    "description": "Infinix Inbook X1 Ci3",
                    "price": "",
                    "brand": "Infinix",
                    "image": ("image.png", fake_invalid_image, "image/png"),
                },
            )
            assert response.status_code == 200
            assert (
                '<div class="invalid-feedback">Provide valid image file</div>'
                in response.text
            )
            # Test empty_file
            response = await async_client.post(
                "/admin/product/create",
                files={
                    "title": "Infinix INBOOK",
                    "description": "Infinix Inbook X1 Ci3",
                    "price": "",
                    "brand": "Infinix",
                    "image": ("image.png", fake_empty_file, "image/png"),
                },
                allow_redirects=False,
            )
            assert response.status_code == 303
            stmt = select(Product).where(Product.title == "Infinix INBOOK")
            product = session.execute(stmt).scalar_one()
            assert product.image is None

    @pytest.mark.asyncio
    async def test_relationships_and_multiple_files(
        self, client, async_client, fake_image_content, fake_empty_file
    ):
        # Test create
        response = client.post(
            "/admin/user/create",
            data={
                "name": "John",
                "products": [1, 3, 5],
            },
            files=[
                ("files", ("text1.txt", fake_image_content, "text/plain")),
                ("files", ("text2", fake_image_content, "")),
            ],
            follow_redirects=False,
        )
        assert response.status_code == 303

        with Session(engine) as session:
            stmt = select(User).where(User.name == "John")
            user = session.execute(stmt).scalar_one()
            assert [x.id for x in user.products] == [1, 3, 5]
            assert [x.filename for x in user.files] == ["text1.txt", "text2"]

        # test rendering
        response = await async_client.get("/admin/user/detail/John")
        assert response.status_code == 200

        # Test edit
        response = client.post(
            "/admin/user/edit/John",
            data={
                "name": "John",
                "products": [2, 4],
            },
            files=[
                ("files", ("new1.txt", fake_image_content, "text/plain")),
                ("files", ("new2.txt", fake_image_content, "text/plain")),
                ("files", ("new3.txt", fake_image_content, "text/plain")),
            ],
            follow_redirects=False,
        )
        assert response.status_code == 303
        with Session(engine) as session:
            stmt = select(User).where(User.name == "John")
            user = session.execute(stmt).scalar_one()
            assert [x.id for x in user.products] == [2, 4]
            assert len(user.files) == 3
            assert [x.filename for x in user.files] == [
                "new1.txt",
                "new2.txt",
                "new3.txt",
            ]

        # Test edit without delete files
        response = client.post(
            "/admin/user/edit/John",
            data={
                "name": "John",
                "products": [],
            },
            files=[
                (
                    "files",
                    ("new1.txt", fake_empty_file, "text/plain"),
                ),  # browser empty files simulation
            ],
            follow_redirects=False,
        )
        assert response.status_code == 303
        with Session(engine) as session:
            stmt = select(User).where(User.name == "John")
            user = session.execute(stmt).scalar_one()
            assert user.products == []
            assert len(user.files) == 3
            assert [x.filename for x in user.files] == [
                "new1.txt",
                "new2.txt",
                "new3.txt",
            ]

        # Test edit, delete files
        response = client.post(
            "/admin/user/edit/John",
            data={"name": "John", "products": [], "_files-delete": "on"},
            files=[
                (
                    "files",
                    ("new1.txt", fake_empty_file, "text/plain"),
                ),  # browser empty files simulation
            ],
            follow_redirects=False,
        )
        assert response.status_code == 303
        with Session(engine) as session:
            stmt = select(User).where(User.name == "John")
            user = session.execute(stmt).scalar_one()
            assert user.products == []
            assert user.files is None

        response = client.post(
            "/admin/product/create",
            data={
                "title": "Infinix INBOOK of John",
                "description": "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey",
                "price": 1049,
                "brand": "Infinix",
                "user": "John",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        with Session(engine) as session:
            stmt = select(Product).where(Product.title == "Infinix INBOOK of John")
            product = session.execute(stmt).scalar_one()
            assert product.user.name == "John"

            response = await async_client.get("/admin/api/product?pks=%d" % product.id)
            assert response.status_code == 200
