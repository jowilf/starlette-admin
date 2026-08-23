---
title: Conceptos fundamentales
description: Comprenda los principios de diseño arquitectónico de starlette-admin,
  incluidas las vistas declarativas, el estado basado en URL y los modelos independientes
  del backend.
source_hash: 3928a168b4a3ffb7f57c78a8e7eed9fd92a949aa93c59339e49c29cb8ccb8a8c
prompt_hash: 4d252dd7142cde87a0a6edf7cc724709cd7913d618d80eb0687c4c9beddf15fb
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
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

Después de completar la guía de inicio rápido escribiendo una `PostView` y montando una instancia de administración, conozca los principios de diseño arquitectónico del framework. Estos conceptos fundamentales constituyen la base del resto de la documentación.

## Una clase por recurso

Cada recurso que administra el panel se expone mediante una única clase dedicada. Cuando hereda de `ModelView` y lo apunta a un modelo de base de datos, se generan automáticamente vistas paginadas, ordenables y filtrables para todas las operaciones CRUD estándar (lista, detalle, creación, edición y eliminación).

Esto elimina la necesidad de escribir rutas personalizadas o plantillas HTML. Todo lo que determina cómo se ve, valida y comporta un recurso reside en esta única clase de vista.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

## La misma vista, cualquier backend

Las vistas interactúan con sus datos a través de una capa de backend adaptable. Tanto si su aplicación usa SQLAlchemy, SQLModel, Beanie, MongoEngine o Tortoise ORM, la API de configuración permanece exactamente igual.

Los campos, filtros, permisos y hooks de ciclo de vida funcionan de manera consistente sin importar dónde residan sus datos. El conocimiento que adquiera sobre un backend se transfiere directamente a los demás. Cambiar su fuente de datos subyacente solo requiere actualizar sus sentencias de importación.

```python
# Para backends SQLAlchemy
from starlette_admin.contrib.sqla import ModelView

# Para backends Beanie: superficie de API idéntica, ruta de importación distinta
from starlette_admin.contrib.beanie import ModelView
```

## Estado de lista basado en URL

El ordenamiento, el filtrado, la paginación y los criterios de búsqueda se sincronizan directamente con la cadena de consulta de la URL. Dado que el servidor renderiza los estados de lista completamente a partir de estos parámetros de URL, cada estado de vista es inherentemente guardable en marcadores y compartible.

Si envía un enlace administrativo específico a un colega, este verá exactamente las mismas filas filtradas y la misma configuración de ordenamiento que usted.

```text
/admin/post/list?page=2&order_by=published_at%20desc&q=release

```

## Los campos saben renderizarse por sí mismos

Los campos son componentes autorrenderizables. Cada tipo de campo gestiona su propia lógica de visualización en tres contextos distintos: una celda dentro de una tabla de lista, una fila dentro de una página de detalle y un elemento de entrada dentro de un formulario.

Al construir una vista, declara instancias de campos o pasa nombres de atributos que el backend mapea automáticamente a campos. Elija el tipo que coincida con su modelo de datos y el framework se encarga del renderizado:

* `StringField` para cadenas de texto
* `IntegerField` para datos numéricos
* `ImageField` para carga de archivos

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

Para diseños de cuadrícula básicos, agrupe los nombres de campos en una tupla para renderizarlos uno al lado del otro en una sola fila. Esto evita la necesidad de importar clases de widget complejas.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" y "price" comparten una fila; "description" queda debajo
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

### Widgets de diseño avanzados

A medida que sus formularios aumentan en complejidad, puede estructurarlos utilizando widgets de diseño. La abreviatura de tupla funciona de forma nativa dentro de estos componentes:

* **`PanelWidget` o `FieldsetWidget`:** Utilice estos componentes para agrupar campos relacionados bajo un encabezado claro o para hacer que las secciones sean plegables.
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

## Los filtros están asociados a los tipos de campo

Las capacidades de filtrado se corresponden directamente con los tipos de datos, lo que garantiza que los usuarios solo vean opciones de consulta relevantes. Un `StringField` ofrece opciones de texto contextuales como *contiene*, *comienza con*, *es igual a* e *es nulo*. Un campo entero ofrece restricciones numéricas como *mayor que* o *entre*.

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

El framework es completamente agnóstico respecto a su esquema de usuarios al omitir un modelo de usuario integrado. La autenticación requiere implementar un único método: `authenticate(request)`.

Conecte este método a su infraestructura de autenticación existente, como una tabla de base de datos local, un proveedor OAuth o un encabezado de proxy de inicio de sesión único (SSO) ascendente. Devolver un objeto `AdminUser` otorga acceso a la interfaz. Devolver `None` deniega el acceso.

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

Las acciones por lotes operan sobre varias filas seleccionadas desde la barra de herramientas superior, y las acciones de fila se ejecutan en línea sobre registros individuales. Decorar un método de vista con `@action` o `@row_action` expone automáticamente el método en la interfaz de usuario, sin necesidad de registrar rutas manualmente.

En lugar de devolver una cadena de mensaje desde el método de acción, active notificaciones de usuario directamente mediante la utilidad integrada `flash()`.

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

Cada página de lista incluye un diálogo de exportación que permite al usuario seleccionar el alcance (filas seleccionadas o la página actual), los campos, el formato y el nombre del archivo. Los filtros activos y los términos de búsqueda se conservan, lo que significa que el archivo exportado coincide exactamente con lo que aparece en pantalla.

El framework admite de forma nativa los formatos CSV, JSON y PDF. Para formatos adicionales como Excel (`xlsx`), el framework se integra con `tablib` para admitir cualquier tipo de archivo compatible. Los formatos se declaran como simples cadenas de extensión. El control de acceso se gestiona a nivel granular mediante el hook `can_export`.

El asistente de importación ingiere de forma segura datos masivos en estos mismos formatos. El asistente valida primero la carga en un paso de vista previa, resaltando los errores fila por fila antes de confirmar cualquier escritura en la base de datos, y admite upserts opcionales de clave primaria. Puede restringir el acceso a esta función mediante el hook `can_import`.

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

El campo coordina automáticamente la carga de archivos, la validación en el backend y el renderizado en el frontend después de que usted lo apunte a la configuración de almacenamiento elegida.

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

## Vistas personalizadas y widgets del panel de control

Las páginas que no están explícitamente vinculadas a un modelo de base de datos, como paneles de control de métricas o informes personalizados, se construyen utilizando `CustomView`. El contenido se completa mediante un parámetro `widget`. Este parámetro acepta ya sea una instancia estática de `BaseWidget` o un callable dinámico que se ejecuta cuando el contenido depende de la solicitud entrante.

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

El framework proporciona dos puntos de extensión distintos para ejecutar código durante los ciclos de creación, actualización y eliminación:

1. **Métodos de ciclo de vida:** Para lógica aislada de una entidad específica, sobrescriba métodos locales como `before_create` directamente en su clase de vista.
2. **Escuchas de eventos:** Para preocupaciones globales como registros de auditoría, invalidación de caché o webhooks, suscríbase al sistema `admin.events`.

Ambos patrones se activan en puntos de ejecución idénticos, lo que le permite elegir el enfoque que mejor se adapte a la arquitectura de su aplicación.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.events import AdminEvent, AfterCreateContext


class PostView(ModelView):
    # Aislado únicamente en esta clase de vista
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")


# Escucha global del sistema que abarca todas las clases de vista
async def log_create(ctx: AfterCreateContext) -> None:
    print(f"created {ctx.view_key} #{ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, log_create)
```

---

**¿Qué sigue?**

* **[Vistas](../user-guide/views.md):** Todas las opciones de configuración de `ModelView`.
* **[Campos](../user-guide/fields.md):** El catálogo completo de tipos de campo.
* **[Diseños de formulario](../advanced/form-layout.md):** Organice formularios de creación y edición con filas, paneles y pestañas.
* **[Acciones](../user-guide/actions.md):** Acciones por lotes y acciones de fila en profundidad.
