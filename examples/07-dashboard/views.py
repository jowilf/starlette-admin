from datetime import date, timedelta
from typing import Any

from models import Post, Status, User
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette_admin import (
    Breakpoints,
    CardRowWidget,
    ChartWidget,
    Col,
    ColumnWidget,
    CustomView,
    DividerWidget,
    EnumField,
    GridWidget,
    HtmlWidget,
    IntegerField,
    PanelWidget,
    StatWidget,
    TableWidget,
    TabsWidget,
    TextWidget,
)
from starlette_admin.contrib.sqla import ModelView


class UserView(ModelView):
    fields = ["id", "name", "email", "created_at", "posts"]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    form_layout = [("name", "email"), "posts"]


class PostView(ModelView):
    fields = [
        "id",
        "title",
        "body",
        EnumField("status", choices=[(s.value, s.value.title()) for s in Status]),
        IntegerField("views"),
        "created_at",
        "author",
    ]
    exclude_fields_from_list = ["body"]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    form_layout = [("title", "status", "views"), "body", "author"]


class DashboardView(CustomView):
    """Custom dashboard that aggregates data from the SQLAlchemy backend."""

    def __init__(self) -> None:
        super().__init__(
            menu_label="Dashboard",
            icon="fa fa-dashboard",
            path="/",
            add_to_menu=True,
            widget=self._build_widget,
        )

    async def _build_widget(self, request: Request) -> ColumnWidget:
        trend = await self._user_trend(request)
        data_points = trend[0]["data"] if trend else []
        growing = len(data_points) >= 2 and data_points[-1] >= data_points[-2]

        today = date.today()
        day_labels = [
            (today - timedelta(days=i)).strftime("%a %d") for i in range(6, -1, -1)
        ]
        status_labels = [s.value.title() for s in Status]

        return ColumnWidget(
            children=[
                TextWidget(
                    content=(
                        "## Welcome to the Dashboard\n\n"
                        "This page summarizes activity across **users** and **posts**. "
                        "Use the tabs below to switch between the _Overview_ summary "
                        "and in-depth _Analytics_ charts."
                    ),
                    markdown=True,
                    card=True,
                ),
                HtmlWidget(
                    html=(
                        '<div class="alert alert-info d-flex align-items-center gap-2" role="alert">'
                        '<i class="fa-solid fa-circle-info"></i>'
                        "<span>Data is queried live from SQLite. "
                        'Quick links: <a href="/admin/user/list">Users</a> &mdash; '
                        '<a href="/admin/post/list">Posts</a>.</span>'
                        "</div>"
                    )
                ),
                CardRowWidget(
                    children=[
                        Col(
                            StatWidget(
                                title="Users",
                                chart_type="area",
                                value_callback=self._count_users,
                                chart_callback=self._user_trend,
                                description=(
                                    "Growing this week"
                                    if growing
                                    else "Declining this week"
                                ),
                                description_icon=(
                                    "fa-solid fa-arrow-trend-up"
                                    if growing
                                    else "fa-solid fa-arrow-trend-down"
                                ),
                                color="success" if growing else "danger",
                                link=request.url_for("admin:list", key="user"),
                                countup=True,
                            ),
                            breakpoints=Breakpoints(default=12, md=6),
                        ),
                        Col(
                            StatWidget(
                                title="Posts",
                                chart_type="area",
                                value_callback=self._count_posts,
                                chart_callback=self._post_trend,
                                description="Last 7 days",
                                description_icon="fa-solid fa-clock",
                                color="success",
                                link=request.url_for("admin:list", key="post"),
                                countup=True,
                            ),
                            breakpoints=Breakpoints(default=12, md=6),
                        ),
                    ]
                ),
                DividerWidget(),
                TabsWidget(
                    tabs=[
                        (
                            "Overview",
                            ColumnWidget(
                                children=[
                                    CardRowWidget(
                                        children=[
                                            Col(
                                                StatWidget(
                                                    title="Total Views",
                                                    value_callback=self._total_views,
                                                    description="Across all posts",
                                                    description_icon="fa-solid fa-eye",
                                                    color="info",
                                                    countup=True,
                                                ),
                                                breakpoints=Breakpoints(
                                                    default=12, md=6, lg=3
                                                ),
                                            ),
                                            Col(
                                                StatWidget(
                                                    title="Avg Views / Post",
                                                    value_callback=self._avg_views,
                                                    description="Per published post",
                                                    description_icon="fa-solid fa-chart-bar",
                                                    color="primary",
                                                    countup=True,
                                                ),
                                                breakpoints=Breakpoints(
                                                    default=12, md=6, lg=3
                                                ),
                                            ),
                                            Col(
                                                StatWidget(
                                                    title="Drafts",
                                                    value_callback=self._count_drafts,
                                                    description="Awaiting review",
                                                    description_icon="fa-solid fa-file-pen",
                                                    color="warning",
                                                    link=request.url_for(
                                                        "admin:list", key="post"
                                                    ).include_query_params(
                                                        filter="status__eq=draft",
                                                        sort="created_at__desc",
                                                    ),
                                                    countup=True,
                                                ),
                                                breakpoints=Breakpoints(
                                                    default=12, md=6, lg=3
                                                ),
                                            ),
                                            Col(
                                                StatWidget(
                                                    title="Archived",
                                                    value_callback=self._count_archived,
                                                    description="No longer active",
                                                    description_icon="fa-solid fa-box-archive",
                                                    color="secondary",
                                                    countup=True,
                                                ),
                                                breakpoints=Breakpoints(
                                                    default=12, md=6, lg=3
                                                ),
                                            ),
                                        ]
                                    ),
                                    PanelWidget(
                                        title="Recent Activity",
                                        icon="fa-solid fa-clock",
                                        children=[
                                            CardRowWidget(
                                                children=[
                                                    Col(
                                                        TableWidget(
                                                            title="Recent Publishers",
                                                            columns=[
                                                                "Name",
                                                                "Last Publication",
                                                            ],
                                                            rows_callback=self._recent_publishers,
                                                        ),
                                                        breakpoints=Breakpoints(
                                                            default=12, lg=6
                                                        ),
                                                    ),
                                                    Col(
                                                        TableWidget(
                                                            title="Recent Published Posts",
                                                            columns=[
                                                                "Title",
                                                                "Published By",
                                                                "Date",
                                                            ],
                                                            rows_callback=self._recent_published_posts,
                                                        ),
                                                        breakpoints=Breakpoints(
                                                            default=12, lg=6
                                                        ),
                                                    ),
                                                ]
                                            )
                                        ],
                                    ),
                                    PanelWidget(
                                        title="Top Content",
                                        icon="fa-solid fa-trophy",
                                        children=[
                                            CardRowWidget(
                                                children=[
                                                    Col(
                                                        TableWidget(
                                                            title="Top Posts by Views",
                                                            columns=[
                                                                "Title",
                                                                "Author",
                                                                "Views",
                                                            ],
                                                            rows_callback=self._top_posts_by_views,
                                                        ),
                                                        breakpoints=Breakpoints(
                                                            default=12, lg=6
                                                        ),
                                                    ),
                                                    Col(
                                                        TableWidget(
                                                            title="Most Active Authors",
                                                            columns=[
                                                                "Author",
                                                                "Posts",
                                                                "Published",
                                                            ],
                                                            rows_callback=self._most_active_authors,
                                                        ),
                                                        breakpoints=Breakpoints(
                                                            default=12, lg=6
                                                        ),
                                                    ),
                                                ]
                                            )
                                        ],
                                    ),
                                    PanelWidget(
                                        title="Drafts Pending Review",
                                        icon="fa-solid fa-file-pen",
                                        collapsible=True,
                                        children=[
                                            TableWidget(
                                                title="Oldest Draft Posts",
                                                columns=["Title", "Author", "Created"],
                                                rows_callback=self._oldest_drafts,
                                            ),
                                        ],
                                    ),
                                ]
                            ),
                        ),
                        (
                            "Analytics",
                            ColumnWidget(
                                children=[
                                    PanelWidget(
                                        title="Trends",
                                        icon="fa-solid fa-chart-line",
                                        children=[
                                            GridWidget(
                                                breakpoints=Breakpoints(
                                                    default=1, md=2, lg=3
                                                ),
                                                gutter=4,
                                                children=[
                                                    ChartWidget(
                                                        title="Users - Line",
                                                        chart_type="line",
                                                        series_callback=self._user_trend,
                                                        options={
                                                            "xaxis": {
                                                                "categories": day_labels
                                                            }
                                                        },
                                                    ),
                                                    ChartWidget(
                                                        title="Posts - Area",
                                                        chart_type="area",
                                                        series_callback=self._post_trend,
                                                        options={
                                                            "xaxis": {
                                                                "categories": day_labels
                                                            }
                                                        },
                                                    ),
                                                    ChartWidget(
                                                        title="Users vs Posts - Radar",
                                                        chart_type="radar",
                                                        series_callback=self._radar_weekly,
                                                        options={
                                                            "xaxis": {
                                                                "categories": day_labels
                                                            }
                                                        },
                                                    ),
                                                ],
                                            )
                                        ],
                                    ),
                                    PanelWidget(
                                        title="Status Breakdown",
                                        icon="fa-solid fa-chart-pie",
                                        collapsible=True,
                                        children=[
                                            GridWidget(
                                                breakpoints=Breakpoints(
                                                    default=1, md=2, lg=3
                                                ),
                                                gutter=4,
                                                children=[
                                                    ChartWidget(
                                                        title="Posts by Status - Column",
                                                        chart_type="bar",
                                                        series_callback=self._status_bar_series,
                                                        options={
                                                            "xaxis": {
                                                                "categories": status_labels
                                                            }
                                                        },
                                                    ),
                                                    ChartWidget(
                                                        title="Posts by Status - Horizontal Bar",
                                                        chart_type="bar",
                                                        series_callback=self._status_bar_series,
                                                        options={
                                                            "xaxis": {
                                                                "categories": status_labels
                                                            },
                                                            "plotOptions": {
                                                                "bar": {
                                                                    "horizontal": True
                                                                }
                                                            },
                                                        },
                                                    ),
                                                    ChartWidget(
                                                        title="Posts by Status - Pie",
                                                        chart_type="pie",
                                                        series_callback=self._status_pie_series,
                                                        options={
                                                            "labels": status_labels
                                                        },
                                                    ),
                                                    ChartWidget(
                                                        title="Posts by Status - Donut",
                                                        chart_type="donut",
                                                        series_callback=self._status_pie_series,
                                                        options={
                                                            "labels": status_labels
                                                        },
                                                    ),
                                                    ChartWidget(
                                                        title="Published Rate - Gauge",
                                                        chart_type="radialBar",
                                                        series_callback=self._published_radial,
                                                        options={
                                                            "labels": ["Published"]
                                                        },
                                                    ),
                                                    ChartWidget(
                                                        title="Posts by Status - Treemap",
                                                        chart_type="treemap",
                                                        series_callback=self._treemap_status,
                                                    ),
                                                ],
                                            )
                                        ],
                                    ),
                                    PanelWidget(
                                        title="Activity Details",
                                        icon="fa-solid fa-fire",
                                        collapsible=True,
                                        collapsed=True,
                                        children=[
                                            GridWidget(
                                                breakpoints=Breakpoints(
                                                    default=1, md=2
                                                ),
                                                gutter=4,
                                                children=[
                                                    ChartWidget(
                                                        title="Post Views - Scatter",
                                                        chart_type="scatter",
                                                        series_callback=self._post_scatter,
                                                        options={
                                                            "xaxis": {
                                                                "title": {
                                                                    "text": "Post #"
                                                                }
                                                            },
                                                            "yaxis": {
                                                                "title": {
                                                                    "text": "Views"
                                                                }
                                                            },
                                                        },
                                                    ),
                                                    ChartWidget(
                                                        title="Activity - Heatmap",
                                                        chart_type="heatmap",
                                                        series_callback=self._status_heatmap,
                                                    ),
                                                ],
                                            )
                                        ],
                                    ),
                                ]
                            ),
                        ),
                    ]
                ),
            ]
        )

    # ── stat callbacks ────────────────────────────────────────────────────────

    async def _count_users(self, request: Request) -> int:
        session: Session = request.state.session
        return session.execute(select(func.count(User.id))).scalar() or 0

    async def _count_posts(self, request: Request) -> int:
        session: Session = request.state.session
        return session.execute(select(func.count(Post.id))).scalar() or 0

    async def _total_views(self, request: Request) -> int:
        session: Session = request.state.session
        return session.execute(select(func.sum(Post.views))).scalar() or 0

    async def _avg_views(self, request: Request) -> int:
        session: Session = request.state.session
        avg = session.execute(
            select(func.avg(Post.views)).where(Post.status == Status.PUBLISHED.value)
        ).scalar()
        return round(avg) if avg else 0

    async def _count_drafts(self, request: Request) -> int:
        session: Session = request.state.session
        return (
            session.execute(
                select(func.count(Post.id)).where(Post.status == Status.DRAFT.value)
            ).scalar()
            or 0
        )

    async def _count_archived(self, request: Request) -> int:
        session: Session = request.state.session
        return (
            session.execute(
                select(func.count(Post.id)).where(Post.status == Status.ARCHIVED.value)
            ).scalar()
            or 0
        )

    # ── sparkline / trend callbacks ───────────────────────────────────────────

    async def _user_trend(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        today = date.today()
        data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            count = (
                session.execute(
                    select(func.count(User.id)).where(func.date(User.created_at) == day)
                ).scalar()
                or 0
            )
            data.append(count)
        return [{"name": "New users", "data": data}]

    async def _post_trend(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        today = date.today()
        data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            count = (
                session.execute(
                    select(func.count(Post.id)).where(func.date(Post.created_at) == day)
                ).scalar()
                or 0
            )
            data.append(count)
        return [{"name": "Posts", "data": data}]

    # ── chart callbacks ───────────────────────────────────────────────────────

    async def _status_bar_series(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        counts = {s.value: 0 for s in Status}
        for status, count in session.execute(
            select(Post.status, func.count(Post.id)).group_by(Post.status)
        ).all():
            counts[status] = count
        return [{"name": "Posts", "data": [counts[s.value] for s in Status]}]

    async def _status_pie_series(self, request: Request) -> list[int]:
        session: Session = request.state.session
        counts = {s.value: 0 for s in Status}
        for status, count in session.execute(
            select(Post.status, func.count(Post.id)).group_by(Post.status)
        ).all():
            counts[status] = count
        return [counts[s.value] for s in Status]

    async def _radar_weekly(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        today = date.today()
        user_data, post_data = [], []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            user_data.append(
                session.execute(
                    select(func.count(User.id)).where(func.date(User.created_at) == day)
                ).scalar()
                or 0
            )
            post_data.append(
                session.execute(
                    select(func.count(Post.id)).where(func.date(Post.created_at) == day)
                ).scalar()
                or 0
            )
        return [
            {"name": "Users", "data": user_data},
            {"name": "Posts", "data": post_data},
        ]

    async def _post_scatter(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        posts = session.execute(select(Post.id, Post.views).order_by(Post.id)).all()
        return [
            {
                "name": "Post views",
                "data": [[i + 1, views] for i, (_, views) in enumerate(posts)],
            }
        ]

    async def _status_heatmap(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        today = date.today()
        day_labels = [
            (today - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)
        ]
        result = []
        for status in Status:
            data = []
            for i, label in zip(range(6, -1, -1), day_labels):
                day = today - timedelta(days=i)
                count = (
                    session.execute(
                        select(func.count(Post.id)).where(
                            func.date(Post.created_at) == day,
                            Post.status == status.value,
                        )
                    ).scalar()
                    or 0
                )
                data.append({"x": label, "y": count})
            result.append({"name": status.value.title(), "data": data})
        return result

    async def _published_radial(self, request: Request) -> list[float]:
        session: Session = request.state.session
        total = session.execute(select(func.count(Post.id))).scalar() or 0
        published = (
            session.execute(
                select(func.count(Post.id)).where(Post.status == Status.PUBLISHED.value)
            ).scalar()
            or 0
        )
        pct = round((published / total) * 100, 1) if total else 0.0
        return [pct]

    async def _treemap_status(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        counts = {s.value: 0 for s in Status}
        for status, count in session.execute(
            select(Post.status, func.count(Post.id)).group_by(Post.status)
        ).all():
            counts[status] = count
        return [
            {"data": [{"x": s.value.title(), "y": counts[s.value]} for s in Status]}
        ]

    # ── table callbacks ───────────────────────────────────────────────────────

    async def _recent_publishers(self, request: Request) -> list[list[Any]]:
        session: Session = request.state.session
        rows = session.execute(
            select(User.name, func.max(Post.created_at).label("last_pub"))
            .join(Post, Post.author_id == User.id)
            .where(Post.status == Status.PUBLISHED.value)
            .group_by(User.id, User.name)
            .order_by(func.max(Post.created_at).desc())
            .limit(5)
        ).all()
        return [[name, last_pub.strftime("%Y-%m-%d %H:%M")] for name, last_pub in rows]

    async def _recent_published_posts(self, request: Request) -> list[list[Any]]:
        session: Session = request.state.session
        rows = session.execute(
            select(Post.title, User.name, Post.created_at)
            .join(User, Post.author_id == User.id)
            .where(Post.status == Status.PUBLISHED.value)
            .order_by(Post.created_at.desc())
            .limit(5)
        ).all()
        return [
            [title, author, created_at.strftime("%Y-%m-%d")]
            for title, author, created_at in rows
        ]

    async def _top_posts_by_views(self, request: Request) -> list[list[Any]]:
        session: Session = request.state.session
        rows = session.execute(
            select(Post.title, User.name, Post.views)
            .join(User, Post.author_id == User.id)
            .order_by(Post.views.desc())
            .limit(5)
        ).all()
        return [[title, author, views] for title, author, views in rows]

    async def _most_active_authors(self, request: Request) -> list[list[Any]]:
        session: Session = request.state.session
        rows = session.execute(
            select(
                User.name,
                func.count(Post.id).label("total"),
                func.sum(
                    case((Post.status == Status.PUBLISHED.value, 1), else_=0)
                ).label("published"),
            )
            .join(Post, Post.author_id == User.id)
            .group_by(User.id, User.name)
            .order_by(func.count(Post.id).desc())
            .limit(5)
        ).all()
        return [[name, total, published or 0] for name, total, published in rows]

    async def _oldest_drafts(self, request: Request) -> list[list[Any]]:
        session: Session = request.state.session
        rows = session.execute(
            select(Post.title, User.name, Post.created_at)
            .join(User, Post.author_id == User.id)
            .where(Post.status == Status.DRAFT.value)
            .order_by(Post.created_at.asc())
            .limit(5)
        ).all()
        return [
            [title, author, created_at.strftime("%Y-%m-%d")]
            for title, author, created_at in rows
        ]
