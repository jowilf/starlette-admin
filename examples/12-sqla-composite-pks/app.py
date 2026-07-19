import datetime
import os
from contextlib import asynccontextmanager

import uvicorn
from sqlalchemy import ForeignKey, Text, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin import EnumField, flash
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.exceptions import FormValidationError

DATABASE_FILE = "12_sqla_composite_pks.sqlite"
engine = create_engine(
    "sqlite:///" + DATABASE_FILE,
    connect_args={"check_same_thread": False},
    echo=True,
)


class Base(DeclarativeBase):
    pass


# ── Models ──────────────────────────────────────────────────────────────────────


class Student(Base):
    __tablename__ = "student"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")

    def __admin_repr__(self, request: Request) -> str:
        return self.name


class Course(Base):
    __tablename__ = "course"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")

    def __admin_repr__(self, request: Request) -> str:
        return self.name


class Enrollment(Base):
    __tablename__ = "enrollment"

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), primary_key=True)

    grade: Mapped[str | None]
    date_enrolled: Mapped[datetime.date] = mapped_column(default=datetime.date.today)
    instructor_comments: Mapped[str | None] = mapped_column(Text)

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")


# ── Views ───────────────────────────────────────────────────────────────────────

GRADES = [
    ("A", "A"),
    ("A-", "A-"),
    ("B+", "B+"),
    ("B", "B"),
    ("B-", "B-"),
    ("C+", "C+"),
    ("C", "C"),
    ("C-", "C-"),
    ("D+", "D+"),
    ("D", "D"),
    ("F", "F"),
]


class StudentView(ModelView):
    fields = ["id", "name"]


class CourseView(ModelView):
    fields = ["id", "name"]


class EnrollmentView(ModelView):
    fields = [
        "student",
        "course",
        "date_enrolled",
        EnumField("grade", choices=GRADES, select2=False),
        "instructor_comments",
    ]

    async def handle_exception(self, request: Request, exc: Exception) -> None:
        if isinstance(
            exc, IntegrityError
        ) and "enrollment.student_id, enrollment.course_id" in str(exc.orig):
            flash(
                request,
                "This student is already enrolled in that course. To update the grade or instructor comments, edit the existing enrollment instead.",
                "warning",
            )
            raise FormValidationError(
                {
                    "student": "Already enrolled in this course.",
                    "course": "Already enrolled in this course.",
                }
            )
        await super().handle_exception(request, exc)


# ── App ─────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(_: Starlette):
    from seed import fill_db

    first_run = not os.path.exists(DATABASE_FILE)
    Base.metadata.create_all(engine)
    if first_run:
        fill_db()
    yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route(
            "/",
            lambda _: HTMLResponse('<a href="/admin/">Go to Admin →</a>'),
        )
    ],
)

admin = Admin(
    engine, title="Example: Composite PKs", secret_key="dev-only-change-me", debug=True
)

admin.add_view(StudentView(Student, icon="fa fa-user-graduate"))
admin.add_view(CourseView(Course, icon="fa fa-book"))
admin.add_view(EnrollmentView(Enrollment, icon="fa fa-clipboard-list"))

admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True, reload_dirs=["../.."])
