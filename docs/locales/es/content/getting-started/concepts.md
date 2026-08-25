---
title: Conceptos fundamentales
description: Comprenda los principios de diseño arquitectónico de starlette-admin,
  incluyendo vistas declarativas, estado basado en URL y modelos independientes del
  backend.
source_hash: 3928a168b4a3ffb7f57c78a8e7eed9fd92a949aa93c59339e49c29cb8ccb8a8c
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/getting-started/concepts/)
<!-- translation-notice:end -->

# Conceptos fundamentales

Una vez que haya completado el Quickstart escribiendo una `PostView` y montando una instancia de administración, conozca los principios de diseño arquitectónico del framework. Estos conceptos fundamentales constituyen la base del resto de la documentación.

## Una clase por recurso

Cada recurso que administra el panel se expone a través de una única clase dedicada. Cuando hereda de `ModelView` y lo apunta hacia un modelo de base de datos, se generan automáticamente vistas paginadas, ordenables y filtrables para todas las operaciones CRUD estándar (listado, detalle, creación, edición y eliminación).

Esto elimina la necesidad de escribir rutas personalizadas o plantillas HTML. Todo lo que determina cómo se ve, valida y comporta un recurso reside dentro de esta única clase de vista.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

## La misma vista, cualquier backend

Las vistas interactúan con sus datos mediante una capa de backend adaptable. Tanto si su aplicación utiliza SQLAlchemy, SQLModel, Beanie, MongoEngine o Tortoise ORM, la API de configuración permanece exactamente igual.

Los campos, filtros, permisos y hooks de ciclo de vida funcionan de manera consistente independientemente de dónde residan sus datos. El conocimiento que adquiera en un backend se transfiere directamente a los demás. Cambiar su fuente de datos subyacente solo requiere actualizar sus sentencias de importación.

```python
# For SQLAlchemy backends
from starlette_admin.contrib.sqla import ModelView

# For Beanie backends: identical API surface, different import path
from starlette_admin.contrib.beanie import ModelView
```

## Estado de listado basado en URL

El ordenamiento, el filtrado, la paginación y los criterios de búsqueda se sincronizan directamente con la cadena de consulta (query string) de la URL. Dado que el servidor renderiza los estados del listado completamente a partir de estos parámetros de URL, cada estado de vista es inherentemente guardable como marcador y compartible.

Si envía un enlace administrativo específico a un colega, este verá exactamente las mismas filas filtradas y la misma configuración de ordenamiento que usted.

```text
/admin/post/list?page=2&order_by=published_at%20desc&q=release

```

## Los campos saben renderizarse a sí mismos

Los campos son componentes autorrenderizables. Cada tipo de campo gestiona su propia lógica de visualización en tres contextos distintos: una celda dentro de una tabla de listado, una fila dentro de una vista de detalle y un elemento de entrada dentro de un formulario.

Al construir una vista, declara instancias de campos o pasa nombres de atributos que el backend mapea automáticamente a campos. Elija el tipo que coincida con su modelo de datos, y el framework se encarga del renderizado:

* `StringField` para cadenas de texto
* `IntegerField` para datos numéricos
* `ImageField` para subida de archivos

```python
from starlette_admin import StringField, IntegerField


class ProductView(ModelView):
    fields = [
        StringField("name"),
        IntegerField("price", help_text="In cents"),
    ]
```

## Diseños de formulario declarativos

De forma predeterminada, el atributo `fields` renderiza sus formularios de creación y edición como una lista plana y vertical. Para reorganizar la interfaz de usuario sin alterar sus definiciones de datos subyacentes, utilice el atributo `form_layout`.

### La abreviatura de tupla

Para diseños de cuadrícula básicos, agrupe los nombres de campos en una tupla para renderizarlos lado a lado en una sola fila. Esto evita la necesidad de importar clases de widget complejas.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

### Widgets de diseño avanzados

A medida que sus formularios aumentan en complejidad, puede estructurarlos mediante widgets de diseño. La abreviatura de tupla funciona de forma nativa dentro de estos componentes:

* **`PanelWidget` o `FieldsetWidget`:** Utilice estos componentes para agrupar campos relacionados bajo un encabezado claro o para hacer secciones plegables.
* **`TabsWidget`:** Utilice este componente cuando un recurso tenga categorías de datos distintas (como datos de envío frente a metadatos SEO) que no necesiten verse simultáneamente.

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

## Los filtros están vinculados a los tipos de campo

Las capacidades de filtrado se corresponden directamente con los tipos de datos, lo que garantiza que los usuarios solo vean opciones de consulta relevantes. Un `StringField` ofrece opciones contextuales de texto como *contiene*, *comienza con*, *igual a* y *es nulo*. Un campo entero ofrece restricciones numéricas como *mayor que* o *entre*.

Puede restringir o sobrescribir estos valores predeterminados en un campo individual mediante el parámetro `filters`, o bien registrar filtros personalizados para tipos de datos únicos.

```python
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla.filters import GreaterThanFilter, BetweenFilter


class OrderView(ModelView):
    fields = [
        IntegerField("total", filters=[GreaterThanFilter, BetweenFilter]),
    ]
```

## Traiga su propia autenticación

El framework permanece completamente agnóstico respecto a su esquema de usuarios al omitir un modelo de usuario integrado. La autenticación requiere implementar un único método: `authenticate(request)`.

Conecte este método a su infraestructura de autenticación existente, ya sea una tabla local de base de datos, un proveedor OAuth o un encabezado de proxy de inicio de sesión único (SSO) ascendente. Devolver un objeto `AdminUser` otorga acceso a la interfaz. Devolver `None` deniega el acceso.

```python
from starlette.requests import Request
from starlette_admin.auth import AdminUser, BaseAuthProvider


class MyAuthProvider(BaseAuthProvider):
    async def authenticate(self, request: Request) -> AdminUser | None:
        if request.session.get("user"):
            return AdminUser(username=request.session["user"])
        return None
```

## Las acciones se ejecutan sobre filas seleccionadas

Las acciones por lotes operan sobre varias filas seleccionadas desde la barra de herramientas superior, y las acciones de fila se ejecutan en línea sobre registros individuales. Decorar un método de vista con `@action` o `@row_action` expone automáticamente el método en la interfaz de usuario sin necesidad de registro manual de rutas.

En lugar de devolver una cadena de mensaje desde el método de acción, active notificaciones al usuario directamente mediante la utilidad integrada `flash()`.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin import action, flash
from starlette_admin.contrib.sqla import ModelView


class ArticleView(ModelView):
    actions = ["make_published"]

    @action(
        name="make_published",
        text="Mark as published",
        confirmation="Publish selected articles?",
    )
    async def make_published_action(self, request: Request, pks: list[Any]) -> None:
        for article in await self.find_by_pks(request, pks):
            article.status = "published"
        flash(request, f"{len(pks)} article(s) published.", "success")
```

## Exportación e importación nativas de datos

Cada página de listado incluye un diálogo de exportación que permite a los usuarios seleccionar el alcance (filas seleccionadas o página actual), los campos, el formato y el nombre de archivo. Los filtros activos y los términos de búsqueda se conservan, lo que significa que el archivo exportado coincide exactamente con lo que aparece en pantalla.

El framework admite de forma nativa los formatos CSV, JSON y PDF. Para formatos adicionales como Excel (`xlsx`), el framework se integra con `tablib` para admitir cualquier tipo de archivo compatible. Los formatos se declaran como simples cadenas de extensión. El control de acceso se gestiona a nivel granular mediante el hook `can_export`.

El asistente de importación ingiere de forma segura datos masivos en estos mismos formatos. El asistente valida primero la carga en un paso de vista previa, resaltando los errores fila por fila antes de realizar cualquier escritura en la base de datos, y admite upserts opcionales de claves primarias. Puede restringir el acceso a esta función mediante el hook `can_import`.

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class OrderView(ModelView):
    exporters = ["csv", "xlsx"]

    def can_export(self, request: Request) -> bool:
        return request.state.user.is_staff

    def can_import(self, request: Request) -> bool:
        return request.state.user.is_admin
```

## Almacenamiento de archivos flexible

La gestión de medios mediante `FileField` e `ImageField` se basa en una capa de abstracción `Storage` subyacente. Utilice `LocalStorage` para escrituras en disco local, o instale la integración opcional de S3 ejecutando `pip install starlette-admin[s3]`.

Después de apuntar el campo a su configuración de almacenamiento elegida, este coordina automáticamente la subida de archivos, la validación en el backend y el renderizado en el frontend.

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/", name="local")


class AuthorView(ModelView):
    fields = [
        "name",
        ImageField("avatar", storage=local, upload_folder="avatars"),
    ]
```

## Vistas personalizadas y widgets de panel

Las páginas que no están explícitamente vinculadas a un modelo de base de datos, como paneles de métricas o informes personalizados, se construyen utilizando `CustomView`. El contenido se completa mediante un parámetro `widget`. Este parámetro acepta tanto una instancia estática de `BaseWidget` como un callable dinámico cuya ejecución ocurre cuando el contenido depende de la solicitud entrante.

Puede componer interfaces de usuario complejas organizando primitivas de diseño y widgets de visualización de datos en una jerarquía limpia.

```python
from starlette.requests import Request
from starlette_admin import CustomView, CardRowWidget, Col, Breakpoints, StatWidget


async def count_users(request: Request) -> int:
    from sqlalchemy import func, select
    from myapp.models import User

    result = await request.state.session.execute(select(func.count(User.id)))
    return result.scalar()


dashboard = CustomView(
    menu_label="Dashboard",
    path="/",
    widget=CardRowWidget(
        children=[
            Col(
                StatWidget(title="Users", value_callback=count_users),
                breakpoints=Breakpoints(default=12, md=6),
            ),
        ]
    ),
)
```

## Eventos y hooks de métodos

El framework proporciona dos puntos de extensión diferenciados para ejecutar código durante los ciclos de creación, actualización y eliminación:

1. **Métodos de ciclo de vida:** Para lógica aislada en una entidad específica, sobrescriba métodos locales como `before_create` directamente en su clase de vista.
2. **Escuchadores de eventos:** Para preocupaciones globales como registros de auditoría, invalidación de caché o webhooks, suscríbase al sistema `admin.events`.

Ambos patrones se activan en puntos de ejecución idénticos, lo que le permite elegir el enfoque que mejor se adapte a la arquitectura de su aplicación.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.events import AdminEvent, AfterCreateContext


class PostView(ModelView):
    # Isolated to this view class only
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")


# Global system listener spanning every view class
async def log_create(ctx: AfterCreateContext) -> None:
    print(f"created {ctx.view_key} #{ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, log_create)
```

---

**¿Qué sigue?**

* **[Vistas](../user-guide/views.md):** Todas las opciones de configuración de `ModelView`.
* **[Campos](../user-guide/fields.md):** El catálogo completo de tipos de campo.
* **[Diseños de formulario](../advanced/form-layout.md):** Organice formularios de creación y edición con filas, paneles y pestañas.
* **[Acciones](../user-guide/actions.md):** Acciones por lotes y de fila en profundidad.
