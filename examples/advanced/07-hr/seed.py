"""Standalone seed script for the 07-hr example.

Generates a Faker dataset and writes it straight to the SQLite database
through the same SQLAlchemy models the app uses. No running app or HTTP
round trip is required.

Usage:
    uv run seed.py                # default volumes
    uv run seed.py --scale 5      # about five times as much data
    uv run seed.py --scale 0.2    # a small dataset for quick local testing

Departments come from a fixed org chart (see `ORG_CHART`) and do not scale:
a company's reporting structure does not grow with headcount here. Every
other entity's volume is `round(base_count * scale)`, see `BASE_COUNTS` and
`scaled_counts()`. `scale` is the single knob that controls how much data
comes out, and turning it up always means more of everything.

Employees are seeded without an avatar; the UI falls back to initials.
"""

import argparse
import random
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from faker import Faker
from models import (
    Base,
    Department,
    Employee,
    EmploymentType,
    Expense,
    ExpenseCategory,
    ExpenseLine,
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
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DATABASE_FILE = "advanced_07_hr.sqlite"

# Fixed org chart: (name, parent name, color). Parents are listed before
# their children so each parent's `Department` is known when a child is
# built. The eight names with children below (Executive plus the seven
# division heads) are the umbrella nodes an org chart draws as boxes with a
# reporting line down; the other eighteen are the leaf teams most employees
# actually belong to (see `pick_department`).
ORG_CHART: list[tuple[str, str | None, str]] = [
    ("Executive", None, "#6b7280"),
    ("Engineering", "Executive", "#3b82f6"),
    ("Platform", "Engineering", "#0ea5e9"),
    ("Backend", "Engineering", "#2563eb"),
    ("Frontend", "Engineering", "#8b5cf6"),
    ("Mobile", "Engineering", "#6366f1"),
    ("QA & Release", "Engineering", "#14b8a6"),
    ("Data & Analytics", "Engineering", "#0891b2"),
    ("Security", "Engineering", "#ef4444"),
    ("Sales", "Executive", "#22c55e"),
    ("Enterprise Sales", "Sales", "#16a34a"),
    ("SMB Sales", "Sales", "#4ade80"),
    ("Sales Operations", "Sales", "#84cc16"),
    ("Marketing", "Executive", "#f59e0b"),
    ("Growth", "Marketing", "#fbbf24"),
    ("Brand & Content", "Marketing", "#f97316"),
    ("Customer Success", "Executive", "#06b6d4"),
    ("Support", "Customer Success", "#67e8f9"),
    ("Onboarding", "Customer Success", "#22d3ee"),
    ("Finance", "Executive", "#a855f7"),
    ("Accounting", "Finance", "#c084fc"),
    ("Procurement", "Finance", "#9333ea"),
    ("People Ops", "Executive", "#ec4899"),
    ("Recruiting", "People Ops", "#f472b6"),
    ("Operations", "Executive", "#eab308"),
    ("IT & Workplace", "Operations", "#facc15"),
]

SKILLS = [
    "python", "typescript", "rust", "go", "sql", "postgres", "sqlalchemy",
    "react", "kubernetes", "terraform", "aws", "gcp", "ci-cd", "grafana",
    "leadership", "mentoring", "negotiation", "crm", "seo", "copywriting",
    "figma", "accounting", "recruiting", "public-speaking",
]  # fmt: skip

TASK_LABELS = [
    "backend", "frontend", "infra", "design", "bug", "research",
    "customer", "urgent", "tech-debt", "docs",
]  # fmt: skip

EMPLOYMENT_TYPES = [
    ("full_time", 72), ("part_time", 10), ("contractor", 12), ("intern", 6),
]  # fmt: skip

PROJECT_STATUSES = [
    ("planning", 20), ("active", 40), ("on_hold", 10),
    ("completed", 25), ("cancelled", 5),
]  # fmt: skip

TASK_STATUSES = [
    ("backlog", 20), ("todo", 20), ("in_progress", 20),
    ("in_review", 10), ("completed", 25), ("cancelled", 5),
]  # fmt: skip

PRIORITIES = [("low", 25), ("medium", 45), ("high", 22), ("critical", 8)]

LEAVE_TYPES = [
    ("annual", 45), ("sick", 25), ("personal", 15),
    ("unpaid", 5), ("parental", 10),
]  # fmt: skip

LEAVE_STATUSES = [
    ("pending", 25), ("approved", 40), ("rejected", 10),
    ("taken", 20), ("cancelled", 5),
]  # fmt: skip

EXPENSE_CATEGORIES = [
    ("travel", 25), ("meals", 20), ("supplies", 15),
    ("equipment", 15), ("software", 20), ("other", 5),
]  # fmt: skip

EXPENSE_STATUSES = [
    ("draft", 15), ("submitted", 30), ("approved", 25),
    ("rejected", 10), ("reimbursed", 20),
]  # fmt: skip


# ── Global scale config ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class SeedConfig:
    """The one knob every entity count scales from.

    `scale=1.0` produces the volumes in `BASE_COUNTS` as-is; every count is
    `round(base_count * scale)`, so `scale=3` is roughly three times as much
    data across every entity, and `scale=0.2` is a fifth as much. Increasing
    `scale` always means more records, proportionally, for all of them.
    """

    scale: float = 1.0
    seed: int = 42
    database: str = DATABASE_FILE
    reset: bool = True


# Volumes at scale=1.0. `Department` is not listed: the org chart above is a
# fixed structure, not a scaled quantity.
BASE_COUNTS: dict[str, int] = {
    "employees": 300,
    "projects": 30,
    "tasks": 150,
    "timesheets": 500,
    "leave_requests": 80,
    "expenses": 100,
}

MIN_COUNTS: dict[str, int] = {
    "employees": 5,
    "projects": 2,
    "tasks": 5,
    "timesheets": 5,
    "leave_requests": 3,
    "expenses": 2,
}


def scaled_counts(config: SeedConfig) -> dict[str, int]:
    """Every entity's volume, proportional to `config.scale`."""
    return {
        key: max(MIN_COUNTS[key], round(base * config.scale))
        for key, base in BASE_COUNTS.items()
    }


# ── Small helpers ────────────────────────────────────────────────────────────


def pick(rng: random.Random, table: list[tuple[str, int]]) -> str:
    values, weights = zip(*table)
    return rng.choices(values, weights=weights, k=1)[0]


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def build_records(label: str, total: int, builder: Any) -> list[Any]:
    """Call `builder(index)` `total` times, printing progress as it goes."""
    items = []
    for i in range(total):
        items.append(builder(i))
        if (i + 1) % 200 == 0 or i + 1 == total:
            print(f"\r  {label}: {i + 1}/{total}", end="", flush=True)
    print()
    return items


# ── Record builders ──────────────────────────────────────────────────────────


def build_department(
    rng: random.Random, fake: Faker, name: str, color: str, parent: Department | None
) -> Department:
    return Department(
        name=name,
        slug=slugify(name),
        description=fake.sentence(nb_words=10),
        budget=Decimal(rng.randint(150, 3000) * 1000),
        headcount=0,  # recomputed from real assignments once employees exist
        color=color,
        is_active=True,
        parent=parent,
    )


def pick_department(
    rng: random.Random,
    leaf_departments: list[Department],
    parent_departments: list[Department],
) -> Department:
    """Most employees belong to a leaf team; a small slice reports directly
    to a division head (an umbrella department with children), the way a
    VP's own direct reports would sit a level above any one team.
    """
    if parent_departments and rng.random() < 0.08:
        return rng.choice(parent_departments)
    return rng.choice(leaf_departments)


def build_employee(
    rng: random.Random,
    fake: Faker,
    index: int,
    department: Department,
) -> Employee:
    first, last = fake.first_name(), fake.last_name()
    local_part = re.sub(r"[^a-z0-9]+", ".", f"{first}.{last}".lower()).strip(".")
    employment_type = pick(rng, EMPLOYMENT_TYPES)
    salary_range = {
        "full_time": (55, 230),
        "part_time": (28, 90),
        "contractor": (70, 210),
        "intern": (30, 45),
    }[employment_type]
    # Contractors are usually billed hourly, so most have no annual salary.
    salary = None
    if not (employment_type == "contractor" and rng.random() < 0.8):
        salary = Decimal(rng.randint(*salary_range) * 1000)
    skills = rng.sample(SKILLS, k=rng.randint(0, 6))

    return Employee(
        name=f"{first} {last}",
        email=f"{local_part}.{index}@example.com",
        phone=fake.phone_number() if rng.random() < 0.85 else None,
        date_of_birth=fake.date_of_birth(minimum_age=20, maximum_age=64),
        hire_date=fake.date_between(start_date="-12y"),
        job_title=fake.job(),
        employment_type=EmploymentType(employment_type),
        salary=salary,
        skills=skills or None,
        is_active=rng.random() < 0.97,
        department=department,
    )


def build_project(
    rng: random.Random, fake: Faker, index: int, department: Department
) -> Project:
    name = fake.catch_phrase().title()
    status = pick(rng, PROJECT_STATUSES)
    start = fake.date_between(start_date="-3y", end_date="+2M")
    budget = rng.randint(20, 500) * 1000
    estimated = rng.randint(100, 2000)
    progress = {
        "planning": 0.0,
        "active": rng.uniform(0.1, 0.9),
        "on_hold": rng.uniform(0.1, 0.7),
        "completed": rng.uniform(0.9, 1.2),
        "cancelled": rng.uniform(0.0, 0.6),
    }[status]
    end_date: date | None = None
    if status in ("completed", "cancelled"):
        end_date = start + timedelta(days=rng.randint(30, 540))
    return Project(
        name=name,
        slug=f"{slugify(name)}-{index}",
        description=fake.paragraph(nb_sentences=2),
        status=ProjectStatus(status),
        priority=TaskPriority(pick(rng, PRIORITIES)),
        department=department,
        budget=Decimal(budget),
        spent=Decimal(f"{budget * progress:.2f}"),
        estimated_hours=Decimal(f"{estimated}.0"),
        actual_hours=Decimal(f"{estimated * progress:.1f}"),
        start_date=start,
        end_date=end_date,
        plan=(
            {"milestones": [fake.bs() for _ in range(rng.randint(2, 4))]}
            if rng.random() < 0.3
            else None
        ),
    )


def build_task(
    rng: random.Random, fake: Faker, project: Project, employees: list[Employee]
) -> Task:
    status = pick(rng, TASK_STATUSES)
    task = Task(
        title=fake.sentence(nb_words=6).rstrip("."),
        project=project,
        status=TaskStatus(status),
        priority=TaskPriority(pick(rng, PRIORITIES)),
        estimated_hours=Decimal(f"{rng.randint(2, 80) / 2:.1f}"),
        actual_hours=Decimal("0.0"),
        sort=rng.randint(0, 50),
        assignee=rng.choice(employees) if rng.random() < 0.85 else None,
        description=fake.paragraph(nb_sentences=2) if rng.random() < 0.5 else None,
        due_date=(
            fake.date_between(start_date="-3M", end_date="+3M")
            if rng.random() < 0.7
            else None
        ),
        labels=(
            rng.sample(TASK_LABELS, k=rng.randint(1, 3)) if rng.random() < 0.4 else None
        ),
    )
    if status == "completed":
        task.completed_at = fake.date_time_between(start_date="-6M", end_date="now")
        task.actual_hours = Decimal(f"{rng.randint(2, 90) / 2:.1f}")
    return task


def build_timesheet(
    rng: random.Random,
    fake: Faker,
    employees: list[Employee],
    projects: list[Project],
    tasks: list[Task],
) -> Timesheet:
    # Most entries are logged against a task; the rest go to a project only.
    # Reusing the task's own project keeps the two foreign keys coherent.
    if tasks and rng.random() < 0.6:
        task = rng.choice(tasks)
        project = task.project
    else:
        task, project = None, rng.choice(projects)
    hours = (Decimal(rng.randint(1, 18)) / 2).quantize(Decimal("0.1"))
    rate = Decimal(rng.choice([0, 0, 60, 75, 90, 110, 140]))
    return Timesheet(
        employee=rng.choice(employees),
        project=project,
        task=task,
        date=fake.date_between(start_date="-1y"),
        hours=hours,
        minutes=rng.choice([0, 0, 15, 30, 45]),
        is_billable=rng.random() < 0.8,
        hourly_rate=rate,
        total_cost=(hours * rate).quantize(Decimal("0.01")),
        description=fake.sentence(nb_words=8) if rng.random() < 0.5 else None,
    )


def build_leave_request(
    rng: random.Random, fake: Faker, employees: list[Employee]
) -> LeaveRequest:
    status = pick(rng, LEAVE_STATUSES)
    start = fake.date_between(start_date="-6M", end_date="+6M")
    days = rng.randint(1, 10)
    leave_request = LeaveRequest(
        employee=rng.choice(employees),
        type=LeaveType(pick(rng, LEAVE_TYPES)),
        status=LeaveStatus(status),
        start_date=start,
        end_date=start + timedelta(days=days - 1),
        days_requested=Decimal(days),
        reason=fake.sentence(nb_words=8),
    )
    if status in ("approved", "rejected", "taken"):
        leave_request.approver = rng.choice(employees)
        reviewed = datetime.combine(
            start - timedelta(days=rng.randint(1, 30)), datetime.min.time()
        ) + timedelta(hours=rng.randint(8, 18))
        leave_request.reviewed_at = reviewed
        if rng.random() < 0.4:
            leave_request.reviewer_notes = fake.sentence(nb_words=6)
    return leave_request


def build_expense(
    rng: random.Random,
    fake: Faker,
    index: int,
    employees: list[Employee],
    projects: list[Project],
) -> Expense:
    status = pick(rng, EXPENSE_STATUSES)
    lines = []
    for _ in range(rng.randint(1, 3)):
        quantity = rng.randint(1, 5)
        unit_price = (Decimal(rng.randint(500, 40000)) / 100).quantize(Decimal("0.01"))
        lines.append(
            ExpenseLine(
                description=fake.sentence(nb_words=4).rstrip("."),
                quantity=quantity,
                unit_price=unit_price,
                amount=(unit_price * quantity).quantize(Decimal("0.01")),
                date=fake.date_between(start_date="-1y"),
            )
        )
    # The real app recomputes this from the expense lines after create/edit
    # (see ExpenseView._recompute_total_amount in views.py); done directly
    # here since this script writes rows without going through that hook.
    expense = Expense(
        employee=rng.choice(employees),
        project=rng.choice(projects) if rng.random() < 0.7 else None,
        expense_number=f"EXP-{2000 + index}",
        status=ExpenseStatus(status),
        category=ExpenseCategory(pick(rng, EXPENSE_CATEGORIES)),
        description=fake.sentence(nb_words=8),
        total_amount=sum((line.amount for line in lines), Decimal("0")),
        notes=fake.sentence(nb_words=6) if rng.random() < 0.3 else None,
        expense_lines=lines,
    )
    if status != "draft":
        submitted = fake.date_time_between(start_date="-1y", end_date="now")
        expense.submitted_at = submitted
        if status in ("approved", "reimbursed"):
            expense.approved_at = submitted + timedelta(days=rng.randint(1, 14))
            expense.approved_by = rng.choice(employees)
    return expense


# ── Main ─────────────────────────────────────────────────────────────────────


def seed(config: SeedConfig) -> None:
    rng = random.Random(config.seed)
    Faker.seed(config.seed)
    fake = Faker()
    counts = scaled_counts(config)
    started = time.perf_counter()

    db_path = Path(config.database)
    if config.reset:
        db_path.unlink(missing_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Departments are built sequentially: a child's `parent=` needs the
        # `Department` instance a parent row a few lines up already created.
        departments_by_name: dict[str, Department] = {}
        for name, parent_name, color in ORG_CHART:
            department = build_department(
                rng, fake, name, color, departments_by_name.get(parent_name)
            )
            departments_by_name[name] = department
            session.add(department)
        session.flush()
        print(f"  departments: {len(ORG_CHART)}/{len(ORG_CHART)}")

        leaf_departments = [d for d in departments_by_name.values() if not d.children]
        parent_departments = [d for d in departments_by_name.values() if d.children]

        employees = build_records(
            "employees",
            counts["employees"],
            lambda i: build_employee(
                rng,
                fake,
                i,
                pick_department(rng, leaf_departments, parent_departments),
            ),
        )
        session.add_all(employees)
        session.flush()

        # Real headcount, now that every employee has a department.
        for department in departments_by_name.values():
            department.headcount = len(department.employees)

        # Soft-delete a small slice, so SoftDeleteModelView's "hidden on
        # delete" behavior is observable on a fresh dataset.
        for employee in rng.sample(employees, k=max(1, len(employees) // 50)):
            employee.deleted_at = fake.date_time_between(
                start_date="-6M", end_date="now"
            )

        all_departments = list(departments_by_name.values())
        projects = build_records(
            "projects",
            counts["projects"],
            lambda i: build_project(rng, fake, i, rng.choice(all_departments)),
        )
        session.add_all(projects)
        session.flush()
        for project in rng.sample(projects, k=max(1, len(projects) // 25)):
            project.deleted_at = fake.date_time_between(
                start_date="-6M", end_date="now"
            )

        tasks = build_records(
            "tasks",
            counts["tasks"],
            lambda _: build_task(rng, fake, rng.choice(projects), employees),
        )
        session.add_all(tasks)
        session.flush()

        timesheets = build_records(
            "timesheets",
            counts["timesheets"],
            lambda _: build_timesheet(rng, fake, employees, projects, tasks),
        )
        session.add_all(timesheets)

        leave_requests = build_records(
            "leave requests",
            counts["leave_requests"],
            lambda _: build_leave_request(rng, fake, employees),
        )
        session.add_all(leave_requests)

        expenses = build_records(
            "expenses",
            counts["expenses"],
            lambda i: build_expense(rng, fake, i, employees, projects),
        )
        session.add_all(expenses)

        session.commit()

    elapsed = time.perf_counter() - started
    total = len(ORG_CHART) + sum(counts.values())
    print(f"Done: {total} records created in {elapsed:.1f}s -> {db_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the 07-hr example database directly through SQLAlchemy."
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Global multiplier every entity count scales from proportionally "
        "(the department org chart is fixed and does not scale); "
        "higher means more records (default: %(default)s).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible data (default: %(default)s).",
    )
    parser.add_argument(
        "--database",
        default=DATABASE_FILE,
        help="SQLite file to write to (default: %(default)s).",
    )
    parser.add_argument(
        "--no-reset",
        dest="reset",
        action="store_false",
        help="Append to the existing database instead of wiping it first "
        "(unique fields like email/slug may then collide across runs).",
    )
    args = parser.parse_args()
    seed(
        SeedConfig(
            scale=args.scale,
            seed=args.seed,
            database=args.database,
            reset=args.reset,
        )
    )


if __name__ == "__main__":
    main()
