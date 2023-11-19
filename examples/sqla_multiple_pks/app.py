import os

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin

from . import Base, engine
from .config import DATABASE_FILE
from .models import Course, Enrollment, Student
from .seed import fill_db
from .views import CourseView, EnrollmentView, StudentView


def init_database() -> None:
    first_run = not os.path.exists(DATABASE_FILE)
    print("hellooooo")
    Base.metadata.create_all(engine)
    if first_run:
        fill_db()


app = Starlette(
    routes=[
        Route(
            "/",
            lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        )
    ],
    on_startup=[init_database],
)

# Create admin
admin = Admin(engine, title="Example: Multiple PKs")

# Add views
admin.add_view(StudentView(Student, icon="fa fa-user-graduate"))
admin.add_view(CourseView(Course, icon="fa fa-book"))
admin.add_view(EnrollmentView(Enrollment, icon="fa fa-clipboard-list"))

# Mount admin
admin.mount_to(app)
