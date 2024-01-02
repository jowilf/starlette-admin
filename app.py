from sqlalchemy import (
    ForeignKey,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqla import Admin, ModelView


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employee"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    type: Mapped[
        str
    ]  # This column is used for polymorphic identity to determine the type of the object.

    __mapper_args__ = {
        "polymorphic_identity": "employee",  # This is the default value for Employee.
        "polymorphic_on": "type",  # This is the column used for polymorphic identity.
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r})"


class Engineer(
    Employee
):  # Inherits from Employee because every Engineer is an Employee.
    __tablename__ = "engineer"
    id: Mapped[int] = mapped_column(ForeignKey("employee.id"), primary_key=True)
    # Engineer specific data, could be so much more.
    engineer_related_data: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": "engineer",  # This is the value used for Engineer.
    }


class Manager(Employee):
    __tablename__ = "manager"
    id: Mapped[int] = mapped_column(ForeignKey("employee.id"), primary_key=True)
    # Manager specific data, could be so much more.
    manager_related_data: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": "manager",  # This is the value used for Manager.
    }


class EmployeeView(ModelView):
    label = "Employees"
    name = "Employee"
    fields = [
        Employee.id,
        Employee.first_name,
        Employee.last_name,
    ]


class EngineerView(
    ModelView
):  # Inherits from ModelView because we want to use the default ModelView.
    label = "Engineers"
    name = "Engineer"
    fields = [
        Engineer.id,
        Engineer.first_name,
        Engineer.last_name,
        Engineer.engineer_related_data,
    ]


class ManagerView(ModelView):
    label = "Managers"
    name = "Manager"
    # I'm not including the `type` column because it doesn't meant to be edited. It will be set automatically by the ORM.
    fields = [
        Manager.id,
        Manager.first_name,
        Manager.last_name,
        Manager.manager_related_data,
    ]


engine = create_engine(
    "sqlite:///db.sqlite3",
    connect_args={"check_same_thread": False},
    echo=True,
)
session = sessionmaker(bind=engine, autoflush=False)


def init_database() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with session() as db:
        db.add_all(
            [
                Engineer(
                    first_name="Jon",
                    last_name="Snow",
                    engineer_related_data="Engineer related data",
                ),
                Engineer(
                    first_name="Maester",
                    last_name="Aemon",
                    engineer_related_data="Engineer related data",
                ),
                Manager(
                    first_name="Lord",
                    last_name="Commander",
                    manager_related_data="Manager related data",
                ),
                Manager(
                    first_name="Lord",
                    last_name="Steward",
                    manager_related_data="Manager related data",
                ),
            ]
        )
        db.commit()
        # Count of each table
        employees = db.query(Employee).all()
        employees = len(employees)
        engineers = db.query(Engineer).all()
        engineers = len(engineers)
        managers = db.query(Manager).all()
        managers = len(managers)
        print("All employees:", employees)
        print("All engineers:", engineers)
        print("All managers:", managers)


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
admin = Admin(engine, title="Example: Polymorphic Association")

# Add views
admin.add_view(EmployeeView(model=Employee))
admin.add_view(EngineerView(model=Engineer))
admin.add_view(ManagerView(model=Manager))

# Mount admin
admin.mount_to(app)
