---
title: Vistas
description: Aprenda a configurar las vistas de lista y de detalle en starlette-admin,
  incluidas la búsqueda, la ordenación y la paginación.
source_hash: 33fc39d0f563908c141e8f5f8dc89dfdff925d4b959ed1d032ee685346daae57
prompt_hash: 4d252dd7142cde87a0a6edf7cc724709cd7913d618d80eb0687c4c9beddf15fb
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? warning "Traducción automática supervisada"

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

Una subclase de `ModelView` es la forma de exponer un modelo de base de datos en el panel de administración. Los atributos de clase y las sobrescrituras de métodos en esa vista definen cómo se ve el recurso, cómo se comporta y cómo maneja los datos.

Todos los ejemplos de esta sección usan la siguiente configuración de SQLAlchemy:

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

Una clase de vista no hace nada hasta que la registre en una instancia de `Admin`:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///blog.db")
admin = Admin(engine, title="Blog Admin", secret_key="change-me")

# Register the view
admin.add_view(PostView(Post))
```

Vea [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) para un panel de administración ejecutable construido de la misma manera, sobre un modelo `Post`.

Al registrar una vista se generan interfaces paginadas, ordenables y con búsqueda para listar, ver, crear, editar y eliminar registros. Usted no escribe rutas ni plantillas.

!!! note
    Importe `ModelView` desde el paquete contrib de su backend, como `starlette_admin.contrib.sqla`, `.beanie`, `.mongoengine`, `.sqlmodel` o `.tortoise`. **Cada atributo descrito a continuación es idéntico en todos los backends**, por lo que puede reemplazar más adelante un modelo de SQLAlchemy por un documento de MongoEngine sin cambiar la lógica de su vista.

### Configuración principal

#### Nomenclatura y enrutamiento

De forma predeterminada, el panel de administración deriva el enrutamiento de URL y las etiquetas de la interfaz del nombre de la clase del modelo. Para el modelo `Post`, utiliza:

* **Clave (`key`):** `post` (URL: `/admin/post/list`)
* **Etiqueta de menú:** `Posts` (entrada en la barra lateral)
* **Nombre visible:** `Post` (botones de la interfaz como **New Post**)

Cuando los valores derivados no son correctos, puede sobrescribirlos al registrar la vista o en el constructor.

| Atributo | Descripción | Ejemplo de sobrescritura | Interfaz o URL resultante |
| --- | --- | --- | --- |
| **`key`** | El slug interno y la ruta URL base. | `key="blog-post"` | `/admin/blog-post/list` |
| **`menu_label`** | El sustantivo plural usado en la barra lateral. | `menu_label="Blog Posts"` | **Barra lateral:** Blog Posts |
| **`display_name`** | El sustantivo singular usado en acciones y formularios. | `display_name="Article"` | **Botones:** New Article |

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

#### Selección y personalización de campos

La lista `fields` define qué atributos del modelo aparecen en la página de lista, en la página de detalle y en los formularios. Omítala para exponer todos los atributos del modelo.

Combine nombres de cadena con instancias explícitas de `BaseField` para controlar widgets, validación y etiquetas:

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
    El panel de administración detecta la clave primaria automáticamente. Defina `pk_attr` únicamente cuando la detección falle, por ejemplo, en un backend personalizado sin una clave primaria de un solo campo.

#### Visibilidad contextual de campos

A menudo, algunos campos pertenecen a la página de lista o a la página de detalle, pero no a un formulario de creación, como las marcas de tiempo y los estados gestionados por el sistema. Use los atributos `exclude_fields_from_*` para ocultar un campo en superficies específicas:

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Hide from specific surfaces
    exclude_fields_from_create = ["published", "created_at"]
    exclude_fields_from_export = ["content"]
```

Los atributos de exclusión disponibles terminan en `_create`, `_edit`, `_list`, `_detail`, `_export` e `_import`.

!!! important
    Para permitir que los usuarios establezcan la clave primaria al crear un registro, lo cual está desactivado de forma predeterminada, configure `show_pk_in_forms = True`.

#### Diseño del formulario

De forma predeterminada, `fields` renderiza sus formularios de creación y edición como una lista plana y vertical. Para reorganizar la interfaz sin modificar sus definiciones de datos, use el atributo `form_layout`.

**La notación abreviada de tuplas**

Para una cuadrícula básica, no necesita importar clases de widget. Agrupe nombres de campos en una tupla para renderizarlos uno al lado del otro en una misma fila.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

**Widgets de diseño avanzados**

A medida que sus formularios crecen, estructúrelos con widgets de diseño. La notación abreviada de tuplas funciona dentro de ellos:

* **`PanelWidget` o `FieldsetWidget`:** agrupan campos relacionados bajo un encabezado, o permiten que una sección sea plegable.
* **`TabsWidget`:** separa categorías de datos distintas, como los detalles de envío y los metadatos SEO, que no necesitan ser visibles al mismo tiempo.

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

Consulte [Diseños de formulario](../advanced/form-layout.md) para conocer filas de varias columnas con anchos explícitos, pestañas, contenido estático y comportamiento de control de acceso.

### Funciones de la tabla de datos

#### Búsqueda y ordenación

Controle cómo los usuarios encuentran y ordenan los datos con `searchable_fields` y `sortable_fields`.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ["title", "content"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]  # Sort newest first
```

* **`searchable_fields`:** activa el generador de filtros y el cuadro de búsqueda global. La búsqueda global ejecuta una consulta de texto completo contra estos campos.
* **`sortable_fields`:** restringe qué encabezados de columna pueden usar los usuarios para ordenar. Una consulta de ordenación de otro campo, pasada mediante parámetros de URL, se ignora.
* **`fields_default_sort`:** define el estado inicial de la tabla. Pase una cadena simple para ordenar de forma ascendente, una tupla con `True` para ordenar de forma descendente, o una tupla con `False` para ordenar de forma ascendente de manera explícita. Encadene varios elementos para una ordenación de múltiples columnas.

#### Paginación y controles de interfaz

Ajuste con precisión el diseño de la página de lista con estos atributos:

```python
class PostView(ModelView):
    page_size = 25
    page_size_options = [25, 50, 100, -1]  # -1 renders as "All"
    show_goto_page = True
    search_auto_submit = True
    show_detail_search = True
    row_click_navigate = False
```

* **`page_size` y `page_size_options`:** el límite de paginación predeterminado y las opciones del menú desplegable.
* **`show_goto_page`:** añade una entrada de «ir a la página» para conjuntos de datos grandes.
* **`search_auto_submit`:** filtra mientras el usuario escribe.
* **`show_detail_search`:** añade un cuadro de búsqueda en la página de detalle para filtrar tablas de relaciones en línea.
* **`row_click_navigate`:** abre la página de detalle cuando el usuario selecciona en cualquier parte de una fila de la tabla. Está activado de forma predeterminada. Establézcalo en `False` para que las filas no respondan, de modo que los usuarios naveguen mediante las acciones de fila en su lugar. Las filas nunca son clicables para los usuarios cuya comprobación de `can_view_detail` falla.

#### Edición en línea

Puede permitir que los usuarios cambien campos específicos directamente desde la página de lista, sin abrir el formulario de edición completo.

Use el atributo `inline_editable_fields` para declarar qué columnas admiten esta función. Al seleccionar una celda habilitada se abre entonces un elemento emergente para realizar una actualización rápida.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Enable quick edits for short text and boolean toggles
    inline_editable_fields = ["title", "published"]
```

!!! note "Security and access"
    La edición en línea está desactivada de forma predeterminada. Cuando la active, el permiso existente `can_edit` de la vista sigue controlándola.

Para obtener detalles de configuración, el comportamiento de validación y la matriz completa de tipos de campo admitidos, consulte la guía [Inline Edit](inline-edit.md).

### Datos relacionales

El panel de administración maneja las relaciones de datos por usted. Para la configuración de muchos a uno entre `Post` y `Author`, añada el atributo de relación a su lista `fields`. Mientras ambos modelos tengan vistas registradas, la interfaz renderiza los widgets adecuados.

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]  # 'books' is a Many relationship


class PostView(ModelView):
    fields = ["id", "title", "author"]  # 'author' is a One relationship


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


# Author uses default key ("author"), Post uses custom key ("post-article")
admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post, key="post-article"))
```

### Representación de objetos

Cuando el panel de administración necesita mostrar un registro como un único valor, recurre a la clave primaria. Un `Post` vinculado a `Author #3` se renderiza entonces como "3" en las columnas de relación, lo cual prácticamente no le dice nada al usuario. Dos métodos opcionales, definidos en el **modelo** en lugar de en la vista, reemplazan ese valor predeterminado por algo significativo. Ambos aceptan la `Request` actual y pueden ser síncronos o asíncronos.

#### `__admin_repr__`

Devuelve una cadena simple, utilizada dondequiera que el registro aparece como texto: las columnas de relación en las páginas de lista y de detalle, las migas de pan y los mensajes de confirmación de acciones.

```python
class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __admin_repr__(self, request: Request) -> str:
        return self.name
```

Con este método en su lugar, el autor de una publicación se renderiza como "Gabriel Garcia Marquez" en lugar de "3".

#### `__admin_select2_repr__`

Devuelve un fragmento HTML que renderiza las opciones en los menús desplegables `select2` usados por los campos de formulario de relación, de modo que pueda enriquecer las opciones con imágenes, insignias o texto secundario. Sin este método, el panel de administración recurre a la salida escapada de `__admin_repr__`. Sin ninguno de los dos métodos, recurre a un resumen generado de los campos de no relación del registro.

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
    Escape los valores de la base de datos para prevenir ataques de cross-site scripting (XSS). Renderice el fragmento con Jinja2 y `autoescape=True`, como se muestra arriba, o escape cada valor usted mismo con `html.escape`. Para obtener más información, consulte la [documentación de OWASP](https://owasp.org/www-community/attacks/xss/).

### Seguridad y autorización

Restrinja el acceso sobrescribiendo los métodos de permisos en su `ModelView`. Cada uno devuelve un valor booleano y las implementaciones base devuelven todas `True`.

Este patrón se conecta directamente con su `AuthProvider`. En el siguiente ejemplo, cada comprobación lee una lista `roles` del `admin_user` de la sesión:

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        # If this returns False, the view is entirely hidden from the UI
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

Para obtener más información sobre cómo configurar su `AuthProvider` y poblar el objeto `admin_user`, consulte [Autenticación](auth.md).

!!! note
    Sobrescriba únicamente los métodos que desee restringir. Los que no toque seguirán permitiendo el acceso.

### Hooks del ciclo de vida

Use los hooks del ciclo de vida para ejecutar efectos secundarios o mutar datos justo antes o después de una transacción de base de datos.

```python
from typing import Any
from starlette.requests import Request


class PostView(ModelView):
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        # Mutate the object before it hits the database
        obj.title = obj.title.strip()

    async def after_create(self, request: Request, obj: Any) -> None:
        # Trigger post-creation side effects
        print(f"Created post #{obj.id}")
```

Los hooks disponibles son `before_create`, `after_create`, `after_create_committed`, `before_edit`, `after_edit`, `after_edit_committed`, `before_delete`, `after_delete` y `after_delete_committed`.

#### Hooks confirmados

`after_create_committed`, `after_edit_committed` y `after_delete_committed` se ejecutan solo después de que la transacción de la base de datos se confirma. Úselos para efectos secundarios que no deben ocurrir cuando una escritura se revierte, como enviar correos electrónicos o poner trabajos en cola:

```python
class PostView(ModelView):
    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await send_new_post_notification(obj.id)
```

!!! warning
    Para cuando estos hooks se ejecutan, la sesión de la solicitud ya se ha confirmado y cerrado. No escriba en la base de datos mediante `request.state.session` dentro de ellos. Utilice E/S externas o abra una nueva sesión de base de datos.

!!! important
    En `after_delete_committed`, `obj` está desconectado de cualquier sesión. Los atributos cargados antes de la eliminación siguen siendo legibles, pero leer uno que nunca fue cargado falla, porque la fila ya no existe.

!!! note "Backend support"
    Solo los backends que aplazan la confirmación hasta el final de la solicitud emiten estos hooks. Hoy en día, ese es el backend de SQLAlchemy.

!!! tip
    Para lógica que abarca varias vistas, como un registro de auditoría, use en su lugar [Events](../advanced/events.md).

### Personalización de la interfaz

#### Organización de la barra lateral

Agrupe vistas relacionadas en una carpeta plegable con `DropDown`. Una carpeta puede mezclar entradas de tipo `ModelView`, `CustomView` y `Link`.

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

`ModelView` tiene tres conjuntos de funciones adicionales para casos complejos, cada uno con su propia guía:

* **Acciones y acciones de fila:** los atributos `actions` y `row_actions` añaden operaciones personalizadas por lotes y por fila más allá del CRUD. Consulte [Acciones](actions.md).
* **Formularios en línea:** el atributo `inlines` anida los formularios de creación y edición de un modelo relacionado dentro de la vista principal. Consulte [Formularios en línea](inline-forms.md).
* **Plantillas y recursos:** reemplace las páginas predeterminadas con sus propias plantillas Jinja mediante `list_template`, `detail_template`, `create_template` o `edit_template`. Consulte [Plantillas](../advanced/templates.md).

## CustomView

No todas las páginas del panel de administración corresponden a un modelo de base de datos. `CustomView` crea una página independiente en la barra lateral construida con widgets, plantillas personalizadas o rutas personalizadas.

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

Consulte [Vistas personalizadas](custom-views.md) para conocer el catálogo completo de widgets, las instrucciones del panel de control y las rutas personalizadas.

## Link

`Link` añade un hipervínculo a la barra lateral que dirige a los usuarios a un sitio en vivo, documentación externa u otra herramienta interna.

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

* **`label`** e **`icon`**: el texto y el icono de la entrada de la barra lateral.
* **`url`** y **`target`**: el destino y el atributo `target` del ancla.

`admin.add_link(link)` es un envoltorio ligero alrededor de `admin.add_view(link)`. Use el que se lea mejor en su base de código. También puede anidar un `Link` dentro de un `DropDown`, como se muestra en [Organización de la barra lateral](#organizacion-de-la-barra-lateral).

---

## Próximos pasos

* **[Fields](fields.md)**: el catálogo completo de tipos de campo.
* **[Diseños de formulario](../advanced/form-layout.md)**: organice los formularios de creación y edición con filas, paneles, fieldsets y pestañas.
* **[Vistas personalizadas](custom-views.md)**: cree paneles de control y páginas independientes con widgets, plantillas y rutas personalizadas.
* **[Acciones y acciones de fila](actions.md)**: añada operaciones por lotes y por fila más allá del CRUD.
* **[Inline Edit](inline-edit.md)**: permita que los usuarios editen un único campo de una fila desde la página de lista.
* **[Formularios en línea](inline-forms.md)**: anide los formularios de creación y edición de un modelo relacionado dentro de una vista principal.
* **[Plantillas](../advanced/templates.md)**: sustituya las plantillas por las suyas propias de Jinja e inyecte recursos personalizados.
