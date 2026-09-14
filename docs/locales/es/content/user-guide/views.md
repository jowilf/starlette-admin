---
title: Vistas
description: Aprenda a configurar las vistas de lista y detalle en starlette-admin,
  incluyendo búsqueda, ordenamiento y paginación.
source_hash: 33fc39d0f563908c141e8f5f8dc89dfdff925d4b959ed1d032ee685346daae57
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/views/)
<!-- translation-notice:end -->

# Vistas

`starlette-admin` construye su barra lateral a partir de tres tipos de vista: `ModelView` expone un modelo de base de datos, `CustomView` renderiza una página independiente y `Link` añade un hipervínculo.

## ModelView

Una subclase de `ModelView` es la forma de exponer un modelo de base de datos en el admin. Los atributos de clase y las sobrescrituras de métodos en esa vista definen cómo se ve, cómo se comporta y cómo maneja los datos el recurso.

Cada ejemplo de esta sección usa la siguiente configuración de SQLAlchemy:

```python
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    books: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(back_populates="books")
```

### Uso básico

Para exponer el modelo `Post`, cree una subclase de `ModelView` y configure sus atributos.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

Una clase de vista no hace nada hasta que la registra con una instancia de `Admin`:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///blog.db")
admin = Admin(engine, title="Blog Admin", secret_key="change-me")

# Registrar la vista
admin.add_view(PostView(Post))
```

Consulte [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) para ver un admin ejecutable construido de la misma manera, sobre un modelo `Post`.

Registrar una vista genera interfaces paginadas, ordenables y con capacidad de búsqueda para listar, ver, crear, editar y eliminar registros. Usted no escribe rutas ni plantillas.

!!! note
    Usted importa `ModelView` desde el paquete contrib de su backend, como `starlette_admin.contrib.sqla`, `.beanie`, `.mongoengine`, `.sqlmodel` o `.tortoise`. **Todos los atributos descritos a continuación son idénticos en todos los backends**, por lo que puede cambiar un modelo SQLAlchemy por un documento MongoEngine más adelante sin modificar la lógica de su vista.

### Configuración principal

#### Nomenclatura y enrutamiento

Por defecto, el admin deriva el enrutamiento de URL y las etiquetas de la interfaz del nombre de la clase del modelo. Para el modelo `Post`, utiliza:

* **Clave (key):** `post` (URL: `/admin/post/list`)
* **Etiqueta del menú:** `Posts` (entrada en la barra lateral)
* **Nombre para mostrar:** `Post` (botones de la interfaz como **New Post**)

Cuando los valores derivados no son correctos, sobrescríbalos al registrar la vista o en el constructor.

| Atributo | Descripción | Ejemplo de sobrescritura | Interfaz o URL resultante |
| --- | --- | --- | --- |
| **`key`** | El slug interno y la ruta base de la URL. | `key="blog-post"` | `/admin/blog-post/list` |
| **`menu_label`** | El sustantivo en plural usado en la barra lateral. | `menu_label="Blog Posts"` | **Barra lateral:** Blog Posts |
| **`display_name`** | El sustantivo en singular usado en acciones y formularios. | `display_name="Article"` | **Botones:** New Article |

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

#### Selección y personalización de campos {#field-selection-and-customization}

La lista `fields` define qué atributos del modelo aparecen en la vista de lista, la página de detalle y los formularios. Omita esta lista para exponer todos los atributos del modelo.

Mezcle nombres de campos como cadenas e instancias explícitas de `BaseField` para controlar los widgets, la validación y las etiquetas:

```python
from starlette_admin.fields import (
    StringField,
    TextAreaField,
    BooleanField,
    DateTimeField,
)


class PostView(ModelView):
    fields = [
        "id",
        StringField("title", required=True, maxlength=200),
        TextAreaField("content", rows=10),
        BooleanField("published"),
        DateTimeField("created_at", exclude_from_create=True, exclude_from_edit=True),
    ]
```

!!! note
    El admin detecta la clave primaria por usted. Defina `pk_attr` únicamente cuando la detección falle, por ejemplo en un backend personalizado sin una clave primaria de campo único.

#### Visibilidad contextual de campos

Los campos suelen pertenecer a la lista o a la página de detalle, pero no a un formulario de creación, como ocurre con las marcas de tiempo y los estados gestionados por el sistema. Utilice los atributos `exclude_fields_from_*` para ocultar un campo en superficies específicas:

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Ocultar en superficies específicas
    exclude_fields_from_create = ["published", "created_at"]
    exclude_fields_from_export = ["content"]
```

Los atributos de exclusión disponibles terminan en `_create`, `_edit`, `_list`, `_detail`, `_export` e `_import`.

!!! important
    Para permitir que los usuarios establezcan la clave primaria al crear un registro, lo cual está desactivado por defecto, configure `show_pk_in_forms = True`.

#### Diseño de formularios

Por defecto, `fields` renderiza sus formularios de creación y edición como una lista plana vertical. Para reorganizar la interfaz sin tocar sus definiciones de datos, utilice el atributo `form_layout`.

**La notación abreviada con tuplas**

Para una cuadrícula básica, no necesita importar clases de widgets. Agrupe nombres de campos en una tupla para renderizarlos lado a lado en una misma fila.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" y "price" comparten fila; "description" queda debajo de ellos
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

**Widgets avanzados de diseño**

A medida que sus formularios crezcan, estructúrelos con widgets de diseño. La notación abreviada con tuplas funciona dentro de ellos:

* **`PanelWidget` o `FieldsetWidget`:** Agrupan campos relacionados bajo un encabezado, o permiten hacer colapsable una sección.
* **`TabsWidget`:** Separa categorías distintas de datos, como los detalles de envío y los metadatos SEO, que no necesitan verse al mismo tiempo.

```python
from starlette_admin import TabsWidget


class ProductView(ModelView):
    fields = [
        "name",
        "price",
        "description",
        "sku",
        "weight",
        "shipping_class",
        "meta_title",
        "meta_description",
    ]

    form_layout = [
        TabsWidget(
            tabs=[
                ("Listing", [("name", "price"), "description"]),
                ("Shipping", [("sku", "weight"), "shipping_class"]),
                ("SEO", ["meta_title", "meta_description"]),
            ]
        ),
    ]
```

Consulte [Form Layouts](../advanced/form-layout.md) para filas multicolunma con anchos explícitos, pestañas, contenido estático y comportamiento de control de acceso.

### Funciones de la tabla de datos

#### Búsqueda y ordenamiento {#search-and-sort}

Controle cómo los usuarios encuentran y ordenan los datos con `searchable_fields` y `sortable_fields`.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ["title", "content"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [
        ("created_at", True)
    ]  # Ordenar del más reciente al más antiguo
```

* **`searchable_fields`**: Activa el generador de filtros y el cuadro de búsqueda global. La búsqueda global ejecuta una consulta de texto completo sobre estos campos.
* **`sortable_fields`**: Restringe qué encabezados de columna pueden usar los usuarios para ordenar. Una consulta de ordenamiento para otro campo, pasada mediante parámetros de URL, se ignora.
* **`fields_default_sort`**: Establece el estado inicial de la tabla. Pase una cadena simple para ordenar de forma ascendente, una tupla con `True` para ordenar de forma descendente, o una tupla con `False` para ordenar de forma ascendente de manera explícita. Encadene varios elementos para un ordenamiento multicolumna.

#### Paginación y controles de interfaz {#pagination-and-ui-controls}

Ajuste el diseño de la página de lista con estos atributos:

```python
class PostView(ModelView):
    page_size = 25
    page_size_options = [25, 50, 100, -1]  # -1 se renderiza como "All"
    show_goto_page = True
    search_auto_submit = True
    show_detail_search = True
    row_click_navigate = False
```

* **`page_size` y `page_size_options`**: El límite de paginación predeterminado y las opciones del menú desplegable.
* **`show_goto_page`**: Añade un campo de entrada «ir a la página» para conjuntos de datos grandes.
* **`search_auto_submit`**: Filtra mientras el usuario escribe.
* **`show_detail_search`**: Añade un cuadro de búsqueda en la página de detalle para filtrar tablas de relaciones en línea.
* **`row_click_navigate`**: Abre la página de detalle cuando el usuario selecciona cualquier parte de una fila de la tabla. Está activado por defecto. Configúrelo en `False` para mantener las filas inactivas, de modo que los usuarios naveguen a través de las acciones de fila. Las filas nunca son clicables para los usuarios cuya comprobación de `can_view_detail` falla.

#### Edición en línea

Puede permitir que los usuarios modifiquen campos específicos directamente desde la vista de lista, sin abrir el formulario de edición completo.

Utilice el atributo `inline_editable_fields` para declarar qué columnas admiten esta función. Al seleccionar una celda habilitada, se abre un popover para una actualización rápida.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Habilitar ediciones rápidas para texto corto y conmutadores booleanos
    inline_editable_fields = ["title", "published"]
```

!!! note "Security and access"
    La edición en línea está desactivada por defecto. Cuando la active, el permiso existente `can_edit` de la vista sigue controlando su acceso.

Para detalles de configuración, comportamiento de validación y la matriz completa de tipos de campo compatibles, consulte la guía [Inline Edit](inline-edit.md).

### Datos relacionales

El admin gestiona las relaciones de datos por usted. Para la configuración de muchos-a-uno entre `Post` y `Author`, añada el atributo de relación a su lista `fields`. Siempre que ambos modelos tengan vistas registradas, la interfaz renderizará los widgets adecuados.

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]  # 'books' es una relación Many


class PostView(ModelView):
    fields = ["id", "title", "author"]  # 'author' es una relación One


admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post))
```

#### Declaración manual de relaciones

Declare usted mismo los campos `HasOne` o `HasMany` solo cuando la vista destino esté registrada bajo una `key` personalizada.

```python
from starlette_admin import HasMany, HasOne, StringField


class AuthorView(ModelView):
    fields = ["id", "name", HasMany("books", key="post-article")]


class PostView(ModelView):
    fields = ["id", "title", HasOne("author", key="author")]


# Author usa la key por defecto ("author"), Post usa una key personalizada ("post-article")
admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post, key="post-article"))
```

### Representación de objetos

Cuando el admin necesita mostrar un registro como un valor único, recurre a la clave primaria. Un `Post` vinculado a `Author #3` se renderiza entonces como "3" en las columnas de relaciones, lo que prácticamente no le dice nada al usuario. Dos métodos opcionales, definidos en el **modelo** y no en la vista, reemplazan ese valor predeterminado por algo significativo. Ambos aceptan el `Request` actual y pueden ser síncronos o asíncronos.

#### `__admin_repr__`

Devuelve una cadena simple; se usa dondequiera que el registro aparezca como texto: columnas de relaciones en las páginas de lista y detalle, migas de pan y mensajes de confirmación de acciones.

```python
class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __admin_repr__(self, request: Request) -> str:
        return self.name
```

Con este método implementado, el autor de una publicación se renderiza como "Gabriel Garcia Marquez" en lugar de "3".

#### `__admin_select2_repr__`

Devuelve un fragmento HTML que renderiza las opciones en los desplegables `select2` utilizados por los campos de formulario de relación, lo que le permite enriquecer las opciones con imágenes, insignias o texto secundario. Sin este método, el admin recurre a la salida escapada de `__admin_repr__`. Sin ninguno de los dos métodos, recurre a un resumen generado de los campos no relacionales del registro.

```python
from jinja2 import Template


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str] = mapped_column(String(255))

    def __admin_select2_repr__(self, request: Request) -> str:
        template = Template(
            '<div class="d-flex align-items-center">'
            '<span class="avatar me-2" style="background-image: url({{ obj.avatar_url }})"></span>'
            "<span>{{ obj.name }}</span>"
            "</div>",
            autoescape=True,
        )
        return template.render(obj=self)
```

!!! note
    El valor devuelto debe ser HTML válido.

!!! warning
    Escape los valores provenientes de la base de datos para prevenir ataques de cross-site scripting (XSS). Renderice el fragmento con Jinja2 y `autoescape=True`, como se muestra arriba, o escape cada valor usted mismo con `html.escape`. Para más información, consulte la [documentación de OWASP](https://owasp.org/www-community/attacks/xss/).

### Seguridad y autorización {#security-and-authorization}

Restrinja el acceso sobrescribiendo los métodos de permisos en su `ModelView`. Cada uno devuelve un booleano, y las implementaciones base devuelven todas `True`.

Este patrón se conecta directamente a su `AuthProvider`. En el ejemplo siguiente, cada comprobación lee una lista `roles` del `admin_user` de la sesión:

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        # Si esto devuelve False, la vista queda completamente oculta en la interfaz
        return any(":post" in role for role in request.state.admin_user.roles)

    def can_create(self, request: Request) -> bool:
        return "create:post" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit:post" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete:post" in request.state.admin_user.roles

    def can_view_detail(self, request: Request) -> bool:
        return "read:post" in request.state.admin_user.roles
```

Para más información sobre cómo configurar su `AuthProvider` y poblar el objeto `admin_user`, consulte [Authentication](auth.md).

!!! note
    Sobrescriba solo los métodos que desea restringir. Los que no toque seguirán permitiendo el acceso.

### Hooks de ciclo de vida {#lifecycle-hooks}

Utilice los hooks de ciclo de vida para ejecutar efectos secundarios o mutar datos justo antes o después de una transacción de base de datos.

```python
from typing import Any
from starlette.requests import Request


class PostView(ModelView):
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        # Mutar el objeto antes de que llegue a la base de datos
        obj.title = obj.title.strip()

    async def after_create(self, request: Request, obj: Any) -> None:
        # Activar efectos secundarios posteriores a la creación
        print(f"Created post #{obj.id}")
```

Los hooks disponibles son `before_create`, `after_create`, `after_create_committed`, `before_edit`, `after_edit`, `after_edit_committed`, `before_delete`, `after_delete` y `after_delete_committed`.

#### Hooks committed

`after_create_committed`, `after_edit_committed` y `after_delete_committed` se ejecutan solo después de que la transacción de base de datos haga commit. Úselos para efectos secundarios que no deben ocurrir si una escritura se revierte, como enviar correos electrónicos o encolar trabajos en segundo plano:

```python
class PostView(ModelView):
    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await send_new_post_notification(obj.id)
```

!!! warning
    Para cuando estos hooks se ejecutan, la sesión de la solicitud ya hizo commit y está cerrada. No escriba en la base de datos a través de `request.state.session` dentro de ellos. Utilice E/S externas, o abra una nueva sesión de base de datos.

!!! important
    En `after_delete_committed`, `obj` está desconectado de cualquier sesión. Los atributos cargados antes de la eliminación siguen siendo legibles, pero leer uno que nunca fue cargado falla, porque la fila ya no existe.

!!! note "Backend support"
    Solo los backends que difieren el commit hasta el final de la solicitud emiten estos hooks. Hoy en día ese es el backend de SQLAlchemy.

!!! tip
    Para lógica que abarca varias vistas, como un registro de auditoría, use [Events](../advanced/events.md) en su lugar.

### Personalización de la interfaz

#### Organización de la barra lateral {#sidebar-organization}

Agrupe vistas relacionadas en una carpeta colapsable con `DropDown`. Una carpeta puede mezclar entradas de tipo `ModelView`, `CustomView` y `Link`.

```python
from starlette_admin import DropDown, Link

admin.add_view(
    DropDown(
        "Content Management",
        icon="fa fa-folder",
        views=[
            PostView(Post, icon="fa fa-newspaper"),
            AuthorView(Author, icon="fa fa-user"),
            Link(
                menu_label="View Live Site",
                icon="fa fa-external-link",
                url="/",
                target="_blank",
            ),
        ],
    )
)
```

#### Exportadores e importadores

Los atributos `exporters` e `importers` definen qué formatos están disponibles para la transferencia de datos. Consulte la guía [Export & Import](export-import.md) para conocer las opciones integradas y cómo escribir las suyas propias.

```python
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["json"]
```

### Acciones, formularios en línea y plantillas

`ModelView` cuenta con tres conjuntos adicionales de funcionalidades para casos complejos, cada uno con su propia guía:

* **Acciones y acciones de fila:** Los atributos `actions` y `row_actions` añaden operaciones personalizadas por lotes y por fila más allá del CRUD. Consulte [Actions](actions.md).
* **Formularios en línea:** El atributo `inlines` anida los formularios de creación y edición de un modelo relacionado dentro de la vista padre. Consulte [Inline Forms](inline-forms.md).
* **Plantillas y assets:** Reemplace las páginas predeterminadas por sus propias plantillas Jinja mediante `list_template`, `detail_template`, `create_template` o `edit_template`. Consulte [Templates](../advanced/templates.md).

## CustomView

No toda página del admin corresponde a un modelo de base de datos. `CustomView` crea una página independiente en la barra lateral construida a partir de widgets, plantillas personalizadas o rutas personalizadas.

```python
from starlette_admin import CustomView, StatWidget

admin.add_view(
    CustomView(
        menu_label="System Status",
        icon="fa fa-heart-pulse",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)
```

Consulte [Custom Views](custom-views.md) para ver el catálogo completo de widgets, instrucciones de dashboards y rutas personalizadas.

## Link

`Link` añade un hipervínculo a la barra lateral, que dirige a los usuarios hacia un sitio en producción, documentación externa u otra herramienta interna.

```python
from starlette_admin import Link

admin.add_link(
    Link(
        menu_label="View Live Site",
        icon="fa fa-external-link",
        url="/",
        target="_blank",
    )
)
```

* **`label`** e **`icon`**: El texto y el ícono de la entrada en la barra lateral.
* **`url`** y **`target`**: El destino y el atributo target del ancla.

`admin.add_link(link)` es un envoltorio ligero alrededor de `admin.add_view(link)`. Use el que resulte más legible en su código. También puede anidar un `Link` dentro de un `DropDown`, como se muestra en [Organización de la barra lateral](#sidebar-organization).

---

## Próximos pasos

* **[Fields](fields.md)**: El catálogo completo de tipos de campo.
* **[Form Layouts](../advanced/form-layout.md)**: Organice los formularios de creación y edición con filas, paneles, fieldsets y pestañas.
* **[Custom Views](custom-views.md)**: Construya dashboards y páginas independientes con widgets, plantillas y rutas personalizadas.
* **[Actions & Row Actions](actions.md)**: Añada operaciones por lotes y por fila más allá del CRUD.
* **[Inline Edit](inline-edit.md)**: Permita que los usuarios editen un único campo de una fila desde la página de lista.
* **[Inline Forms](inline-forms.md)**: Anide los formularios de creación y edición de un modelo relacionado dentro de una vista padre.
* **[Templates](../advanced/templates.md)**: Sustituya por sus propias plantillas Jinja e inyecte assets personalizados.
