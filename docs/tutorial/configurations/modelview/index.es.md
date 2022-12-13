# Configuraciones de ModelView

Hay múltiples opciones disponibles para personalizar su ModelView. Para obtener una lista completa, consulte la documentación de la API para [BaseModelView()][starlette_admin.views.BaseModelView]. Estas son algunas de las opciones más utilizadas:

## Campos

Use la propiedad `fields` para personalizar qué campos incluir en la vista de administración.

```Python hl_lines="21"
from sqlalchemy import JSON, Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from starlette.applications import Starlette
from starlette_admin import TagsField
from starlette_admin.contrib.sqla import Admin, ModelView

Base = declarative_base()
engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    tags = Column(JSON)
    content = Column(Text)


class PostView(ModelView):
    fields = ["id", "title", Post.content, TagsField("tags", label="Tags")]


app = Starlette()

admin = Admin(engine)
admin.add_view(PostView(Post, icon="fa fa-blog"))
admin.mount_to(app)
```

## Exclusiones

Hay varias opciones para ayudarlo a excluir algunos campos de cierta parte de la interfaz de administración.

Las opciones son:

* `exclude_fields_from_list`: Lista de campos para excluir en la página Lista.
* `exclude_fields_from_detail`: Lista de campos para excluir en la página de Detalles.
* `exclude_fields_from_create`: Lista de campos para excluir de la página de Creación.
* `exclude_fields_from_edit`: Lista de campos para excluir de la página de Edición.

```Python
class PostView(ModelView):
    exclude_fields_from_list = [Post.content, Post.tags]
```

## Búsqueda y clasificación

Hay dos opciones disponibles para especificar qué campos se pueden ordenar o buscar.

* `searchable_fields` para la lista de campos de búsqueda
* `sortable_fields` para la lista de campos ordenables

!!! Uso
    ```Python
    class PostView(ModelView):
        sortable_fields = [Post.id, "title"]
        searchable_fields = [Post.id, Post.title, "tags"]
    ```

## Exportando

Puede exportar sus datos desde la página de lista. Las opciones de exportación se pueden configurar por modelo e incluyen las siguientes opciones:

* `export_fields`: Lista de campos a incluir en las exportaciones.
* `export_types`: una lista de tipos de archivo de exportación disponibles.
Las exportaciones disponibles son `['csv', 'excel', 'pdf', 'print']`. Por defecto, todos ellos están activos por defecto.

!!! Ejemplo
    ```Python
    from starlette_admin import ExportType

    class PostView(ModelView):
        export_fields = [Post.id, Post.content, Post.tags]
        export_types = [ExportType.CSV, ExportType.EXCEL]
    ```

## Paginación

Las opciones de paginación en la página de lista se pueden configurar. Las opciones disponibles son:

* `page_size`: número predeterminado de elementos para mostrar en la paginación de la página de lista.
             El valor predeterminado se establece en `10`.
* `page_size_options`: opciones de paginación que se muestran en la página de lista. El valor predeterminado se establece en `[10, 25, 50, 100]`.
      Use `-1` para mostrar Todo


!!! Ejemplo
    ```Python
    class PostView(ModelView):
        page_size = 5
        page_size_options = [5, 10, 25, 50, -1]
    ```

## Plantillas
Los archivos de plantilla se crean con Jinja2 y se pueden reescribir por completo en las configuraciones. Las páginas disponibles son:

* `list_template`: plantilla de vista de lista. El valor predeterminado es `list.html`.
* `detail_template`: Plantilla de vista de detalles. El valor predeterminado es `detail.html`.
* `create_template`: Plantilla de vista de edición. El valor predeterminado es `create.html`.
* `edit_template`: Plantilla de vista de edición. El valor predeterminado es `edit.html`.

!!! Ejemplo
    ```Python
    class PostView(ModelView):
        detail_template = "post_detail.html"
    ```
