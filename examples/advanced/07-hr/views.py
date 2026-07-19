"""
07-hr: admin views.

`SoftDeleteModelView` is the reusable base class: any ModelView built on
top of a model that mixes in `SoftDeleteMixin` (see models.py) gets
"delete hides the row" behavior for free by subclassing it. Employee and
Project both mix in SoftDeleteMixin and both just hide deleted rows,
without exposing a restore UI.
"""

from collections import Counter
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import anyio
from fields import (
    AvatarNameField,
    DollarField,
    EmploymentTypeBadgeField,
    ExpenseCategoryBadgeField,
    ExpenseStatusBadgeField,
    LeaveStatusBadgeField,
    LeaveTypeBadgeField,
    ProgressField,
    ProjectStatusBadgeField,
    TaskPriorityBadgeField,
    TaskStatusBadgeField,
    name_initials,
)
from filters import (
    DepartmentContainsFilter,
    DepartmentInFilter,
    DepartmentNotInFilter,
)
from models import (
    Employee,
    EmploymentType,
    Expense,
    ExpenseCategory,
    ExpenseLine,
    ExpenseStatus,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    ProjectStatus,
    Task,
    TaskPriority,
    TaskStatus,
)
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette_admin import (
    CollectionField,
    ColorField,
    FieldsetWidget,
    HasOne,
    ImageField,
    ListField,
    PanelWidget,
    RowActionsDisplayType,
    RowActionsPosition,
    StringField,
    TabsWidget,
    TagsField,
    TextWidget,
    action,
    flash,
    row_action,
)
from starlette_admin.contrib.sqla import InlineModelView
from starlette_admin.contrib.sqla import ModelView as BaseModelView
from starlette_admin.contrib.sqla.filters import IsNotNullFilter, IsNullFilter
from starlette_admin.exceptions import ActionFailed, FormValidationError
from starlette_admin.fields import EmailField, SlugField
from starlette_admin.helpers import on_commit
from starlette_admin.storage import LocalStorage

# ── Soft-delete base views ───────────────────────────────────────────────────


class ModelView(BaseModelView):
    """Share common configuration across all views."""

    row_actions_display_type = RowActionsDisplayType.KEBAB
    row_actions_position = RowActionsPosition.AFTER_COLUMNS
    show_goto_page = True


class SoftDeleteModelView(ModelView):
    """Base view for a model mixing in SoftDeleteMixin.

    Hides trashed rows from the list/count/detail queries, and turns "delete"
    into stamping `deleted_at` rather than issuing a SQL DELETE.
    """

    exclude_fields_from_list = ["deleted_at"]
    exclude_fields_from_create = ["deleted_at"]
    exclude_fields_from_edit = ["deleted_at"]

    def get_list_query(self, request: Request):
        return super().get_list_query(request).where(self.model.deleted_at.is_(None))

    def get_count_query(self, request: Request):
        return super().get_count_query(request).where(self.model.deleted_at.is_(None))

    def get_detail_query(self, request: Request):
        return super().get_detail_query(request).where(self.model.deleted_at.is_(None))

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        session: Session = request.state.session
        objs = await self.find_by_pks(request, pks)
        now = datetime.utcnow()
        for obj in objs:
            await self._emit_before_delete(request, obj.id, obj)
            obj.deleted_at = now
            session.add(obj)
        session.flush()

        def _make_after_delete_committed(obj: Any, pk: Any) -> Callable[[], Any]:
            return lambda: self._emit_after_delete_committed(request, pk, obj)

        for obj in objs:
            pk = obj.id
            await self._emit_after_delete(request, pk, obj)
            on_commit(request, _make_after_delete_committed(obj, pk))
        return len(objs)


# ── Department ───────────────────────────────────────────────────────────────


class DepartmentView(ModelView):
    fields = [
        "id",
        "name",
        SlugField("slug", populate_from="name"),
        "description",
        DollarField(
            "budget", help_text="Annual budget allocated to the department, in USD."
        ),
        "headcount",
        ColorField("color"),
        "is_active",
        HasOne(
            "parent",
            key="department",
            null_template="fields/detail/_department_parent_null.html",
        ),
    ]
    exclude_fields_from_list = ["id", "description"]
    fields_default_sort = ["name"]
    form_layout = [
        FieldsetWidget(legend="Identity", children=[("name", "slug"), "description"]),
        PanelWidget(
            title="Structure",
            children=[("parent", "headcount"), ("color", "is_active")],
        ),
        PanelWidget(
            title="Budget",
            children=[
                TextWidget(
                    content="Prefer the 'Adjust budget' row action for changes",
                ),
                "budget",
            ],
        ),
    ]

    row_actions = ["view", "adjust_budget", "edit", "delete"]

    @staticmethod
    def _build_adjust_budget_form(_request: Request, obj: Any) -> str:
        return f"""
        <form>
            <div class="mt-3">
                <label class="form-label">New budget for {obj.name}</label>
                <input type="number" class="form-control" name="new_budget"
                       value="{obj.budget:.2f}" step="0.01">
            </div>
        </form>
        """

    @row_action(
        name="adjust_budget",
        text="Adjust budget",
        confirmation="Set this department's new budget.",
        icon_class="fa-solid fa-sack-dollar",
        submit_btn_text="Apply",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
        form=_build_adjust_budget_form,
    )
    async def adjust_budget_row_action(self, request: Request, pk: Any) -> None:
        session: Session = request.state.session
        data = await request.form()
        try:
            new_budget = Decimal(data.get("new_budget"))
        except (InvalidOperation, TypeError) as err:
            raise ActionFailed("Enter a valid amount.") from err
        if new_budget < 0:
            raise ActionFailed("Budget cannot be reduced below zero.")
        department = await self.find_by_pk(request, pk)
        delta = new_budget - department.budget
        department.budget = new_budget
        session.add(department)
        session.flush()  # the session is committed automatically at the end of each request
        delta_sign = "+" if delta >= 0 else "-"
        flash(
            request,
            f"{department.name}'s budget was adjusted by {delta_sign}${abs(delta):,.2f}, "
            f"new total: ${new_budget:,.2f}.",
            "success",
        )

    @action(
        name="deactivate",
        text="Deactivate selected departments",
        confirmation="Are you sure you want to deactivate the selected departments?",
        submit_btn_text="Yes, deactivate",
        submit_btn_class="btn-outline-danger",
    )
    async def deactivate_action(self, request: Request, pks: list[Any]) -> None:
        session: Session = request.state.session
        departments = await self.find_by_pks(request, pks)
        for department in departments:
            department.is_active = False
            session.add(department)
        session.flush()  # the session is committed automatically at the end of each request
        flash(
            request,
            f"{len(departments)} department(s) were deactivated.",
            "success",
        )


# ── Employee (soft-deletable) ────────────────────────────────────────────────

avatars_storage = LocalStorage(base_dir="uploads/")


class EmployeeView(SoftDeleteModelView):
    """Renders the detail page as a profile: `templates/employee/detail.html`
    extends the stock detail template and replaces the attribute/value table
    (the `details_table` block) with a hand-built profile body: an identity
    row (avatar, job title, badges) followed by grouped datagrids for
    contact, employment, and compensation facts.

    The `initials` and `tenure` methods below exist for that template: it
    receives this view as `view` in its context and calls them directly,
    which keeps date math and string munging in Python rather than in Jinja.
    """

    detail_template = "employee/detail.html"

    fields = [
        "id",
        ImageField(
            "avatar",
            storage=avatars_storage,
            upload_folder="avatars",
            exclude_from_list=True,
        ),
        AvatarNameField(avatars_storage=avatars_storage),
        EmailField("email"),
        "phone",
        "date_of_birth",
        "job_title",
        EmploymentTypeBadgeField("employment_type", enum=EmploymentType),
        DollarField("salary", help_text="Annual salary in USD."),
        "hire_date",
        TagsField("skills", label="Skills"),
        ListField(
            CollectionField(
                "metadata_",
                fields=[StringField("property"), StringField("value")],
            ),
        ),
        "is_active",
        HasOne(
            "department",
            key="department",
            filters=[
                DepartmentContainsFilter,
                DepartmentInFilter,
                DepartmentNotInFilter,
                IsNullFilter,
                IsNotNullFilter,
            ],
        ),
        "deleted_at",
    ]
    exclude_fields_from_list = [
        *SoftDeleteModelView.exclude_fields_from_list,
        "id",
        "phone",
        "date_of_birth",
        "skills",
        "metadata_",
    ]
    # `RelationField`s (like `department`) are excluded from the searchable
    # default computed by the SQLAlchemy converter. Listed here
    # explicitly, alongside every other field, so `department` picks up the
    # filters declared on it above.
    searchable_fields = [
        "id",
        "name",
        "email",
        "phone",
        "date_of_birth",
        "job_title",
        "employment_type",
        "salary",
        "hire_date",
        "skills",
        "metadata_",
        "is_active",
        "department",
        "deleted_at",
    ]
    fields_default_sort = ["name"]
    form_layout = [
        TabsWidget(
            tabs=[
                (
                    "Identity",
                    ["avatar", "name", ("email", "phone"), "date_of_birth"],
                ),
                (
                    "Employment",
                    [
                        ("job_title", "employment_type"),
                        ("hire_date", "department"),
                        "is_active",
                    ],
                ),
                ("Additional Info", ["skills", "metadata_"]),
                (
                    "Compensation",
                    [TextWidget(content="Visible to HR only.", card=False), "salary"],
                ),
            ]
        ),
    ]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}
        salary = data.get("salary")
        if salary is not None and salary <= 0:
            errors["salary"] = "Salary must be a positive amount."
        date_of_birth = data.get("date_of_birth")
        hire_date = data.get("hire_date")
        if date_of_birth is not None and hire_date is not None:
            working_age_cutoff = date(
                hire_date.year - 16, hire_date.month, hire_date.day
            )
            if date_of_birth > working_age_cutoff:
                errors["date_of_birth"] = (
                    "Employee must be at least 16 years old as of the hire date."
                )
        email = data.get("email")
        if email is not None:
            # Checked here rather than left to the database so the form
            # reports it against the `email` field instead of surfacing
            # the raw `sqlalchemy.exc.IntegrityError` from the unique
            # constraint on `employees.email`.
            session: Session = request.state.session
            query = select(Employee.id).where(Employee.email == email)
            pk = request.query_params.get("pk")
            if pk is not None:
                query = query.where(Employee.id != int(pk))
            if session.execute(query).first() is not None:
                errors["email"] = "An employee with this email already exists."
        if errors:
            raise FormValidationError(errors)
        await super().validate(request, data)

    def get_search_query(self, request: Request, term: str) -> Any:
        # The base `get_search_query` only matches fields whose exact type is
        # in its allowlist (see `contrib/sqla/view.py`), so it skips `name`
        # here: that column is rendered by `AvatarNameField`, a `StringField`
        # subclass, and the allowlist check is an exact type match rather
        # than an `isinstance` check. Add the `name` match back explicitly so
        # the search bar still finds employees by name.
        return or_(
            super().get_search_query(request, term), Employee.name.ilike(f"%{term}%")
        )

    @staticmethod
    def initials(name: str) -> str:
        """Fallback for the profile header avatar when no image is uploaded,
        matching the list page chip rendered by `AvatarNameField`."""
        return name_initials(name)

    @staticmethod
    def tenure(obj: Any) -> str:
        """Human-readable time since `hire_date`, e.g. "3 years, 4 months"."""
        days = (date.today() - obj.hire_date).days
        if days < 0:
            return "Starts soon"
        years, remainder = divmod(days, 365)
        months = remainder // 30
        if years and months:
            return f"{years} year{'s' if years > 1 else ''}, {months} month{'s' if months > 1 else ''}"
        if years:
            return f"{years} year{'s' if years > 1 else ''}"
        if months:
            return f"{months} month{'s' if months > 1 else ''}"
        return f"{days} day{'s' if days != 1 else ''}"


# ── LeaveRequest ─────────────────────────────────────────────────────────────


class LeaveRequestView(ModelView):
    fields = [
        "id",
        "employee",
        "approver",
        LeaveTypeBadgeField("type", enum=LeaveType),
        LeaveStatusBadgeField("status", enum=LeaveStatus),
        "start_date",
        "end_date",
        "start_time",
        "end_time",
        "days_requested",
        "reason",
        "reviewer_notes",
        "reviewed_at",
    ]
    exclude_fields_from_list = ["id", "reason", "reviewer_notes"]
    fields_default_sort = [("start_date", True)]
    form_layout = [
        FieldsetWidget(
            legend="Request",
            children=[
                ("employee", "type"),
                ("start_date", "end_date"),
                ("start_time", "end_time"),
                "days_requested",
                "reason",
            ],
        ),
        PanelWidget(
            title="Review",
            children=[
                TextWidget(
                    content="Normally set through the Approve/Reject row "
                    "actions; edit directly only to correct a mistake.",
                    card=False,
                ),
                ("approver", "status"),
                "reviewer_notes",
                "reviewed_at",
            ],
            collapsible=True,
            collapsed=True,
        ),
    ]

    row_actions = ["view", "approve", "reject", "edit", "delete"]
    actions = ["approve", "reject"]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if start_date is not None and end_date is not None and end_date < start_date:
            errors["end_date"] = "End date must be on or after the start date."
        days_requested = data.get("days_requested")
        if days_requested is not None and days_requested <= 0:
            errors["days_requested"] = "Days requested must be greater than zero."
        if errors:
            raise FormValidationError(errors)
        await super().validate(request, data)

    async def is_row_action_allowed_for_obj(
        self, request: Request, name: str, obj: Any
    ) -> bool:
        if name in ("approve", "reject"):
            return obj.status == LeaveStatus.PENDING
        return await super().is_row_action_allowed_for_obj(request, name, obj)

    @row_action(
        name="approve",
        text="Approve",
        confirmation="Approve this leave request?",
        icon_class="fa-solid fa-check",
        submit_btn_text="Yes, approve",
        submit_btn_class="btn-success",
        action_btn_class="btn-success",
    )
    async def approve_row_action(self, request: Request, pk: Any) -> None:
        leave_request = await self.find_by_pk(request, pk)
        self._review(request, [leave_request], LeaveStatus.APPROVED)
        flash(
            request,
            f"{leave_request.employee.name}'s leave request was approved.",
            "success",
        )

    @row_action(
        name="reject",
        text="Reject",
        confirmation="Reject this leave request?",
        icon_class="fa-solid fa-xmark",
        submit_btn_text="Yes, reject",
        submit_btn_class="btn-danger",
        action_btn_class="btn-danger",
    )
    async def reject_row_action(self, request: Request, pk: Any) -> None:
        leave_request = await self.find_by_pk(request, pk)
        self._review(request, [leave_request], LeaveStatus.REJECTED)
        flash(
            request,
            f"{leave_request.employee.name}'s leave request was rejected.",
            "success",
        )

    @action(
        name="approve",
        text="Approve selected leave requests",
        confirmation="Approve the selected leave requests? Requests that "
        "aren't pending are left untouched.",
        submit_btn_text="Yes, approve",
        submit_btn_class="btn-success",
        icon_class="fa-solid fa-check",
    )
    async def approve_action(self, request: Request, pks: list[Any]) -> None:
        leave_requests = await self.find_by_pks(request, pks)
        pending = [lr for lr in leave_requests if lr.status == LeaveStatus.PENDING]
        self._review(request, pending, LeaveStatus.APPROVED)
        flash(request, f"{len(pending)} leave request(s) were approved.", "success")

    @action(
        name="reject",
        text="Reject selected leave requests",
        confirmation="Reject the selected leave requests? Requests that "
        "aren't pending are left untouched.",
        submit_btn_text="Yes, reject",
        submit_btn_class="btn-outline-danger",
        icon_class="fa-solid fa-xmark",
    )
    async def reject_action(self, request: Request, pks: list[Any]) -> None:
        leave_requests = await self.find_by_pks(request, pks)
        pending = [lr for lr in leave_requests if lr.status == LeaveStatus.PENDING]
        self._review(request, pending, LeaveStatus.REJECTED)
        flash(request, f"{len(pending)} leave request(s) were rejected.", "success")

    @staticmethod
    def _review(
        request: Request, leave_requests: list[LeaveRequest], status: LeaveStatus
    ) -> None:
        session: Session = request.state.session
        now = datetime.utcnow()
        for leave_request in leave_requests:
            leave_request.status = status
            leave_request.reviewed_at = now
            session.add(leave_request)
        session.flush()  # the session is committed automatically at the end of each request


# ── Project (soft-deletable) ─────────────────────────────────────────────────


class ExpenseLineInline(InlineModelView):
    model = ExpenseLine
    fields = ["id", "description", "amount", "quantity", "unit_price", "date"]
    menu_label = "Expense lines"
    extra = 1
    collapsed = True


class TaskInline(InlineModelView):
    model = Task
    fk_attr = "project_id"
    fields = [
        "id",
        "title",
        TaskStatusBadgeField("status", enum=TaskStatus),
        TaskPriorityBadgeField("priority", enum=TaskPriority),
        "assignee",
        "due_date",
    ]
    menu_label = "Tasks"
    extra = 1


class ProjectView(SoftDeleteModelView):
    """Renders the detail page as a mini dashboard: `templates/project/detail.html`
    extends the stock detail template, adds three stat cards (budget burn,
    task breakdown, timeline), and replaces the attribute/value table with a
    facts datagrid, with the task inline table below it for drill-down.

    Each card is backed by one of the helper methods below. The template
    receives this view as `view` and the model instance as `raw_obj`, so a
    card renders with `view.budget_burn(raw_obj)` and the aggregation logic
    stays in Python next to the view.
    """

    detail_template = "project/detail.html"

    fields = [
        "id",
        "name",
        SlugField("slug", populate_from="name"),
        "description",
        ProjectStatusBadgeField("status", enum=ProjectStatus),
        TaskPriorityBadgeField("priority", enum=TaskPriority),
        DollarField(
            "budget", help_text="Total budget allocated to the project, in USD."
        ),
        DollarField("spent", help_text="Total amount spent on the project, in USD."),
        "estimated_hours",
        "actual_hours",
        ProgressField(
            "progress", help_text="Actual hours logged as a share of estimated hours."
        ),
        "start_date",
        "end_date",
        "plan",
        "department",
        "deleted_at",
    ]
    exclude_fields_from_list = [
        *SoftDeleteModelView.exclude_fields_from_list,
        "id",
        "slug",
        "description",
        "plan",
        "estimated_hours",
        "actual_hours",
    ]
    inlines = [TaskInline]
    fields_default_sort = ["name"]
    form_layout = [
        FieldsetWidget(
            legend="Identity",
            children=[("name", "slug"), "description", "department"],
        ),
        PanelWidget(
            title="Status",
            children=[("status", "priority"), ("start_date", "end_date")],
        ),
        PanelWidget(
            title="Budget & Effort",
            children=[
                TextWidget(
                    content="Actuals feed the burn and timeline cards on the "
                    "detail dashboard.",
                    card=False,
                ),
                ("budget", "spent"),
                ("estimated_hours", "actual_hours"),
            ],
            collapsible=True,
            collapsed=True,
        ),
    ]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if start_date is not None and end_date is not None and end_date < start_date:
            errors["end_date"] = "End date must be on or after the start date."
        budget = data.get("budget")
        if budget is not None and budget < 0:
            errors["budget"] = "Budget cannot be negative."
        spent = data.get("spent")
        if spent is not None and spent < 0:
            errors["spent"] = "Spent cannot be negative."
        if errors:
            raise FormValidationError(errors)
        await super().validate(request, data)

    # Instantiated once for its color and icon mappings, so the task
    # breakdown card uses the exact same badges as the task list and inline.
    _task_status_badges = TaskStatusBadgeField("status", enum=TaskStatus)

    @staticmethod
    def budget_burn(obj: Any) -> dict[str, Any]:
        """Share of `budget` consumed by `spent`, as progress bar context.

        The bar turns orange at 80 percent and red past 100, the same
        thresholds a reviewer would eyeball on a burn chart.
        """
        if not obj.budget:
            return {"width": 0, "bar_class": "bg-secondary", "label": "No budget set"}
        percent = round(float(obj.spent) / float(obj.budget) * 100)
        bar_class = (
            "bg-danger"
            if percent > 100
            else "bg-warning"
            if percent >= 80
            else "bg-primary"
        )
        return {
            "width": min(percent, 100),
            "bar_class": bar_class,
            "label": f"{percent}% of budget spent",
        }

    def task_stats(self, obj: Any) -> list[dict[str, Any]]:
        """Task counts grouped by status, shaped for `fields/badge.html`.

        Each entry carries the badge class and icon from
        `TaskStatusBadgeField` plus a `count`, and statuses with no tasks
        are omitted. Iterating `TaskStatus` keeps the workflow order
        (backlog first, cancelled last) rather than insertion order.
        """
        counts = Counter(task.status for task in obj.tasks)
        return [
            {
                "label": status.value.replace("_", " ").title(),
                "badge_class": self._task_status_badges.badge_class_by_value.get(
                    status.value, "badge"
                ),
                "icon": self._task_status_badges.icon_by_value.get(status.value),
                "count": counts[status],
            }
            for status in TaskStatus
            if counts[status]
        ]

    @staticmethod
    def timeline(obj: Any) -> dict[str, Any]:
        """Schedule position between `start_date` and `end_date`.

        Returns a headline (days left, days overdue, or a status note) plus
        progress bar context for how far through its window the project is.
        """
        today = date.today()
        if obj.status == ProjectStatus.COMPLETED:
            return {"headline": "Completed", "width": 100, "bar_class": "bg-success"}
        if today < obj.start_date:
            days = (obj.start_date - today).days
            return {
                "headline": f"Starts in {days} day{'s' if days != 1 else ''}",
                "width": 0,
                "bar_class": "bg-primary",
            }
        if obj.end_date is None:
            day = (today - obj.start_date).days + 1
            return {"headline": f"Day {day}", "width": 0, "bar_class": "bg-primary"}
        remaining = (obj.end_date - today).days
        if remaining < 0:
            return {
                "headline": f"{-remaining} day{'s' if remaining != -1 else ''} overdue",
                "width": 100,
                "bar_class": "bg-danger",
            }
        total = max((obj.end_date - obj.start_date).days, 1)
        elapsed = (today - obj.start_date).days
        return {
            "headline": f"{remaining} day{'s' if remaining != 1 else ''} left",
            "width": min(round(elapsed / total * 100), 100),
            "bar_class": "bg-primary",
        }


# ── Task ─────────────────────────────────────────────────────────────────────


class TaskView(ModelView):
    fields = [
        "id",
        "title",
        "description",
        "project",
        "assignee",
        TaskStatusBadgeField("status", enum=TaskStatus),
        TaskPriorityBadgeField("priority", enum=TaskPriority),
        "estimated_hours",
        "actual_hours",
        "due_date",
        "completed_at",
        "labels",
    ]
    exclude_fields_from_list = ["id", "description", "labels"]
    form_layout = [
        FieldsetWidget(
            legend="Details",
            children=["title", "description", ("project", "assignee")],
        ),
        PanelWidget(
            title="Status & Priority",
            children=[("status", "priority"), ("due_date", "completed_at")],
        ),
        PanelWidget(
            title="Effort",
            children=[("estimated_hours", "actual_hours"), "labels"],
            collapsible=True,
            collapsed=True,
        ),
    ]


# ── Timesheet ────────────────────────────────────────────────────────────────


class TimesheetView(ModelView):
    fields = [
        "id",
        "employee",
        "date",
        "hours",
        "minutes",
        "description",
        "is_billable",
        "hourly_rate",
        "total_cost",
        "task",
        "project",
    ]
    exclude_fields_from_list = ["id", "description"]
    fields_default_sort = [("date", True)]
    form_layout = [
        FieldsetWidget(
            legend="Entry",
            children=[("employee", "project"), ("task", "date"), "description"],
        ),
        PanelWidget(
            title="Time & Billing",
            children=[
                ("hours", "minutes"),
                ("is_billable", "hourly_rate"),
                "total_cost",
            ],
        ),
    ]


# ── Expense ──────────────────────────────────────────────────────────────────


class ExpenseView(ModelView):
    fields = [
        "id",
        "employee",
        "project",
        "expense_number",
        ExpenseStatusBadgeField("status", enum=ExpenseStatus),
        ExpenseCategoryBadgeField("category", enum=ExpenseCategory),
        "description",
        DollarField(
            "total_amount",
            help_text="Sum of this expense's line items, in USD. Derived, not editable.",
            read_only=True,
        ),
        "submitted_at",
        "approved_at",
        "approved_by",
        "receipt_path",
        "notes",
    ]
    exclude_fields_from_list = ["id", "description", "notes", "receipt_path"]
    exclude_fields_from_create = ["total_amount"]
    inlines = [ExpenseLineInline]
    fields_default_sort = [("submitted_at", True)]
    form_layout = [
        FieldsetWidget(
            legend="Details",
            children=[("employee", "project"), "expense_number", "description"],
        ),
        PanelWidget(title="Classification", children=[("status", "category")]),
        PanelWidget(
            title="Approval",
            children=[
                TextWidget(
                    content="Set by the review workflow rather than entered by hand.",
                    card=False,
                ),
                ("submitted_at", "approved_at"),
                ("approved_by", "total_amount"),
            ],
            collapsible=True,
            collapsed=True,
        ),
        PanelWidget(
            title="Receipt & Notes",
            children=["receipt_path", "notes"],
            collapsible=True,
            collapsed=True,
        ),
    ]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}
        submitted_at = data.get("submitted_at")
        approved_at = data.get("approved_at")
        if (
            submitted_at is not None
            and approved_at is not None
            and approved_at < submitted_at
        ):
            errors["approved_at"] = "Approval time cannot precede submission time."
        if data.get("status") == ExpenseStatus.APPROVED and not data.get("approved_by"):
            errors["approved_by"] = "An approver is required for an approved expense."
        if errors:
            raise FormValidationError(errors)
        await super().validate(request, data)

    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await self._recompute_total_amount(request, obj.id)

    async def after_edit_committed(self, request: Request, obj: Any) -> None:
        await self._recompute_total_amount(request, obj.id)

    @staticmethod
    async def _recompute_total_amount(request: Request, expense_id: int) -> None:
        """Set `total_amount` to the sum of this expense's line items.

        Runs once the request's own transaction is durably committed, so the
        expense's inline `ExpenseLine` rows (saved after the parent expense,
        see `_save_inlines` in base.py) are guaranteed to already be in the
        database. `request.state.session` must not be written to at this
        point (see `on_commit`'s docstring: it is committed and closed by the
        time this hook returns, discarding anything flushed on it), so this
        opens its own session on the same engine, updates, and commits
        independently.
        """
        engine = request.state.session.get_bind()

        def _update() -> None:
            with Session(engine) as session:
                total = session.scalar(
                    select(func.coalesce(func.sum(ExpenseLine.amount), 0)).where(
                        ExpenseLine.expense_id == expense_id
                    )
                )
                session.execute(
                    update(Expense)
                    .where(Expense.id == expense_id)
                    .values(total_amount=total)
                )
                session.commit()

        await anyio.to_thread.run_sync(_update)
