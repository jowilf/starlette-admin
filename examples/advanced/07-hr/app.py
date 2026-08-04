"""
07-hr: an HR admin, ported from the Filament demo's HR module
(filamentphp/demo, app/Models/HR).

Department -> Employee -> {LeaveRequest, Task, Timesheet, Expense} -> Project,
with Employee and Project soft-deletable through the shared
`SoftDeleteMixin` / `SoftDeleteModelView` pair defined in models.py / views.py.

Timesheet and LeaveRequest are grouped under a single "Time & Attendance"
dropdown in the menu.
"""

from contextlib import asynccontextmanager

import uvicorn
from dashboard import HRDashboardView
from models import (
    Base,
    Department,
    Employee,
    Expense,
    LeaveRequest,
    Project,
    Task,
    Timesheet,
)
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import DropDown
from starlette_admin.contrib.sqla import Admin
from views import (
    DepartmentView,
    EmployeeView,
    ExpenseView,
    LeaveRequestView,
    ProjectView,
    TaskView,
    TimesheetView,
)

DATABASE_FILE = "advanced_07_hr.sqlite"

engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},
    echo=True,  # log SQL to console for debugging
)


@asynccontextmanager
async def lifespan(_: Starlette):
    # Tables are created here, but data is not: seeding is handled by the
    # standalone seed.py script, which populates a running app through the
    # admin's own HTTP endpoints. See seed.py for usage.
    Base.metadata.create_all(engine)
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse(
                "<h2>HR example</h2>"
                "<p>Departments, employees, projects, tasks, timesheets, leave "
                "requests, and expenses, ported from the Filament HR demo.</p>"
                '<a href="/admin/">Go to Admin →</a>'
            ),
        )
    ],
)

admin = Admin(
    engine,
    title="Example: HR",
    secret_key="dev-only-change-me",
    templates_dir="templates",
    # The dashboard replaces the default index page; see dashboard.py.
    index_view=HRDashboardView(),
)

admin.add_view(DepartmentView(Department, icon="fa fa-sitemap"))
admin.add_view(EmployeeView(Employee, icon="fa fa-id-badge"))
admin.add_view(ProjectView(Project, icon="fa fa-diagram-project"))
admin.add_view(TaskView(Task, icon="fa fa-list-check"))
admin.add_view(ExpenseView(Expense, icon="fa fa-receipt"))
admin.add_view(
    DropDown(
        "Time & Attendance",
        icon="fa fa-business-time",
        views=[
            TimesheetView(Timesheet, icon="fa fa-clock"),
            LeaveRequestView(LeaveRequest, icon="fa fa-calendar-days"),
        ],
    )
)

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../../.."])
