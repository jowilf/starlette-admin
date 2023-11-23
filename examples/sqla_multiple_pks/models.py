import datetime
from typing import List

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from starlette.requests import Request

from . import Base


class Student(Base):
    __tablename__ = "student"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="student")

    def __admin_repr__(self, request: Request):
        return self.name


class Course(Base):
    __tablename__ = "course"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    enrollments: Mapped[List["Enrollment"]] = relationship(back_populates="course")

    def __admin_repr__(self, request: Request):
        return self.name


class Enrollment(Base):
    __tablename__ = "enrollment"

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), primary_key=True)

    grade: Mapped[str]
    date_enrolled: Mapped[datetime.date] = mapped_column(default=datetime.date.today)
    instructor_comments: Mapped[str] = mapped_column(Text)

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")
