import enum
from datetime import datetime
from typing import Any

from beanie import Document, Link
from jinja2 import Template
from markupsafe import escape
from pydantic import EmailStr, Field
from starlette.requests import Request


class MembershipType(enum.StrEnum):
    BASIC = "basic"
    PREMIUM = "premium"
    STUDENT = "student"


class LoanStatus(enum.StrEnum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"


class Genre(Document):
    name: str = Field(min_length=2, max_length=50)
    color: str | None = None
    description: str | None = None

    async def __admin_repr__(self, request) -> str:
        return self.name

    async def __admin_select2_repr__(self, _request: Request) -> str:
        template_str = """<span><span class="badge me-1" style="background-color:{{obj.color}};"></span> {{obj.name}}</span>"""
        return Template(template_str, autoescape=True).render(obj=self)

    class Settings:
        name = "genres"


class Book(Document):
    title: str = Field(min_length=2)
    isbn: str = Field(min_length=10, max_length=17)
    synopsis: str | None = None
    published_year: int = Field(ge=1000, le=2100)
    page_count: int = Field(ge=1)
    total_copies: int = Field(ge=1, default=1)
    featured: bool = False
    tags: list[str] = Field(default_factory=list)
    cover: dict[str, Any] | None = None
    sample: dict[str, Any] | None = None
    genres: list[Link[Genre]] = Field(default_factory=list)
    created_at: datetime | None = None

    async def __admin_repr__(self, request) -> str:
        return self.title

    async def __admin_select2_repr__(self, request: Request) -> str:
        url = None
        if self.cover is not None:
            url = request.url_for(
                request.app.state.ROUTE_NAME + ":file",
                storage=self.cover["storage"],
                path=self.cover["key"],
            )
        template_str = (
            '<div class="d-flex align-items-center">'
            '<span class="me-2 avatar avatar-xs"'
            "{% if url %}"
            ' style="background-image: url({{url}});--tblr-avatar-size: 1.5rem;"'
            "{% else %}"
            ' style="--tblr-avatar-size: 1.5rem;"'
            "{% endif %}"
            ">{% if not url %}{{obj.title[:2]}}{% endif %}</span>"
            "{{obj.title}}"
            "</div>"
        )
        return Template(template_str, autoescape=True).render(obj=self, url=url)

    class Settings:
        name = "books"


class Member(Document):
    full_name: str = Field(min_length=2)
    email: EmailStr
    phone: str | None = None
    membership_type: MembershipType = MembershipType.BASIC
    notes: str | None = None
    joined_at: datetime | None = None

    async def __admin_repr__(self, request) -> str:
        return self.full_name

    async def __admin_select2_repr__(self, _request: Request) -> str:
        return f"<span>{escape(self.full_name)}</span>"

    class Settings:
        name = "members"


class Loan(Document):
    book: Link[Book]
    member: Link[Member]
    loan_date: datetime
    due_date: datetime
    returned_at: datetime | None = None
    status: LoanStatus = LoanStatus.ACTIVE
    notes: str | None = None

    async def __admin_repr__(self, request) -> str:
        return f"Loan #{self.id}"

    async def __admin_select2_repr__(self, _request: Request) -> str:
        return f"<span>{escape(f'Loan #{self.id}')}</span>"

    class Settings:
        name = "loans"
