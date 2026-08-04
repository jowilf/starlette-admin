import enum

import mongoengine as me
from jinja2 import Template
from markupsafe import escape
from starlette.requests import Request


class PodcastStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class EpisodeStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class HostRole(enum.Enum):
    HOST = "host"
    CO_HOST = "co_host"
    GUEST = "guest"


class Category(me.Document):
    name = me.StringField(required=True, min_length=2, max_length=50)
    color = me.StringField()
    description = me.StringField()

    meta = {"collection": "categories"}

    def __admin_repr__(self, request) -> str:
        return self.name

    def __admin_select2_repr__(self, _request: Request) -> str:
        template_str = """<span class="py-5"><span class="badge me-1" style="background-color:{{obj.color}};"></span> {{obj.name}}</span>"""
        return Template(template_str, autoescape=True).render(obj=self)

    def __str__(self) -> str:
        return self.name


class Podcast(me.Document):
    title = me.StringField(required=True, min_length=2)
    slug = me.StringField(required=True, unique=True)
    description = me.StringField()
    language = me.StringField(default="en")
    featured = me.BooleanField(default=False)
    cover = me.ImageField(thumbnail_size=(80, 80, True))
    trailer = me.FileField()
    tags = me.ListField(me.StringField())
    categories = me.ListField(me.ReferenceField(Category))
    status = me.EnumField(PodcastStatus, default=PodcastStatus.DRAFT)
    created_at = me.DateTimeField()

    meta = {"collection": "podcasts"}

    def __admin_repr__(self, request) -> str:
        return self.title

    def __admin_select2_repr__(self, request: Request) -> str:
        url = None
        if self.cover.grid_id:
            pk = getattr(self.cover, "thumbnail_id", None) or self.cover.grid_id
            url = request.url_for(
                request.app.state.ROUTE_NAME + ":api:file",
                db=self.cover.db_alias,
                col=self.cover.collection_name,
                pk=pk,
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

    def __str__(self) -> str:
        return self.title


class Host(me.Document):
    full_name = me.StringField(required=True, min_length=2)
    email = me.EmailField(required=True)
    bio = me.StringField()
    role = me.EnumField(HostRole, default=HostRole.HOST)
    joined_at = me.DateTimeField()

    meta = {"collection": "hosts"}

    def __admin_repr__(self, request) -> str:
        return self.full_name

    def __admin_select2_repr__(self, _request: Request) -> str:
        return f"<span>{escape(self.full_name)}</span>"

    def __str__(self) -> str:
        return self.full_name


class Episode(me.Document):
    podcast = me.ReferenceField(Podcast, required=True)
    host = me.ReferenceField(Host, required=True)
    title = me.StringField(required=True)
    episode_number = me.IntField(required=True, min_value=1)
    season = me.IntField(min_value=1)
    duration_minutes = me.IntField(min_value=1)
    published_at = me.DateTimeField()
    status = me.EnumField(EpisodeStatus, default=EpisodeStatus.DRAFT)
    notes = me.StringField()

    meta = {"collection": "episodes"}

    def __admin_repr__(self, request) -> str:
        return f"E{self.episode_number}: {self.title}"

    def __admin_select2_repr__(self, _request: Request) -> str:
        return f"<span>{escape(f'E{self.episode_number}: {self.title}')}</span>"

    def __str__(self) -> str:
        return f"E{self.episode_number}: {self.title}"
