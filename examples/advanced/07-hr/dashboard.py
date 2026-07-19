"""
07-hr: dashboard index view.

`HRDashboardView` replaces the admin's default index page with an HR
dashboard built from the stock widget set (StatWidget, ChartWidget,
TableWidget, TabsWidget, ...) plus one custom widget defined here:
`OrgChartWidget`, which renders the department hierarchy with ApexTree,
the organizational chart library from the ApexCharts team.

`OrgChartWidget` is the reference for writing your own widget: subclass
`BaseWidget`, point `template` at a file under the app's `templates_dir`
(see `templates/widgets/org_chart_widget.html`), return template variables
from `get_context`, and declare vendor scripts in `additional_js_links` so
the page injects them once, after the built-in bundles.

Every number on the page is queried live from the request's SQLAlchemy
session. Aggregates that bucket rows by month or year rely on SQLite's
`strftime`; port those expressions if you move the example to another
database.
"""

from calendar import monthrange
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from typing import Any, ClassVar
from uuid import uuid4

from models import (
    Department,
    Employee,
    EmploymentType,
    Expense,
    ExpenseCategory,
    ExpenseStatus,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    Project,
    ProjectStatus,
    Task,
    TaskPriority,
    TaskStatus,
    Timesheet,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette_admin import (
    Breakpoints,
    CardRowWidget,
    ChartWidget,
    Col,
    ColumnWidget,
    CustomView,
    GridWidget,
    HtmlWidget,
    PanelWidget,
    StatWidget,
    TableWidget,
    TabsWidget,
    TextWidget,
)
from starlette_admin.widgets import BaseWidget

# Pinned to 1.3.0 on purpose: it is the last release without a license
# gate, so the chart renders without an ApexCharts watermark. The API used
# here (contentKey, nodeTemplate, per node nodeBGColor) is stable across
# 1.x, so bumping the version only requires a license key, not new code.
APEXTREE_JS = "https://cdn.jsdelivr.net/npm/apextree@1.3.0/apextree.min.js"

# Colorblind safe categorical palette, assigned to series in this fixed
# order. Validated for adjacent pair CVD separation on a white card surface.
CATEGORICAL = [
    "#2a78d6",  # blue
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
    "#e87ba4",  # magenta
    "#eb6834",  # orange
]

# Status colors mirror the semantics of the Tabler badges used in the list
# views: green for settled good states, amber for waiting states, red for
# rejections, gray for inert states, blue and violet for informative ones.
GOOD = "#0ca30c"
WARNING = "#fab219"
CRITICAL = "#d03b3b"
NEUTRAL = "#9ca3af"
INFO = "#2a78d6"
ACCENT = "#4a3aa7"

LEAVE_STATUS_COLORS = {
    LeaveStatus.PENDING: WARNING,
    LeaveStatus.APPROVED: GOOD,
    LeaveStatus.REJECTED: CRITICAL,
    LeaveStatus.TAKEN: INFO,
    LeaveStatus.CANCELLED: NEUTRAL,
}

PROJECT_STATUS_COLORS = {
    ProjectStatus.PLANNING: NEUTRAL,
    ProjectStatus.ACTIVE: GOOD,
    ProjectStatus.ON_HOLD: WARNING,
    ProjectStatus.COMPLETED: INFO,
    ProjectStatus.CANCELLED: CRITICAL,
}

TASK_STATUS_COLORS = {
    TaskStatus.BACKLOG: NEUTRAL,
    TaskStatus.TODO: INFO,
    TaskStatus.IN_PROGRESS: WARNING,
    TaskStatus.IN_REVIEW: ACCENT,
    TaskStatus.COMPLETED: GOOD,
    TaskStatus.CANCELLED: CRITICAL,
}

TASK_PRIORITY_COLORS = {
    TaskPriority.LOW: NEUTRAL,
    TaskPriority.MEDIUM: INFO,
    TaskPriority.HIGH: WARNING,
    TaskPriority.CRITICAL: CRITICAL,
}

EXPENSE_STATUS_COLORS = {
    ExpenseStatus.DRAFT: NEUTRAL,
    ExpenseStatus.SUBMITTED: WARNING,
    ExpenseStatus.APPROVED: GOOD,
    ExpenseStatus.REJECTED: CRITICAL,
    ExpenseStatus.REIMBURSED: INFO,
}


def _title(value: str) -> str:
    """Human readable label for an enum value, e.g. "in_progress" -> "In Progress"."""
    return value.replace("_", " ").title()


def _fmt_money(value: Any) -> str:
    """Compact dollar amount for cards and org chart nodes, e.g. "$1.2M"."""
    amount = float(value or 0)
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:.0f}"


def _last_months(count: int) -> list[tuple[str, str]]:
    """The last `count` calendar months, oldest first.

    Returns (key, label) pairs where `key` matches SQLite's
    `strftime('%Y-%m', ...)` output and `label` is a short axis caption.
    """
    year, month = date.today().year, date.today().month
    months: list[tuple[str, str]] = []
    for _ in range(count):
        months.append(
            (f"{year:04d}-{month:02d}", date(year, month, 1).strftime("%b %y"))
        )
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    months.reverse()
    return months


# ── Custom widget: ApexTree organization chart ───────────────────────────────


@dataclass
class OrgChartWidget(BaseWidget):
    """Renders a hierarchy as an interactive ApexTree organization chart.

    The widget is data source agnostic: `tree_callback` returns the nested
    node structure ApexTree consumes. Each node needs an `id`, a `children`
    list, and a `data` payload with the strings the node card displays
    (`name`, `people`, `budget`, and a `color` used as the card background).

    Args:
        title: Card heading.
        tree_callback: Async callable returning the root node of the tree.
        height: Canvas height in pixels.
        direction: Direction the tree grows from the root:
            "top", "bottom", "left", or "right".
        node_width: Width of a node card in pixels.
        node_height: Height of a node card in pixels.
    """

    template: ClassVar[str] = "widgets/org_chart_widget.html"

    title: str
    tree_callback: Callable[[Request], Awaitable[dict[str, Any]]]
    height: int = 620
    direction: str = "top"
    node_width: int = 176
    node_height: int = 76

    def additional_js_links(self, request: Request) -> list[str]:
        return [APEXTREE_JS]

    async def get_context(self, request: Request) -> dict[str, Any]:
        tree = await self.tree_callback(request)
        return {
            "widget": self,
            "title": self.title,
            "chart_id": f"org-chart-{uuid4().hex[:8]}",
            "tree": tree,
            "height": self.height,
            "direction": self.direction,
            "node_width": self.node_width,
            "node_height": self.node_height,
        }


# ── Dashboard view ───────────────────────────────────────────────────────────


class HRDashboardView(CustomView):
    """Admin index page: KPI cards, the org chart, and tabbed analytics.

    The widget tree is rebuilt on every request (`widget` is a callable),
    so headline descriptions can be computed from the same live queries
    that feed the charts.
    """

    def __init__(self) -> None:
        super().__init__(
            menu_label="Dashboard",
            icon="fa fa-gauge-high",
            path="/",
            add_to_menu=True,
            widget=self._build_widget,
        )

    async def _build_widget(self, request: Request) -> ColumnWidget:
        session: Session = request.state.session
        today = date.today()

        hires = await self._hires_sparkline(request)
        hire_counts = hires[0]["data"]
        hiring_up = len(hire_counts) >= 2 and hire_counts[-1] >= hire_counts[-2]

        total_projects = session.scalar(
            select(func.count(Project.id)).where(Project.deleted_at.is_(None))
        )
        pending_expense_total = session.scalar(
            select(func.coalesce(func.sum(Expense.total_amount), 0)).where(
                Expense.status == ExpenseStatus.SUBMITTED
            )
        )
        salaried = session.scalar(
            select(func.count(Employee.id)).where(
                Employee.deleted_at.is_(None), Employee.salary.is_not(None)
            )
        )
        billable_this_month = session.scalar(
            select(func.coalesce(func.sum(Timesheet.hours), 0)).where(
                func.strftime("%Y-%m", Timesheet.date) == today.strftime("%Y-%m"),
                Timesheet.is_billable.is_(True),
            )
        )

        month_labels = [label for _, label in _last_months(12)]
        division_names = self._division_names(session)
        month_start = today.replace(day=1)
        month_end = today.replace(day=monthrange(today.year, today.month)[1])

        def stat_col(widget: StatWidget) -> Col:
            return Col(widget, breakpoints=Breakpoints(default=12, md=6, lg=3))

        return ColumnWidget(
            children=[
                TextWidget(
                    content=(
                        "## HR Overview\n\n"
                        "Live snapshot of the workforce, projects, time tracking, "
                        "and spend. Every figure is queried from the database on "
                        "each page load; follow a card to drill into the "
                        "underlying records."
                    ),
                    markdown=True,
                    card=True,
                ),
                HtmlWidget(
                    html=(
                        '<div class="alert alert-info d-flex align-items-center gap-2" role="alert">'
                        '<i class="fa-solid fa-circle-info"></i>'
                        "<span>Quick links: "
                        f'<a href="{request.url_for("admin:list", key="employee")}">Employees</a> &middot; '
                        f'<a href="{request.url_for("admin:list", key="project")}">Projects</a> &middot; '
                        f'<a href="{request.url_for("admin:list", key="leave-request")}">Leave requests</a> &middot; '
                        f'<a href="{request.url_for("admin:list", key="expense")}">Expenses</a>'
                        "</span></div>"
                    )
                ),
                CardRowWidget(
                    children=[
                        stat_col(
                            StatWidget(
                                title="Employees",
                                value_callback=self._count_employees,
                                chart_type="area",
                                chart_callback=self._hires_sparkline,
                                description=(
                                    "Hiring is up this month"
                                    if hiring_up
                                    else "Hiring slowed this month"
                                ),
                                description_icon=(
                                    "fa-solid fa-arrow-trend-up"
                                    if hiring_up
                                    else "fa-solid fa-arrow-trend-down"
                                ),
                                color="success" if hiring_up else "warning",
                                link=request.url_for("admin:list", key="employee"),
                                countup=True,
                            )
                        ),
                        stat_col(
                            StatWidget(
                                title="Active Projects",
                                value_callback=self._count_active_projects,
                                description=f"of {total_projects} projects overall",
                                description_icon="fa-solid fa-diagram-project",
                                color="primary",
                                link=request.url_for(
                                    "admin:list", key="project"
                                ).include_query_params(filter="status__eq=active"),
                                countup=True,
                            )
                        ),
                        stat_col(
                            StatWidget(
                                title="Pending Leave",
                                value_callback=self._count_pending_leave,
                                description="requests awaiting review",
                                description_icon="fa-solid fa-hourglass-half",
                                color="warning",
                                link=request.url_for(
                                    "admin:list", key="leave-request"
                                ).include_query_params(filter="status__eq=pending"),
                                countup=True,
                            )
                        ),
                        stat_col(
                            StatWidget(
                                title="Open Tasks",
                                value_callback=self._count_open_tasks,
                                description="in backlog, progress, or review",
                                description_icon="fa-solid fa-list-check",
                                color="info",
                                link=request.url_for(
                                    "admin:list", key="task"
                                ).include_query_params(
                                    filter="status__in=backlog,todo,in_progress,in_review"
                                ),
                                countup=True,
                            )
                        ),
                    ]
                ),
                CardRowWidget(
                    children=[
                        stat_col(
                            StatWidget(
                                title="Annual Payroll",
                                value_callback=self._annual_payroll,
                                description=f"across {salaried} salaried employees",
                                description_icon="fa-solid fa-money-check-dollar",
                                color="primary",
                            )
                        ),
                        stat_col(
                            StatWidget(
                                title="Hours This Month",
                                value_callback=self._hours_this_month,
                                chart_type="area",
                                chart_callback=self._hours_sparkline,
                                description=f"{billable_this_month:.0f}h billable",
                                description_icon="fa-solid fa-clock",
                                color="success",
                                link=request.url_for(
                                    "admin:list", key="timesheet"
                                ).include_query_params(
                                    filter=f"date__between={month_start.isoformat()}..{month_end.isoformat()}"
                                ),
                            )
                        ),
                        stat_col(
                            StatWidget(
                                title="Expenses To Review",
                                value_callback=self._count_submitted_expenses,
                                description=f"{_fmt_money(pending_expense_total)} awaiting approval",
                                description_icon="fa-solid fa-receipt",
                                color="warning",
                                link=request.url_for(
                                    "admin:list", key="expense"
                                ).include_query_params(filter="status__eq=submitted"),
                                countup=True,
                            )
                        ),
                        stat_col(
                            StatWidget(
                                title="Departments",
                                value_callback=self._count_departments,
                                description=f"{len(division_names)} top level divisions",
                                description_icon="fa-solid fa-sitemap",
                                color="secondary",
                                link=request.url_for(
                                    "admin:list", key="department"
                                ).include_query_params(filter="is_active__is_true"),
                                countup=True,
                            )
                        ),
                    ]
                ),
                # The org chart stays outside the tabs: ApexTree measures its
                # container at render time, and a hidden tab pane measures 0.
                OrgChartWidget(
                    title="Organization Chart",
                    tree_callback=self._org_tree,
                    height=440,
                ),
                TabsWidget(
                    tabs=[
                        ("Workforce", self._workforce_tab(request, division_names)),
                        (
                            "Projects & Tasks",
                            self._projects_tab(request, division_names),
                        ),
                        ("Time & Money", self._money_tab(request, month_labels)),
                    ]
                ),
            ]
        )

    # ── tab builders ─────────────────────────────────────────────────────────

    def _workforce_tab(
        self, request: Request, division_names: list[str]
    ) -> ColumnWidget:
        year_labels = [str(date.today().year - offset) for offset in range(9, -1, -1)]
        return ColumnWidget(
            children=[
                CardRowWidget(
                    children=[
                        Col(
                            ChartWidget(
                                title="Headcount by Division",
                                chart_type="bar",
                                series_callback=self._headcount_by_division,
                                options={
                                    "colors": [CATEGORICAL[0]],
                                    "plotOptions": {"bar": {"horizontal": True}},
                                    "xaxis": {"categories": division_names},
                                },
                            ),
                            breakpoints=Breakpoints(default=12, lg=7),
                        ),
                        Col(
                            ChartWidget(
                                title="Employment Type Mix",
                                chart_type="donut",
                                series_callback=self._employment_type_series,
                                options={
                                    "labels": [_title(t.value) for t in EmploymentType],
                                    "colors": CATEGORICAL[: len(EmploymentType)],
                                },
                            ),
                            breakpoints=Breakpoints(default=12, lg=5),
                        ),
                    ]
                ),
                CardRowWidget(
                    children=[
                        Col(
                            ChartWidget(
                                title="Hires per Year",
                                chart_type="area",
                                series_callback=self._hires_per_year,
                                options={
                                    "colors": [CATEGORICAL[0]],
                                    "xaxis": {"categories": year_labels},
                                    "dataLabels": {"enabled": False},
                                },
                            ),
                            breakpoints=Breakpoints(default=12, lg=6),
                        ),
                        Col(
                            ChartWidget(
                                title="Leave Requests by Type and Status",
                                chart_type="bar",
                                series_callback=self._leave_stacked_series,
                                options={
                                    "chart": {"stacked": True},
                                    "colors": [
                                        LEAVE_STATUS_COLORS[s] for s in LeaveStatus
                                    ],
                                    "xaxis": {
                                        "categories": [
                                            _title(t.value) for t in LeaveType
                                        ]
                                    },
                                    "dataLabels": {"enabled": False},
                                },
                            ),
                            breakpoints=Breakpoints(default=12, lg=6),
                        ),
                    ]
                ),
                PanelWidget(
                    title="People Movements",
                    icon="fa-solid fa-person-walking-arrow-right",
                    children=[
                        CardRowWidget(
                            children=[
                                Col(
                                    TableWidget(
                                        title="Recent Hires",
                                        columns=[
                                            "Name",
                                            "Job Title",
                                            "Department",
                                            "Hired",
                                        ],
                                        rows_callback=self._recent_hires,
                                    ),
                                    breakpoints=Breakpoints(default=12, lg=6),
                                ),
                                Col(
                                    TableWidget(
                                        title="Upcoming Leave",
                                        columns=[
                                            "Employee",
                                            "Type",
                                            "Status",
                                            "Starts",
                                            "Days",
                                        ],
                                        rows_callback=self._upcoming_leave,
                                    ),
                                    breakpoints=Breakpoints(default=12, lg=6),
                                ),
                            ]
                        )
                    ],
                ),
            ]
        )

    def _projects_tab(
        self, request: Request, division_names: list[str]
    ) -> ColumnWidget:
        return ColumnWidget(
            children=[
                GridWidget(
                    breakpoints=Breakpoints(default=1, md=2, lg=3),
                    gutter=4,
                    children=[
                        ChartWidget(
                            title="Projects by Status",
                            chart_type="donut",
                            series_callback=self._projects_by_status,
                            options={
                                "labels": [_title(s.value) for s in ProjectStatus],
                                "colors": [
                                    PROJECT_STATUS_COLORS[s] for s in ProjectStatus
                                ],
                            },
                        ),
                        ChartWidget(
                            title="Tasks by Status",
                            chart_type="bar",
                            series_callback=self._tasks_by_status,
                            options={
                                "colors": [TASK_STATUS_COLORS[s] for s in TaskStatus],
                                "plotOptions": {"bar": {"distributed": True}},
                                "legend": {"show": False},
                                "xaxis": {
                                    "categories": [_title(s.value) for s in TaskStatus]
                                },
                            },
                        ),
                        ChartWidget(
                            title="Tasks by Priority",
                            chart_type="bar",
                            series_callback=self._tasks_by_priority,
                            options={
                                "colors": [
                                    TASK_PRIORITY_COLORS[p] for p in TaskPriority
                                ],
                                "plotOptions": {"bar": {"distributed": True}},
                                "legend": {"show": False},
                                "xaxis": {
                                    "categories": [
                                        _title(p.value) for p in TaskPriority
                                    ]
                                },
                            },
                        ),
                    ],
                ),
                ChartWidget(
                    title="Project Budget vs Spend by Division ($K)",
                    chart_type="bar",
                    series_callback=self._budget_by_division,
                    height=320,
                    options={
                        "colors": [CATEGORICAL[0], CATEGORICAL[1]],
                        "xaxis": {"categories": division_names},
                        "dataLabels": {"enabled": False},
                    },
                ),
                PanelWidget(
                    title="Delivery Watchlist",
                    icon="fa-solid fa-triangle-exclamation",
                    children=[
                        CardRowWidget(
                            children=[
                                Col(
                                    TableWidget(
                                        title="Largest Project Budgets",
                                        columns=[
                                            "Project",
                                            "Department",
                                            "Budget",
                                            "Spent",
                                            "Burn",
                                        ],
                                        rows_callback=self._top_projects,
                                    ),
                                    breakpoints=Breakpoints(default=12, lg=6),
                                ),
                                Col(
                                    TableWidget(
                                        title="Overdue Tasks",
                                        columns=[
                                            "Task",
                                            "Project",
                                            "Assignee",
                                            "Due",
                                            "Priority",
                                        ],
                                        rows_callback=self._overdue_tasks,
                                    ),
                                    breakpoints=Breakpoints(default=12, lg=6),
                                ),
                            ]
                        )
                    ],
                ),
            ]
        )

    def _money_tab(self, request: Request, month_labels: list[str]) -> ColumnWidget:
        return ColumnWidget(
            children=[
                CardRowWidget(
                    children=[
                        Col(
                            ChartWidget(
                                title="Hours Logged per Month",
                                chart_type="line",
                                series_callback=self._hours_per_month,
                                options={
                                    "colors": [CATEGORICAL[0], CATEGORICAL[2]],
                                    "xaxis": {"categories": month_labels},
                                    "stroke": {"width": 2},
                                    "dataLabels": {"enabled": False},
                                },
                            ),
                            breakpoints=Breakpoints(default=12, lg=8),
                        ),
                        Col(
                            ChartWidget(
                                title="Billable Share (last 12 months)",
                                chart_type="radialBar",
                                series_callback=self._billable_share,
                                options={
                                    "labels": ["Billable"],
                                    "colors": [GOOD],
                                },
                            ),
                            breakpoints=Breakpoints(default=12, lg=4),
                        ),
                    ]
                ),
                CardRowWidget(
                    children=[
                        Col(
                            ChartWidget(
                                title="Expense Amounts by Category",
                                chart_type="donut",
                                series_callback=self._expenses_by_category,
                                options={
                                    "labels": [
                                        _title(c.value) for c in ExpenseCategory
                                    ],
                                    "colors": CATEGORICAL[: len(ExpenseCategory)],
                                },
                            ),
                            breakpoints=Breakpoints(default=12, lg=6),
                        ),
                        Col(
                            ChartWidget(
                                title="Expense Amounts by Status",
                                chart_type="bar",
                                series_callback=self._expenses_by_status,
                                options={
                                    "colors": [
                                        EXPENSE_STATUS_COLORS[s] for s in ExpenseStatus
                                    ],
                                    "plotOptions": {"bar": {"distributed": True}},
                                    "legend": {"show": False},
                                    "xaxis": {
                                        "categories": [
                                            _title(s.value) for s in ExpenseStatus
                                        ]
                                    },
                                    "dataLabels": {"enabled": False},
                                },
                            ),
                            breakpoints=Breakpoints(default=12, lg=6),
                        ),
                    ]
                ),
                TableWidget(
                    title="Expenses Awaiting Approval",
                    columns=["Number", "Employee", "Category", "Amount", "Submitted"],
                    rows_callback=self._pending_expenses,
                ),
            ]
        )

    # ── stat callbacks ───────────────────────────────────────────────────────

    async def _count_employees(self, request: Request) -> int:
        session: Session = request.state.session
        return (
            session.scalar(
                select(func.count(Employee.id)).where(Employee.deleted_at.is_(None))
            )
            or 0
        )

    async def _count_active_projects(self, request: Request) -> int:
        session: Session = request.state.session
        return (
            session.scalar(
                select(func.count(Project.id)).where(
                    Project.deleted_at.is_(None),
                    Project.status == ProjectStatus.ACTIVE,
                )
            )
            or 0
        )

    async def _count_pending_leave(self, request: Request) -> int:
        session: Session = request.state.session
        return (
            session.scalar(
                select(func.count(LeaveRequest.id)).where(
                    LeaveRequest.status == LeaveStatus.PENDING
                )
            )
            or 0
        )

    async def _count_open_tasks(self, request: Request) -> int:
        session: Session = request.state.session
        return (
            session.scalar(
                select(func.count(Task.id)).where(
                    Task.status.not_in([TaskStatus.COMPLETED, TaskStatus.CANCELLED])
                )
            )
            or 0
        )

    async def _annual_payroll(self, request: Request) -> str:
        session: Session = request.state.session
        total = session.scalar(
            select(func.coalesce(func.sum(Employee.salary), 0)).where(
                Employee.deleted_at.is_(None)
            )
        )
        return _fmt_money(total)

    async def _hours_this_month(self, request: Request) -> str:
        session: Session = request.state.session
        total = session.scalar(
            select(func.coalesce(func.sum(Timesheet.hours), 0)).where(
                func.strftime("%Y-%m", Timesheet.date) == date.today().strftime("%Y-%m")
            )
        )
        return f"{total:.0f}h"

    async def _count_submitted_expenses(self, request: Request) -> int:
        session: Session = request.state.session
        return (
            session.scalar(
                select(func.count(Expense.id)).where(
                    Expense.status == ExpenseStatus.SUBMITTED
                )
            )
            or 0
        )

    async def _count_departments(self, request: Request) -> int:
        session: Session = request.state.session
        return (
            session.scalar(
                select(func.count(Department.id)).where(Department.is_active.is_(True))
            )
            or 0
        )

    # ── sparkline callbacks ──────────────────────────────────────────────────

    async def _hires_sparkline(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        months = _last_months(12)
        month_expr = func.strftime("%Y-%m", Employee.hire_date)
        counts = dict(
            session.execute(
                select(month_expr, func.count(Employee.id))
                .where(
                    Employee.deleted_at.is_(None),
                    month_expr >= months[0][0],
                )
                .group_by(month_expr)
            ).all()
        )
        return [{"name": "Hires", "data": [counts.get(key, 0) for key, _ in months]}]

    async def _hours_sparkline(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        months = _last_months(12)
        month_expr = func.strftime("%Y-%m", Timesheet.date)
        totals = dict(
            session.execute(
                select(month_expr, func.sum(Timesheet.hours))
                .where(month_expr >= months[0][0])
                .group_by(month_expr)
            ).all()
        )
        return [
            {
                "name": "Hours",
                "data": [float(totals.get(key, 0) or 0) for key, _ in months],
            }
        ]

    # ── chart callbacks ──────────────────────────────────────────────────────

    def _division_names(self, session: Session) -> list[str]:
        """Top level division names (the root's direct children), by id order."""
        root_id = session.scalar(
            select(Department.id).where(Department.parent_id.is_(None))
        )
        return list(
            session.scalars(
                select(Department.name)
                .where(Department.parent_id == root_id)
                .order_by(Department.id)
            )
        )

    def _division_of(self, session: Session) -> dict[int, str]:
        """Map every department id to the name of its top level division.

        The root department maps to itself, so employees or projects attached
        directly to it still land in a bucket.
        """
        rows = session.execute(
            select(Department.id, Department.name, Department.parent_id)
        ).all()
        by_id = {dep_id: (name, parent_id) for dep_id, name, parent_id in rows}

        def climb(dep_id: int) -> str:
            name, parent_id = by_id[dep_id]
            # Stop one level below the root; the root maps to itself.
            while parent_id is not None and by_id[parent_id][1] is not None:
                name, parent_id = by_id[parent_id]
            return name

        return {dep_id: climb(dep_id) for dep_id in by_id}

    async def _headcount_by_division(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        division_of = self._division_of(session)
        totals: dict[str, int] = dict.fromkeys(self._division_names(session), 0)
        rows = session.execute(
            select(Employee.department_id, func.count(Employee.id))
            .where(Employee.deleted_at.is_(None), Employee.department_id.is_not(None))
            .group_by(Employee.department_id)
        ).all()
        for department_id, count in rows:
            division = division_of.get(department_id)
            if division in totals:
                totals[division] += count
        return [{"name": "Employees", "data": list(totals.values())}]

    async def _employment_type_series(self, request: Request) -> list[int]:
        session: Session = request.state.session
        counts = dict(
            session.execute(
                select(Employee.employment_type, func.count(Employee.id))
                .where(Employee.deleted_at.is_(None))
                .group_by(Employee.employment_type)
            ).all()
        )
        return [counts.get(employment_type, 0) for employment_type in EmploymentType]

    async def _hires_per_year(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        year_expr = func.strftime("%Y", Employee.hire_date)
        counts = dict(
            session.execute(
                select(year_expr, func.count(Employee.id))
                .where(Employee.deleted_at.is_(None))
                .group_by(year_expr)
            ).all()
        )
        years = [str(date.today().year - offset) for offset in range(9, -1, -1)]
        return [{"name": "Hires", "data": [counts.get(year, 0) for year in years]}]

    async def _leave_stacked_series(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        rows = session.execute(
            select(
                LeaveRequest.status,
                LeaveRequest.type,
                func.count(LeaveRequest.id),
            ).group_by(LeaveRequest.status, LeaveRequest.type)
        ).all()
        counts: dict[tuple[LeaveStatus, LeaveType], int] = {
            (status, leave_type): count for status, leave_type, count in rows
        }
        return [
            {
                "name": _title(status.value),
                "data": [
                    counts.get((status, leave_type), 0) for leave_type in LeaveType
                ],
            }
            for status in LeaveStatus
        ]

    async def _projects_by_status(self, request: Request) -> list[int]:
        session: Session = request.state.session
        counts = dict(
            session.execute(
                select(Project.status, func.count(Project.id))
                .where(Project.deleted_at.is_(None))
                .group_by(Project.status)
            ).all()
        )
        return [counts.get(status, 0) for status in ProjectStatus]

    async def _tasks_by_status(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        counts = dict(
            session.execute(
                select(Task.status, func.count(Task.id)).group_by(Task.status)
            ).all()
        )
        return [
            {"name": "Tasks", "data": [counts.get(status, 0) for status in TaskStatus]}
        ]

    async def _tasks_by_priority(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        counts = dict(
            session.execute(
                select(Task.priority, func.count(Task.id)).group_by(Task.priority)
            ).all()
        )
        return [
            {
                "name": "Tasks",
                "data": [counts.get(priority, 0) for priority in TaskPriority],
            }
        ]

    async def _budget_by_division(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        division_of = self._division_of(session)
        divisions = self._division_names(session)
        budget: dict[str, float] = dict.fromkeys(divisions, 0.0)
        spent: dict[str, float] = dict.fromkeys(divisions, 0.0)
        rows = session.execute(
            select(
                Project.department_id,
                func.sum(Project.budget),
                func.sum(Project.spent),
            )
            .where(Project.deleted_at.is_(None), Project.department_id.is_not(None))
            .group_by(Project.department_id)
        ).all()
        for department_id, budget_sum, spent_sum in rows:
            division = division_of.get(department_id)
            if division in budget:
                budget[division] += float(budget_sum or 0)
                spent[division] += float(spent_sum or 0)
        return [
            # Reported in thousands of dollars to keep axis labels short.
            {"name": "Budget", "data": [round(budget[d] / 1000) for d in divisions]},
            {"name": "Spent", "data": [round(spent[d] / 1000) for d in divisions]},
        ]

    async def _hours_per_month(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        months = _last_months(12)
        month_expr = func.strftime("%Y-%m", Timesheet.date)
        rows = session.execute(
            select(month_expr, Timesheet.is_billable, func.sum(Timesheet.hours))
            .where(month_expr >= months[0][0])
            .group_by(month_expr, Timesheet.is_billable)
        ).all()
        totals: dict[tuple[str, bool], float] = {
            (month, bool(billable)): float(hours or 0)
            for month, billable, hours in rows
        }
        return [
            {
                "name": "Billable",
                "data": [totals.get((key, True), 0.0) for key, _ in months],
            },
            {
                "name": "Non-billable",
                "data": [totals.get((key, False), 0.0) for key, _ in months],
            },
        ]

    async def _billable_share(self, request: Request) -> list[float]:
        session: Session = request.state.session
        months = _last_months(12)
        month_expr = func.strftime("%Y-%m", Timesheet.date)
        total = session.scalar(
            select(func.coalesce(func.sum(Timesheet.hours), 0)).where(
                month_expr >= months[0][0]
            )
        )
        billable = session.scalar(
            select(func.coalesce(func.sum(Timesheet.hours), 0)).where(
                month_expr >= months[0][0], Timesheet.is_billable.is_(True)
            )
        )
        if not total:
            return [0.0]
        return [round(float(billable) / float(total) * 100, 1)]

    async def _expenses_by_category(self, request: Request) -> list[float]:
        session: Session = request.state.session
        totals = dict(
            session.execute(
                select(Expense.category, func.sum(Expense.total_amount)).group_by(
                    Expense.category
                )
            ).all()
        )
        return [
            round(float(totals.get(category, 0) or 0), 2)
            for category in ExpenseCategory
        ]

    async def _expenses_by_status(self, request: Request) -> list[dict[str, Any]]:
        session: Session = request.state.session
        totals = dict(
            session.execute(
                select(Expense.status, func.sum(Expense.total_amount)).group_by(
                    Expense.status
                )
            ).all()
        )
        return [
            {
                "name": "Amount",
                "data": [
                    round(float(totals.get(status, 0) or 0)) for status in ExpenseStatus
                ],
            }
        ]

    # ── table callbacks ──────────────────────────────────────────────────────

    async def _recent_hires(self, request: Request) -> list[list[Any]]:
        session: Session = request.state.session
        employees = session.scalars(
            select(Employee)
            .where(Employee.deleted_at.is_(None))
            .order_by(Employee.hire_date.desc())
            .limit(6)
        ).all()
        return [
            [
                employee.name,
                employee.job_title,
                employee.department.name if employee.department else "Unassigned",
                employee.hire_date.strftime("%Y-%m-%d"),
            ]
            for employee in employees
        ]

    async def _upcoming_leave(self, request: Request) -> list[list[Any]]:
        session: Session = request.state.session
        leave_requests = session.scalars(
            select(LeaveRequest)
            .where(
                LeaveRequest.start_date >= date.today(),
                LeaveRequest.status.in_([LeaveStatus.APPROVED, LeaveStatus.PENDING]),
            )
            .order_by(LeaveRequest.start_date.asc())
            .limit(6)
        ).all()
        return [
            [
                leave.employee.name,
                _title(leave.type.value),
                _title(leave.status.value),
                leave.start_date.strftime("%Y-%m-%d"),
                f"{leave.days_requested:g}",
            ]
            for leave in leave_requests
        ]

    async def _top_projects(self, request: Request) -> list[list[Any]]:
        session: Session = request.state.session
        projects = session.scalars(
            select(Project)
            .where(Project.deleted_at.is_(None))
            .order_by(Project.budget.desc())
            .limit(6)
        ).all()
        return [
            [
                project.name,
                project.department.name if project.department else "Unassigned",
                _fmt_money(project.budget),
                _fmt_money(project.spent),
                f"{float(project.spent) / float(project.budget) * 100:.0f}%"
                if project.budget
                else "n/a",
            ]
            for project in projects
        ]

    async def _overdue_tasks(self, request: Request) -> list[list[Any]]:
        session: Session = request.state.session
        tasks = session.scalars(
            select(Task)
            .where(
                Task.due_date < date.today(),
                Task.status.not_in([TaskStatus.COMPLETED, TaskStatus.CANCELLED]),
            )
            .order_by(Task.due_date.asc())
            .limit(6)
        ).all()
        return [
            [
                task.title,
                task.project.name,
                task.assignee.name if task.assignee else "Unassigned",
                task.due_date.strftime("%Y-%m-%d"),
                _title(task.priority.value),
            ]
            for task in tasks
        ]

    async def _pending_expenses(self, request: Request) -> list[list[Any]]:
        session: Session = request.state.session
        expenses = session.scalars(
            select(Expense)
            .where(Expense.status == ExpenseStatus.SUBMITTED)
            .order_by(Expense.submitted_at.desc())
            .limit(6)
        ).all()
        return [
            [
                expense.expense_number,
                expense.employee.name,
                _title(expense.category.value),
                f"${expense.total_amount:,.2f}",
                expense.submitted_at.strftime("%Y-%m-%d")
                if expense.submitted_at
                else "",
            ]
            for expense in expenses
        ]

    # ── org chart callback ───────────────────────────────────────────────────

    async def _org_tree(self, request: Request) -> dict[str, Any]:
        """Nested department tree in the shape ApexTree renders.

        Each node card shows the department name, the number of people in
        the department and everything below it, and the department budget.
        The card background uses the color stored on the department row.
        """
        session: Session = request.state.session
        departments = session.scalars(select(Department).order_by(Department.id)).all()
        head_counts = dict(
            session.execute(
                select(Employee.department_id, func.count(Employee.id))
                .where(
                    Employee.deleted_at.is_(None),
                    Employee.department_id.is_not(None),
                )
                .group_by(Employee.department_id)
            ).all()
        )
        children_of: dict[int | None, list[Department]] = {}
        for department in departments:
            children_of.setdefault(department.parent_id, []).append(department)

        def build(department: Department) -> tuple[dict[str, Any], int]:
            child_nodes: list[dict[str, Any]] = []
            people = head_counts.get(department.id, 0)
            for child in children_of.get(department.id, []):
                node, subtree_people = build(child)
                child_nodes.append(node)
                people += subtree_people
            color = department.color or "#6b7280"
            return {
                "id": str(department.id),
                "data": {
                    "name": department.name,
                    "people": f"{people} {'person' if people == 1 else 'people'}",
                    "budget": _fmt_money(department.budget),
                    "color": color,
                },
                "options": {"nodeBGColor": color, "nodeBGColorHover": color},
                "children": child_nodes,
            }, people

        roots = children_of.get(None, [])
        if not roots:
            return {"id": "empty", "data": {"name": "No departments"}, "children": []}
        root_node, _ = build(roots[0])
        return root_node
