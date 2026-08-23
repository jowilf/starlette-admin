---
title: Seguridad
description: Descubra las funciones de seguridad integradas en starlette-admin, incluida
  la protección CSRF, la seguridad de la carga de archivos y el control de acceso.
source_hash: d16d4b0beefd5dc8580f8d65abaa28fda407896efff2ea2c3988ec3bf93277a4
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/security/)
<!-- translation-notice:end -->

# Seguridad

`starlette-admin` incluye salvaguardas para los riesgos que conlleva ejecutar un panel de administración. La protección contra la falsificación de solicitudes entre sitios (CSRF) y los límites en el tamaño de las cargas de exportación e importación están activos desde que se instancia la clase `Admin`.

Estos valores predeterminados refuerzan la interfaz frente a ataques comunes, pero no reemplazan la seguridad estándar de despliegue. Usted sigue siendo responsable de la seguridad de la capa de transporte (HTTPS/TLS), el control de acceso a la red, la autenticación de usuarios (consulte [Autenticación](auth.md)), las actualizaciones de dependencias y las revisiones de seguridad. Esta página cubre las protecciones automáticas, las que usted configura y el ajuste `secret_key` que necesita en producción.

## Lo que obtiene automáticamente

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()
admin = Admin(engine, title="My Admin")
admin.mount_to(app)
```

Incluso sin parámetros de seguridad, la instancia de administración defiende contra varias vulnerabilidades comunes:

* **Protección CSRF:** activa en cada formulario y llamada AJAX de jQuery, incluidas las acciones de fila y los diálogos de confirmación.
* **Mensajes flash:** transportados en una cookie firmada, por lo que no necesita `SessionMiddleware`.
* **Saneamiento de nombres de archivo:** aplicado a cada carga de archivos que pasa por un backend de almacenamiento.
* **Verificación del contenido de imágenes:** valida las cargas de `ImageField` a nivel de bytes con Pillow, cuando está instalado.
* **Límites de exportación:** limitados a 100 000 filas por solicitud, para evitar el agotamiento de recursos y la denegación de servicio.
* **Límites de importación:** limitados a 10 MB por solicitud, para reducir el agotamiento de memoria.

Hay una protección más disponible, pero desactivada de forma predeterminada: el escape que evita la inyección de fórmulas en hojas de cálculo en las exportaciones CSV y de hojas de cálculo (XLSX, XLS, ODS). Consulte [Inyección de fórmulas](#inyeccion-de-formulas).

Las secciones siguientes explican estas protecciones y cómo ajustar los umbrales que usted controla.

## La clave secreta

```python
admin = Admin(engine, title="My Admin", secret_key="a-long-random-string")
```

La `secret_key` es la raíz criptográfica para firmar dos cookies: el token CSRF y la cookie de mensajes flash. Ambas usan [itsdangerous](https://itsdangerous.palletsprojects.com/), de modo que los clientes pueden leer las cookies, pero no pueden falsificar ni alterar la carga sin la clave.

!!! warning "Establezca siempre una clave secreta explícita en producción"
    Si omite `secret_key`, la instancia de `Admin` genera una clave aleatoria al arrancar y emite una advertencia `UserWarning`. Esto es aceptable para una demostración local, pero falla en despliegues con varios workers. Cuando ejecuta varios workers, como `uvicorn --workers 4`, Gunicorn o varios contenedores, cada proceso genera su propia clave. Un token CSRF firmado por el worker que sirvió el formulario fallará la validación cuando un worker diferente procese el envío, lo que produce errores de token CSRF no válido en una fracción aparentemente aleatoria de las solicitudes. Establezca `secret_key` explícitamente antes de escalar más allá de un solo proceso.

## Protección CSRF

`CSRFMiddleware` usa un patrón de cookie de doble envío firmado para prevenir la falsificación de solicitudes entre sitios. Emite una cookie `starlette_admin_csrftoken` en los métodos HTTP seguros (`GET`, `HEAD`, `OPTIONS` y `TRACE`). Para las solicitudes de modificación, valida esa cookie contra un encabezado `X-CSRFToken` o un campo oculto de formulario `csrftoken`.

Cada plantilla integrada de administración (`create`, `edit` y `login`) renderiza el campo oculto por usted:

```jinja
{{ csrf_input(request) }}

```

El JavaScript incluido también adjunta el encabezado a cada llamada AJAX de jQuery, de modo que las acciones de fila y otras interacciones asíncronas quedan protegidas sin código adicional. Llame a `csrf_input(request)` usted mismo solo cuando construya formularios personalizados fuera de las plantillas predeterminadas. Consulte [Vistas personalizadas](custom-views.md).

## Cargas de archivos

Cada carga que pasa por un backend de [almacenamiento de archivos](file-storage.md) se sanea con `secure_filename`. Los componentes de ruta de recorrido de directorios se eliminan y los caracteres fuera de `[A-Za-z0-9_.-]` se convierten en guiones bajos (`_`). No puede desactivar esto.

Establezca restricciones de tipo de contenido y tamaño por campo con `accept` y `max_size`:

```python
from starlette_admin.fields import FileField


class DocumentView:
    invoice = FileField(accept=".pdf,.docx", max_size=5 * 1024 * 1024)  # límite de 5 MB
```

Sin ellas, un `FileField` acepta cualquier tipo y tamaño de archivo. `ImageField` es la excepción: usa de forma predeterminada `accept="image/*"`, y cuando Pillow está instalado antepone un validador que abre la carga con `PIL.Image` para confirmar que los bytes se decodifican como una imagen, en lugar de confiar en los metadatos proporcionados por el navegador.

!!! important "Aplique límites de tamaño de solicitud a nivel del servidor web"
    No dependa únicamente de `max_size`. Esa verificación a nivel de aplicación se ejecuta solo después de que el servidor haya recibido toda la carga de la solicitud. Para prevenir ataques de denegación de servicio (DoS), limite el tamaño del cuerpo de la solicitud en la configuración de su servidor web, como `client_max_body_size` en NGINX o el ajuste equivalente en su balanceador de carga.

!!! warning "Las extensiones de archivo y los encabezados Content-Type pueden ser suplantados"
    El atributo `accept` depende de la extensión del nombre de archivo y del encabezado `Content-Type` proporcionado por el navegador, y un atacante puede suplantar ambos. Un archivo que parece `invoice.pdf` puede contener una carga ejecutable.

    Para archivos que no son imágenes, combine `accept` con un validador personalizado que inspeccione los bytes mágicos del archivo. Bibliotecas como [`filetype`](https://github.com/h2non/filetype.py) y [`python-magic`](https://github.com/ahupp/python-magic) verifican el formato real del archivo:

    ```python
    import filetype
    from starlette.datastructures import UploadFile
    from starlette.requests import Request
    from starlette_admin.fields import BaseField

    ALLOWED_DOCUMENT_MIME_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def validate_document_type(
        request: Request, field: BaseField, upload: UploadFile, form_values: dict
    ) -> None:
        upload.file.seek(0)
        try:
            header = upload.file.read(2048)
            kind = filetype.guess(header)
            detected = kind.mime if kind else "application/octet-stream"
        finally:
            upload.file.seek(0)

        if detected not in ALLOWED_DOCUMENT_MIME_TYPES:
            raise ValueError(
                f"Invalid file type '{detected}'. Only PDF, DOC, and DOCX are allowed."
            )
    ```

    Aplique el validador con `FileField(..., validators=[validate_document_type])`. Para una implementación completa, consulte [`examples/04-filestorage`](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage).

## Límites de exportación

```python
from starlette_admin.export import ExportConfig

admin = Admin(engine, title="My Admin", export_config=ExportConfig(max_rows=50_000))
```

| Atributo | Predeterminado | Descripción |
| --- | --- | --- |
| `max_rows` | `100_000` | Número máximo de filas por solicitud de exportación. Si se supera el límite, se muestra un mensaje flash de error y se devuelve al usuario a la vista de lista. Establezca en `None` para eliminar el límite. |
| `restrict_url_download` | `True` | Se aplica a referencias de archivos solo URL. Restringe el ZIP de exportación a archivos cuyo origen coincida con el `base_url` de la administración. |
| `max_download_size` | `20 MB` | Tamaño máximo para una descarga solo URL empaquetada en un ZIP de exportación. Los archivos más grandes se omiten y se registran con una advertencia. |
| `safe_download_url` | `None` | Una función de devolución de llamada personalizada con la firma `(url, request) -> str`. |

Para saber cómo se construye el paquete ZIP, consulte [Exportación e importación](export-import.md).

### Inyección de fórmulas

El software de hojas de cálculo trata un valor de celda que comienza con `=`, `+`, `-` o `@` como una fórmula. Si un usuario no confiable guarda una carga como `=HYPERLINK(...)` en un campo exportado, la aplicación de hoja de cálculo la ejecuta cuando un administrador abre el archivo. Esto se conoce como inyección CSV o inyección de fórmulas.

Dado que los valores exportados se escriben exactamente como están almacenados en la base de datos, el escape de fórmulas está **desactivado de forma predeterminada**. El exportador CSV y los exportadores de hojas de cálculo de Tablib (`xlsx`, `xls` y `ods`) aceptan todos un parámetro `escape_formulas`. Cuando lo activa, cualquier cadena que comience con un carácter desencadenante recibe una comilla simple inicial (`'`), lo que obliga a la aplicación a mostrar el valor como texto sin formato.

!!! warning "Active el escape de fórmulas para datos proporcionados por usuarios"
    Si alguna cuenta que no sea de administrador puede escribir datos en un campo exportado, establezca `escape_formulas=True`. Sin ello, los valores controlados por atacantes pueden ejecutar comandos del sistema o extraer datos cuando alguien abra el archivo localmente.

Para activar el escape, reemplace la cadena de formato por una instancia explícita de exportador:

```python
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.export import CsvExporter, TablibExporter


class ProductView(ModelView):
    exporters = [
        CsvExporter(escape_formulas=True),
        TablibExporter("xlsx", escape_formulas=True),
        "json",
    ]
```

## Límites de importación

```python
from starlette_admin.importers import ImportConfig

admin = Admin(
    engine,
    title="My Admin",
    import_config=ImportConfig(
        max_upload_size=5 * 1024 * 1024,
        max_rows=50_000,
    ),
)
```

| Atributo | Predeterminado | Descripción |
| --- | --- | --- |
| `max_upload_size` | `10 MB` | Se verifica tan pronto como llega la solicitud, antes de cualquier análisis. |
| `max_rows` | `100_000` | Número máximo de filas por solicitud de importación. La administración cuenta la carga en una pasada previa y rechaza un archivo mayor con una respuesta HTTP 400 antes de crear cualquier registro en la base de datos. Establezca en `None` para eliminar el límite. |

La importación rechaza los archivos ZIP de forma rotunda, lo que elimina el riesgo de ataques de bomba ZIP en este endpoint. `FileField` e `ImageField` también quedan excluidos de las importaciones masivas, porque usan `exclude_from_import=True` de forma predeterminada, de modo que los usuarios adjuntan archivos de uno en uno mediante los formularios de creación o edición.

## Lo que esta página no cubre

Las protecciones integradas abordan riesgos dentro del código base de la administración. No aseguran su arquitectura en su conjunto. Estas medidas operativas están fuera del alcance de `starlette-admin` y siguen siendo responsabilidad suya:

* **Seguridad del transporte:** sirva la administración sobre HTTPS. Las cookies CSRF y de mensajes flash están firmadas, pero no cifradas, por lo que cualquiera que intercepte tráfico HTTP sin cifrar puede leerlas.
* **Autenticación y autorización:** la instancia de `Admin` es pública hasta que adjunte un `AuthProvider`. Sin uno, todos los endpoints y rutas están abiertos. Consulte [Autenticación](auth.md).
* **Exposición en red:** si el panel de administración no necesita acceso público, colóquelo detrás de un firewall, una VPN o una lista blanca de direcciones IP.
* **Higiene de dependencias:** esté atento a los avisos de seguridad y mantenga `starlette-admin`, Starlette, su driver ORM y el resto de sus dependencias actualizados.
* **Acciones posteriores a la autenticación:** la protección CSRF y la validación de cargas no limitan lo que un usuario autenticado puede hacer. El control de acceso granular proviene enteramente de las verificaciones de permisos que usted escriba en `is_accessible`, `can_create`, `can_edit` y `can_delete`. Consulte [Autenticación](auth.md).

Considere esta página como una guía para configurar el paquete de administración, no como una lista de verificación para asegurar todo su despliegue de producción.

---

## Qué sigue

* **[Exportación e importación](export-import.md):** el diálogo de exportación, el ciclo de vida de la vista previa de importación y la estructura del paquete ZIP.
* **[Almacenamiento de archivos](file-storage.md):** patrones para configurar backends de almacenamiento para `FileField` e `ImageField`.
* **[Autenticación](auth.md):** cómo `secret_key` regula las sesiones de inicio de sesión y las verificaciones CSRF una vez que añade un proveedor de autenticación.
