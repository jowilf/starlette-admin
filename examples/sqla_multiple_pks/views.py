from starlette_admin import EnumField
from starlette_admin.contrib.sqla import ModelView

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
