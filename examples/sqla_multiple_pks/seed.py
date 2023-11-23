from sqlalchemy.orm import Session

from . import engine
from .models import Course, Enrollment, Student


def fill_db():
    with Session(engine) as session:
        session.add_all(
            [
                Student(id=1, name="John Doe"),
                Student(id=2, name="Jane Smith"),
                Student(id=3, name="Bob Wilson"),
            ]
        )

        session.add_all(
            [
                Course(id=1, name="Introduction to Computer Science"),
                Course(id=2, name="Algorithms and Data Structures"),
                Course(id=3, name="Database Systems"),
            ]
        )
        session.add_all(
            [
                Enrollment(
                    student_id=1,
                    course_id=1,
                    grade="A",
                    instructor_comments="Great work!",
                ),
                Enrollment(
                    student_id=2,
                    course_id=2,
                    grade="B",
                    instructor_comments="Good effort",
                ),
                Enrollment(
                    student_id=1,
                    course_id=3,
                    grade="B+",
                    instructor_comments="Study more for the final.",
                ),
                Enrollment(
                    student_id=2,
                    course_id=1,
                    grade="A-",
                    instructor_comments="Excellent improvement!",
                ),
                Enrollment(
                    student_id=3,
                    course_id=2,
                    grade="C+",
                    instructor_comments="See me to discuss.",
                ),
                Enrollment(
                    student_id=2,
                    course_id=3,
                    grade="A",
                    instructor_comments="Outstanding work!",
                ),
                Enrollment(
                    student_id=3,
                    course_id=1,
                    grade="B",
                    instructor_comments="Good work.",
                ),
                Enrollment(
                    student_id=1,
                    course_id=2,
                    grade="A-",
                    instructor_comments="Nice improvement.",
                ),
            ]
        )

        session.commit()
