"""
07-hr: SQLAlchemy models for the HR module.

Ported from the entities and relationships of the Filament HR demo
(filamentphp/demo, app/Models/HR): Department, Employee, LeaveRequest,
Project, Task, Timesheet, Expense, and ExpenseLine.

`SoftDeleteMixin` is shared by every model that should be hidden rather
than hard-deleted (Employee, Project). Pair it with `SoftDeleteModelView`
in views.py to get the "hidden on delete" behavior in the admin.
"""

import enum
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette.requests import Request


class Base(DeclarativeBase):
    """Base class for every SQLAlchemy declarative model in the HR example."""


class SoftDeleteMixin:
    """Adds the `deleted_at` column shared by every soft-deletable model.

    A row with `deleted_at IS NULL` is live; any other value means the row
    was "deleted" through the admin. Mix this into a model, then use
    `SoftDeleteModelView` (see views.py) so list/count queries hide trashed
    rows and the delete action stamps this column instead of running DELETE.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None
    )


# ── Enums ────────────────────────────────────────────────────────────────────
# Values mirror the Filament demo's PHP backed enums (App\Enums\*).


class EmploymentType(enum.StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACTOR = "contractor"
    INTERN = "intern"


class LeaveType(enum.StrEnum):
    ANNUAL = "annual"
    SICK = "sick"
    PERSONAL = "personal"
    UNPAID = "unpaid"
    PARENTAL = "parental"


class LeaveStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TAKEN = "taken"
    CANCELLED = "cancelled"


class ProjectStatus(enum.StrEnum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(enum.StrEnum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExpenseCategory(enum.StrEnum):
    TRAVEL = "travel"
    MEALS = "meals"
    SUPPLIES = "supplies"
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    OTHER = "other"


class ExpenseStatus(enum.StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    REIMBURSED = "reimbursed"


# ── Department ───────────────────────────────────────────────────────────────


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    headcount: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    parent: Mapped["Department | None"] = relationship(
        "Department", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Department"]] = relationship(
        "Department", back_populates="parent"
    )
    employees: Mapped[list["Employee"]] = relationship(
        "Employee", back_populates="department"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="department"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


# ── Employee ─────────────────────────────────────────────────────────────────


class Employee(SoftDeleteMixin, Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    avatar: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType), default=EmploymentType.FULL_TIME, nullable=False
    )
    salary: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    department: Mapped["Department | None"] = relationship(
        "Department", back_populates="employees"
    )
    leave_requests: Mapped[list["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="employee",
        foreign_keys="LeaveRequest.employee_id",
    )
    approved_leave_requests: Mapped[list["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="approver",
        foreign_keys="LeaveRequest.approver_id",
    )
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="assignee")
    timesheets: Mapped[list["Timesheet"]] = relationship(
        "Timesheet", back_populates="employee"
    )
    expenses: Mapped[list["Expense"]] = relationship(
        "Expense", back_populates="employee", foreign_keys="Expense.employee_id"
    )
    approved_expenses: Mapped[list["Expense"]] = relationship(
        "Expense", back_populates="approved_by", foreign_keys="Expense.approved_by_id"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


# ── LeaveRequest ─────────────────────────────────────────────────────────────


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=False
    )
    approver_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=True
    )
    type: Mapped[LeaveType] = mapped_column(Enum(LeaveType), nullable=False)
    status: Mapped[LeaveStatus] = mapped_column(
        Enum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    days_requested: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="leave_requests", foreign_keys=[employee_id]
    )
    approver: Mapped["Employee | None"] = relationship(
        "Employee",
        back_populates="approved_leave_requests",
        foreign_keys=[approver_id],
    )

    async def __admin_repr__(self, request: Request) -> str:
        return f"{self.employee.name}: {self.type.value} ({self.start_date} → {self.end_date})"


# ── Project ──────────────────────────────────────────────────────────────────


class Project(SoftDeleteMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    department_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.PLANNING, nullable=False
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False
    )
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    spent: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    estimated_hours: Mapped[Decimal] = mapped_column(Numeric(8, 1), default=0)
    actual_hours: Mapped[Decimal] = mapped_column(Numeric(8, 1), default=0)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    plan: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    department: Mapped["Department | None"] = relationship(
        "Department", back_populates="projects"
    )
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="project")
    timesheets: Mapped[list["Timesheet"]] = relationship(
        "Timesheet", back_populates="project"
    )
    expenses: Mapped[list["Expense"]] = relationship(
        "Expense", back_populates="project"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


# ── Task ─────────────────────────────────────────────────────────────────────


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False
    )
    assigned_to: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.BACKLOG, nullable=False
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False
    )
    estimated_hours: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 1), nullable=True
    )
    actual_hours: Mapped[Decimal] = mapped_column(Numeric(6, 1), default=0)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    labels: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    assignee: Mapped["Employee | None"] = relationship(
        "Employee", back_populates="tasks", foreign_keys=[assigned_to]
    )
    timesheets: Mapped[list["Timesheet"]] = relationship(
        "Timesheet", back_populates="task"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.title


# ── Timesheet ────────────────────────────────────────────────────────────────


class Timesheet(Base):
    __tablename__ = "timesheets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=False
    )
    task_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    hours: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_billable: Mapped[bool] = mapped_column(default=True)
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="timesheets")
    task: Mapped["Task | None"] = relationship("Task", back_populates="timesheets")
    project: Mapped["Project"] = relationship("Project", back_populates="timesheets")

    async def __admin_repr__(self, request: Request) -> str:
        return f"{self.employee.name} — {self.date} ({self.hours}h)"


# ── Expense / ExpenseLine ────────────────────────────────────────────────────


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=False
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    expense_number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    status: Mapped[ExpenseStatus] = mapped_column(
        Enum(ExpenseStatus), default=ExpenseStatus.DRAFT, nullable=False
    )
    category: Mapped[ExpenseCategory] = mapped_column(
        Enum(ExpenseCategory), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by_id: Mapped[int | None] = mapped_column(
        "approved_by", Integer, ForeignKey("employees.id"), nullable=True
    )
    receipt_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    employee: Mapped["Employee"] = relationship(
        "Employee", back_populates="expenses", foreign_keys=[employee_id]
    )
    project: Mapped["Project | None"] = relationship(
        "Project", back_populates="expenses"
    )
    approved_by: Mapped["Employee | None"] = relationship(
        "Employee",
        back_populates="approved_expenses",
        foreign_keys=[approved_by_id],
    )
    expense_lines: Mapped[list["ExpenseLine"]] = relationship(
        "ExpenseLine", back_populates="expense", cascade="all, delete-orphan"
    )

    async def __admin_repr__(self, request: Request) -> str:
        return self.expense_number


class ExpenseLine(Base):
    __tablename__ = "expense_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expense_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("expenses.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    expense: Mapped["Expense"] = relationship("Expense", back_populates="expense_lines")

    async def __admin_repr__(self, request: Request) -> str:
        return f"{self.description} x{self.quantity}"
