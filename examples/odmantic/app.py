from datetime import datetime
from typing import Any, Dict, List, Optional

from odmantic import EmbeddedModel, Field, Model, Reference, SyncEngine
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.odmantic import Admin, ModelView

app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ]
)


class Author(Model):
    name: str = Field(min_length=3, max_length=100, key_name="db_name")
    age: int = Field(ge=5, lt=150)
    sex: Optional[str]
    tags: Optional[List[str]]
    dts: Optional[List[datetime]]
    float: Optional[float]
    byt: Optional[bytes]
    dic: Optional[dict]
    dict2: Optional[Dict[str, Any]]
    dt: datetime


class Book(Model):
    title: str
    pages: int
    publisher: Author = Reference()


class CapitalCity(EmbeddedModel):
    name: str = Field(min_length=3)
    population: int = Field(gt=8)
    another: Optional[bool]


class Country(Model):
    name: str
    currency: str
    tags: Optional[List[str]]
    party: datetime
    capital_city: CapitalCity


class CountryView(ModelView):
    pass


admin = Admin(SyncEngine())
admin.add_view(ModelView(Author))
admin.add_view(ModelView(Book))
admin.add_view(CountryView(Country))
# admin.add_view(AuthorView)
admin.mount_to(app)

if __name__ == "__main__":
    from faker import Faker

    fake = Faker()
    engine = SyncEngine()
    engine.remove(Country)
    countries = []
    for i in range(30):
        c = Country(
            name=fake.country(),
            currency=fake.country_code(),
            party=fake.date_time_this_year(),
            capital_city=CapitalCity(
                name=fake.city(), population=fake.pyint(100, 100000)
            ),
        )
        countries.append(c)
    engine.save_all(countries)
