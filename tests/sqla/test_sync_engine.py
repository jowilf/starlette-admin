import enum
import json

import pytest
import pytest_asyncio
import sqlalchemy_file as sf
from httpx import AsyncClient
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
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, relationship
from sqlalchemy_file.storage import StorageManager
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.view import ModelView

from tests.sqla.utils import get_test_container, get_test_engine

pytestmark = pytest.mark.asyncio

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
    image = Column(sf.ImageField(thumbnail_size=(128, 128)))
    user_name = Column(String(100), ForeignKey("user.name"))
    user = relationship("User", back_populates="products")


class User(Base):
    __tablename__ = "user"
    name = Column(String(100), primary_key=True)
    files = Column(sf.FileField(multiple=True))
    products = relationship("Product", back_populates="user")


class UserView(ModelView):
    form_include_pk = True


@pytest.fixture
def engine(fake_image) -> Engine:
    engine = get_test_engine()

    Base.metadata.create_all(engine)
    StorageManager._clear()
    StorageManager.add_storage("test", get_test_container("test-sqla"))
    with Session(engine) as session:
        products = []
        for _i, product in enumerate(json.load(open("./tests/data/products.json"))):
            products.append(Product(**product))
        products[0].image = sf.File(fake_image, filename="image.png")
        session.add_all(products)
        session.add(User(name="Doe", files=[sf.File("Hello", filename="hello.txt")]))
        session.commit()

    yield engine

    for obj in StorageManager.get().list_objects():
        obj.delete()
    StorageManager.get().delete()
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


@pytest.fixture
def admin(engine: Engine):
    admin = Admin(engine)
    admin.add_view(UserView(User))
    admin.add_view(ModelView(Product))
    return admin


@pytest.fixture
def app(admin: Admin):
    app = Starlette()
    admin.mount_to(app)
    return app


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://testserver") as c:
        yield c


async def test_file_serving_api(
    admin: Admin, app: Starlette, client: AsyncClient, session: Session
):
    assert len(admin._views) == 2
    assert (
        app.url_path_for("admin:api:file", storage="test", file_id="test_id")
        == "/admin/api/file/test/test_id"
    )
    response = await client.get("/admin/api/file/test/test_id")
    assert response.status_code == 404
    stmt = select(Product).where(Product.id == 1)
    path = session.execute(stmt).scalar_one().image.path
    response = await client.get("/admin/api/file/{}".format(path))
    assert response.status_code == 200


async def test_api(client: AsyncClient):
    response = await client.get(
        "/admin/api/product?skip=1&limit=2&where={}&order_by=title desc"
    )
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert ["OPPOF19", "IPhone X"] == [x["title"] for x in data["items"]]
    # Find by pks
    response = await client.get(
        "/admin/api/product",
        params={"pks": [x["id"] for x in data["items"]]},
    )
    assert {"OPPOF19", "IPhone X"} == {x["title"] for x in response.json()["items"]}


async def test_api_fulltext(client: AsyncClient):
    response = await client.get(
        "/admin/api/product?limit=-1&where=IPhone&order_by=price asc"
    )
    data = response.json()
    assert data["total"] == 2
    assert ["IPhone 9", "IPhone X"] == [x["title"] for x in data["items"]]


async def test_api_query1(client: AsyncClient):
    where = (
        '{"or": [{"in_stock": {"is_true": {}}},{"in_stock": {"is_false": {}}}, {"title":'
        ' {"eq": "IPhone 9"}}, {"price": {"between": [200, 500]}}]}'
    )
    response = await client.get(f"/admin/api/product?where={where}&order_by=price asc")
    data = response.json()
    assert data["total"] == 3
    assert ["OPPOF19", "Huawei P30", "IPhone 9"] == [x["title"] for x in data["items"]]


async def test_api_query2(client: AsyncClient):
    where = (
        '{"and": [{"description": {"contains": "App"}}, {"price": {"not_between":'
        " [500, 600]}}]}"
    )
    response = await client.get(f"/admin/api/product?where={where}")
    data = response.json()
    assert data["total"] == 1
    assert ["IPhone X"] == [x["title"] for x in data["items"]]


async def test_api_query3(client: AsyncClient):
    where = (
        '{"and": [{"description": {"not_endswith": "Universe"}}, {"title":'
        ' {"not_startswith":"IPhone"}}]}'
    )
    response = await client.get(f"/admin/api/product?where={where}&order_by=price asc")
    data = response.json()
    assert data["total"] == 2
    assert ["OPPOF19", "Huawei P30"] == [x["title"] for x in data["items"]]


async def test_api_query4(client: AsyncClient):
    response = await client.get("/admin/api/product", params={"pks": [1, 2, 3]})
    data = response.json()
    assert data["total"] == 3
    assert sorted([x["id"] for x in data["items"]]) == [1, 2, 3]


async def test_api_query5(client: AsyncClient):
    where = (
        '{"and":[{"id":{"neq":5}}],"or":[{"id":{"is_not_null":{},"in":[0,10],"not_in":[0,10],"lt":0,'
        '"le":-1,"gt":5,"ge":6}},{"in_stock":{"is_null": {}}}]} '
    )
    response = await client.get(f"/admin/api/product?where={where}&order_by=price asc")
    data = response.json()
    assert data["total"] == 4


async def test_detail(client: AsyncClient):
    response = await client.get("/admin/product/detail/1")
    assert response.status_code == 200
    response = await client.get("/admin/product/detail/9")
    assert response.status_code == 404


async def test_create(client: AsyncClient, session: Session):
    response = await client.post(
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
    stmt = select(Product).where(Product.title == "Infinix INBOOK")
    product = session.execute(stmt).scalar_one()
    assert product is not None


async def test_edit(client: AsyncClient, session: Session):
    data = {
        "title": "Infinix INBOOK",
        "description": (
            "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey – 1 Year Warranty"
        ),
        "price": 1049,
        "brand": "Infinix",
    }
    response = await client.post(
        "/admin/product/edit/1", data=data, follow_redirects=False
    )
    assert response.status_code == 303
    product = session.get(Product, 1)
    assert product is not None
    assert product.title == data["title"]
    assert product.description == data["description"]
    assert product.price == data["price"]
    assert product.brand == data["brand"]


async def test_delete(client: AsyncClient, session: Session):
    response = await client.delete("/admin/api/product", params={"pks": [1, 3, 5]})
    assert response.status_code == 204
    stmt = select(func.count(Product.id)).where(Product.id.in_([1, 3, 5]))
    assert session.execute(stmt).scalars().unique().all()[0] == 0


async def test_create_with_image(client: AsyncClient, session: Session, fake_image):
    response = await client.post(
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
    stmt = select(Product).where(Product.title == "Infinix INBOOK")
    product = session.execute(stmt).scalar_one()
    assert product.image.filename == "image.png"
    response = await client.get("/admin/api/file/{}".format(product.image.path))
    assert response.status_code == 200


async def test_edit_with_image(client: AsyncClient, session: Session, fake_image):
    response = await client.post(
        "/admin/product/edit/1",
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
    stmt = select(Product).where(Product.title == "Infinix INBOOK")
    product = session.execute(stmt).scalar_one()
    assert product.image.filename == "image_edit.png"


async def test_edit_without_delete_image(client: AsyncClient, session: Session):
    response = await client.post(
        "/admin/product/edit/1",
        data={
            "title": "Infinix INBOOK",
            "description": (
                "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey – 1 Year"
                " Warranty"
            ),
            "price": "",  # simulate null input
            "brand": "Infinix",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Product).where(Product.title == "Infinix INBOOK")
    product = session.execute(stmt).scalar_one()
    assert product.image.filename == "image.png"


async def test_delete_image(client: AsyncClient, session: Session):
    response = await client.post(
        "/admin/product/edit/1",
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
    assert response.status_code == 303
    stmt = select(Product).where(Product.id == 1)
    product = session.execute(stmt).scalar_one()
    assert product.image is None


async def test_file_validation_error(client: AsyncClient, fake_invalid_image):
    response = await client.post(
        "/admin/product/create",
        data={
            "title": "Infinix INBOOK",
            "description": "Infinix Inbook X1 Ci3",
            "price": "",
            "brand": "Infinix",
        },
        files={"image": ("image.png", fake_invalid_image, "image/png")},
    )
    assert response.status_code == 200
    assert (
        '<div class="invalid-feedback">Provide valid image file</div>' in response.text
    )


async def test_create_with_empty_file(
    client: AsyncClient, session: Session, fake_empty_file
):
    """Empty file is ignored"""
    response = await client.post(
        "/admin/product/create",
        data={
            "title": "Infinix INBOOK",
            "description": "Infinix Inbook X1 Ci3",
            "price": "",
            "brand": "Infinix",
        },
        files={"image": ("image.png", fake_empty_file, "image/png")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Product).where(Product.title == "Infinix INBOOK")
    product = session.execute(stmt).scalar_one()
    assert product.image is None


async def test_create_with_multiple_files(
    client: AsyncClient, session: Session, fake_image
):
    response = await client.post(
        "/admin/user/create",
        data={
            "name": "John",
            "products": [1, 3, 5],
        },
        files=[
            ("files", ("text1.txt", fake_image, "text/plain")),
            ("files", ("text2", fake_image, "")),
        ],
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(User).where(User.name == "John")
    user = session.execute(stmt).scalar_one()
    assert [x.id for x in user.products] == [1, 3, 5]
    assert [x.filename for x in user.files] == ["text1.txt", "text2"]

    # test rendering
    response = await client.get("/admin/user/detail/John")
    assert response.status_code == 200


async def test_edit_with_multiple_files(
    client: AsyncClient, session: Session, fake_image_content
):
    response = await client.post(
        "/admin/user/edit/Doe",
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
    stmt = select(User).where(User.name == "John")
    user = session.execute(stmt).scalar_one()
    assert [x.id for x in user.products] == [2, 4]
    assert len(user.files) == 3
    assert [x.filename for x in user.files] == [
        "new1.txt",
        "new2.txt",
        "new3.txt",
    ]


async def test_edit_without_delete_multiple_files(
    client: AsyncClient, session: Session, fake_empty_file
):
    response = await client.post(
        "/admin/user/edit/Doe",
        data={
            "name": "Doe",
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
    stmt = select(User).where(User.name == "Doe")
    user = session.execute(stmt).scalar_one()
    assert user.products == []
    assert len(user.files) == 1
    assert user.files[0].filename == "hello.txt"


async def test_edit_erase_old_files(client: AsyncClient, session: Session):
    response = await client.post(
        "/admin/user/edit/Doe",
        data={"name": "Doe", "products": [], "_files-delete": "on"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(User).where(User.name == "Doe")
    user = session.execute(stmt).scalar_one()
    assert user.products == []
    assert user.files is None


async def test_create_with_relationships(client: AsyncClient, session: Session):
    response = await client.post(
        "/admin/product/create",
        data={
            "title": "Infinix INBOOK of Doe",
            "description": "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey",
            "price": 1049,
            "brand": "Infinix",
            "user": "Doe",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Product).where(Product.title == "Infinix INBOOK of Doe")
    product = session.execute(stmt).scalar_one()
    assert product.user.name == "Doe"

    # Test rendering
    response = await client.get("/admin/api/product?pks=%d" % product.id)
    assert response.status_code == 200
