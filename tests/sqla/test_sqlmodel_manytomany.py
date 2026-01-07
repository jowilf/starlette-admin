"""
Test SQLModel with MANYTOMANY relationships using association tables.
This verifies that the FK population fix doesn't break association tables.
"""

from typing import List, Optional

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.engine import Engine
from sqlmodel import Field, Relationship, Session, SQLModel, select
from starlette.applications import Starlette
from starlette_admin.contrib.sqlmodel import Admin, ModelView

from tests.sqla.utils import get_test_engine

pytestmark = pytest.mark.asyncio


# Association table
student_course_association = Table(
    "student_course_assoc",
    SQLModel.metadata,
    Column("student_id", Integer, ForeignKey("student.id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("course.id"), primary_key=True),
)


class Student(SQLModel, table=True):
    """Student with MANYTOMANY courses"""

    id: Optional[int] = Field(None, primary_key=True)
    name: str

    # MANYTOMANY - no FK columns on Student table
    courses: List["Course"] = Relationship(
        back_populates="students",
        sa_relationship_kwargs={"secondary": student_course_association},
    )


class Course(SQLModel, table=True):
    """Course with MANYTOMANY students"""

    id: Optional[int] = Field(None, primary_key=True)
    title: str

    # MANYTOMANY - no FK columns on Course table
    students: List[Student] = Relationship(
        back_populates="courses",
        sa_relationship_kwargs={"secondary": student_course_association},
    )


@pytest.fixture
def engine() -> Engine:
    _engine = get_test_engine()
    SQLModel.metadata.create_all(_engine)
    yield _engine
    SQLModel.metadata.drop_all(_engine)


@pytest.fixture
def session(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


@pytest.fixture
def admin(engine: Engine):
    admin = Admin(engine)
    admin.add_view(ModelView(Student))
    admin.add_view(ModelView(Course))
    return admin


@pytest.fixture
def app(admin: Admin):
    app = Starlette()
    admin.mount_to(app)
    return app


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


async def test_create_student_with_courses_manytomany(
    client: AsyncClient, session: Session
):
    """
    Test creating Student with courses (MANYTOMANY via association table).
    This should work because there are no FK columns on Student or Course tables.
    """
    # Setup: Create courses
    course1 = Course(title="Python 101")
    course2 = Course(title="SQL Basics")
    session.add_all([course1, course2])
    session.commit()

    # Test: Create student with multiple courses
    response = await client.post(
        "/admin/student/create",
        data={
            "name": "Alice Johnson",
            "courses": [course1.id, course2.id],
        },
        follow_redirects=False,
    )

    # Should succeed (303 redirect)
    assert response.status_code == 303, f"Expected 303, got {response.status_code}"

    # Verify in database
    # In MySQL with REPEATABLE READ isolation, we need to end the current
    # transaction to see changes committed by the app session
    session.commit()
    stmt = select(Student).where(Student.name == "Alice Johnson")
    student = session.exec(stmt).one()
    assert student is not None
    assert len(student.courses) == 2
    assert sorted([c.title for c in student.courses]) == ["Python 101", "SQL Basics"]

    # Verify association table entries exist
    session.execute(select(student_course_association))
    rows = session.execute(select(student_course_association)).fetchall()
    assert len(rows) == 2  # Two associations


async def test_edit_student_courses_manytomany(client: AsyncClient, session: Session):
    """
    Test editing Student's courses (MANYTOMANY).
    """
    # Setup
    course1 = Course(id=1, title="Python 101")
    course2 = Course(id=2, title="SQL Basics")
    course3 = Course(id=3, title="Web Development")
    student = Student(id=1, name="Bob Smith", courses=[course1, course2])
    session.add_all([course1, course2, course3, student])
    session.commit()

    # Test: Edit student to change courses
    response = await client.post(
        "/admin/student/edit/1",
        data={
            "name": "Bob Smith",
            "courses": [2, 3],  # Remove course 1, add course 3
        },
        follow_redirects=False,
    )

    # Should succeed
    assert response.status_code == 303

    # Verify courses updated
    session.expire(student)
    session.refresh(student)
    assert len(student.courses) == 2
    assert sorted([c.title for c in student.courses]) == [
        "SQL Basics",
        "Web Development",
    ]


async def test_create_course_with_students_manytomany(
    client: AsyncClient, session: Session
):
    """
    Test creating Course with students (reverse MANYTOMANY).
    """
    # Setup: Create students
    student1 = Student(name="Alice")
    student2 = Student(name="Bob")
    session.add_all([student1, student2])
    session.commit()

    # Test: Create course with multiple students
    response = await client.post(
        "/admin/course/create",
        data={
            "title": "Advanced Python",
            "students": [student1.id, student2.id],
        },
        follow_redirects=False,
    )

    # Should succeed
    assert response.status_code == 303

    # Verify in database
    # In MySQL with REPEATABLE READ isolation, we need to end the current
    # transaction to see changes committed by the app session
    session.commit()
    stmt = select(Course).where(Course.title == "Advanced Python")
    course = session.exec(stmt).one()
    assert len(course.students) == 2
    assert sorted([s.name for s in course.students]) == ["Alice", "Bob"]


async def test_create_student_without_courses(client: AsyncClient, session: Session):
    """
    Test creating Student without any courses (empty MANYTOMANY).
    """
    response = await client.post(
        "/admin/student/create",
        data={
            "name": "Charlie Brown",
            # courses not provided (empty)
        },
        follow_redirects=False,
    )

    # Should succeed
    assert response.status_code == 303

    # Verify student created with no courses
    stmt = select(Student).where(Student.name == "Charlie Brown")
    student = session.exec(stmt).one()
    assert len(student.courses) == 0
