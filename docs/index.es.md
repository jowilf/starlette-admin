# Visión General

*Starlette-Admin* es un rápido, hermoso y extensible framework de interfaz administrativa para aplicaciones Starlette/FastAPI.

<p align="center">
<a href="https://github.com/jowilf/starlette-admin/actions/workflows/test.yml">
    <img src="https://github.com/jowilf/starlette-admin/actions/workflows/test.yml/badge.svg" alt="Test suite">
</a>
<a href="https://github.com/jowilf/starlette-admin/actions">
    <img src="https://github.com/jowilf/starlette-admin/actions/workflows/publish.yml/badge.svg" alt="Publish">
</a>
<a href="https://codecov.io/gh/jowilf/starlette-admin">
    <img src="https://codecov.io/gh/jowilf/starlette-admin/branch/main/graph/badge.svg" alt="Codecov">
</a>
<a href="https://pypi.org/project/starlette-admin/">
    <img src="https://badge.fury.io/py/starlette-admin.svg" alt="Package version">
</a>
<a href="https://pypi.org/project/starlette-admin/">
    <img src="https://img.shields.io/pypi/pyversions/starlette-admin?color=2334D058" alt="Supported Python versions">
</a>
</p>

## Empezando

* Revisa [la documentación](https://jowilf.github.io/starlette-admin).
* Prueba la [demostración en vivo](https://starlette-admin-demo.jowilf.com/). ([Código fuente](https://github.com/jowilf/starlette-admin-demo))
* Pruebe los varios ejemplos de uso incluidos en la carpeta [/examples](https://github.com/jowilf/starlette-admin/tree/main/examples)

## Características

- CRUD de cualquier dato con facilidad
- Validación automática de formularios
- Widget de tabla avanzado con [Datatables](https://datatables.net/)
- Búsqueda y filtrado
- Resaltado de búsqueda
- Ordenamiento multi columna
- Exportación de datos a CSV/EXCEL/PDF e impresión con navegador
- Autenticación
- Autorización
- Administrar archivos
- Vistas personalizadas
- ORMs compatibles
    * [SQLAlchemy](https://www.sqlalchemy.org/)
    * [SQLModel](https://sqlmodel.tiangolo.com/)
    * [MongoEngine](http://mongoengine.org/)
    * [ODMantic](https://github.com/art049/odmantic/)
- Backend personalizado ([doc](https://jowilf.github.io/starlette-admin/advanced/base-model-view/), [example](https://github.com/jowilf/starlette-admin/tree/main/examples/custom-backend))


## Instalación

### PIP

```shell
$ pip install starlette-admin
```

### Poetry

```shell
$ poetry add starlette-admin
```

## Ejemplo

Este es un ejemplo simple con el modelo SQLAlchemy

```python
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

Base = declarative_base()
engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})


# Define tu modelo
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String)


Base.metadata.create_all(engine)

app = Starlette()  # FastAPI()

# Crear instancia de admin
admin = Admin(engine, title="Ejemplo: SQLAlchemy")

# Agregar vista
admin.add_view(ModelView(Post))

# Montar admin a tu app
admin.mount_to(app)
```

Acceda a su interfaz de administrador en su navegador en [http://localhost:8000/admin](http://localhost:8000/admin)

## Terceros

*starlette-admin* está construido con otros proyectos de código abierto:

- [Tabler](https://tabler.io/)
- [Datatables](https://datatables.net/)
- [jquery](https://jquery.com/)
- [Select2](https://select2.org/)
- [flatpickr](https://flatpickr.js.org/)
- [moment](http://momentjs.com/)
- [jsoneditor](https://github.com/josdejong/jsoneditor)
- [fontawesome](https://fontawesome.com/)
