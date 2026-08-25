---
title: Seguridad
description: Descubra las funciones de seguridad integradas en starlette-admin, incluyendo
  la protección CSRF, la seguridad en la subida de archivos y el control de acceso.
source_hash: d16d4b0beefd5dc8580f8d65abaa28fda407896efff2ea2c3988ec3bf93277a4
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/security/)
<!-- translation-notice:end -->

# Seguridad

`starlette-admin` incluye salvaguardas para los riesgos que conlleva ejecutar un panel de administración. La protección contra la falsificación de solicitudes entre sitios (CSRF) y los límites en el tamaño de las cargas de exportación e importación se activan tan pronto como instancia la clase `Admin`.

Estos valores predeterminados endurecen la interfaz frente a ataques comunes, pero no sustituyen la seguridad estándar de despliegue. Usted sigue siendo responsable de la seguridad de la capa de transporte (HTTPS/TLS), del control de acceso a la red, de la autenticación de usuarios (consulte [Autenticación](auth.md)), de las actualizaciones de dependencias y de las revisiones de seguridad. Esta página cubre las protecciones automáticas, las que usted configura y el ajuste `secret_key` que necesita en producción.

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

Incluso sin ningún parámetro de seguridad, la instancia de administración se defiende contra varias vulnerabilidades comunes:

* **Protección CSRF:** Activa en cada formulario y llamada AJAX de jQuery, incluidas las acciones de fila y los diálogos de confirmación.
* **Mensajes flash:** Se transportan en una cookie firmada, por lo que no necesita `SessionMiddleware`.
* **Saneamiento de nombres de archivo:** Se aplica a cada subida de archivo que pasa por un backend de almacenamiento.
* **Verificación del contenido de imágenes:** Valida las subidas de `ImageField` a nivel de bytes con Pillow, cuando está instalado.
* **Límites de exportación:** Limitados a 100 000 filas por solicitud, para evitar el agotamiento de recursos y la denegación de servicio.
* **Límites de importación:** Limitados a 10 MB por solicitud, para restringir el agotamiento de memoria.

Hay una protección más disponible, pero desactivada de forma predeterminada: el escape que previene la inyección de fórmulas en hojas de cálculo en las exportaciones CSV y de hojas de cálculo (XLSX, XLS, ODS). Consulte [Inyección de fórmulas](#formula-injection).

Las secciones siguientes explican estas protecciones y cómo ajustar los umbrales que usted controla.

## La clave secreta

```python
admin = Admin(engine, title="My Admin", secret_key="a-long-random-string")
```

La `secret_key` es la raíz criptográfica para firmar dos cookies: el token CSRF y la cookie de mensajes flash. Ambas utilizan [itsdangerous](https://itsdangerous.palletsprojects.com/), de modo que los clientes pueden leer las cookies pero no pueden falsificar ni alterar la carga útil sin la clave.

!!! warning "Defina siempre una clave secreta explícita en producción"
    Si omite `secret_key`, la instancia `Admin` genera una clave aleatoria al arrancar y emite una `UserWarning`. Esto es aceptable para una demostración local, pero falla en despliegues con varios workers. Cuando ejecute varios workers, como `uvicorn --workers 4`, Gunicorn o varios contenedores, cada proceso genera su propia clave. Un token CSRF firmado por el worker que sirvió el formulario fallará entonces la validación cuando otro worker procese el envío, lo que produce errores de token CSRF no válido en una fracción aparentemente aleatoria de las solicitudes. Defina `secret_key` explícitamente antes de escalar más allá de un único proceso.

## Protección CSRF

`CSRFMiddleware` utiliza un patrón de cookie firmada de doble envío para prevenir la falsificación de solicitudes entre sitios. Emite una cookie `starlette_admin_csrftoken` en los métodos HTTP seguros (`GET`, `HEAD`, `OPTIONS` y `TRACE`). Para las solicitudes de modificación, valida esa cookie contra una cabecera `X-CSRFToken` o un campo oculto de formulario `csrftoken`.

Cada plantilla integrada del panel de administración (`create`, `edit` y `login`) renderiza el campo oculto por usted:

```jinja
{{ csrf_input(request) }}

```

El JavaScript incluido también adjunta la cabecera a cada llamada AJAX de jQuery, de modo que las acciones de fila y otras interacciones asíncronas quedan protegidas sin código adicional. Llame a `csrf_input(request)` por su cuenta solo cuando construya formularios personalizados fuera de las plantillas predeterminadas. Consulte [Vistas personalizadas](custom-views.md).

## Subida de archivos

Cada subida que pasa por un backend de [almacenamiento](file-storage.md) se sanea con `secure_filename`. Los componentes de ruta que intentan atravesar directorios se eliminan, y los caracteres fuera de `[A-Za-z0-9_.-]` se convierten en guiones bajos (`_`). No puede desactivar esto.

Defina restricciones de tipo de contenido y de tamaño por campo con `accept` y `max_size`:

```python
from starlette_admin.fields import FileField


class DocumentView:
    invoice = FileField(accept=".pdf,.docx", max_size=5 * 1024 * 1024)  # 5 MB limit
```

Sin ellas, un `FileField` acepta cualquier tipo y tamaño de archivo. `ImageField` es la excepción: por defecto usa `accept="image/*"`, y cuando Pillow está instalado antepone un validador que abre la subida con `PIL.Image` para confirmar que los bytes se decodifican como una imagen, en lugar de confiar en los metadatos proporcionados por el navegador.

!!! important "Imponga límites de tamaño de solicitud a nivel del servidor web"
    No dependa únicamente de `max_size`. Esa comprobación a nivel de aplicación se ejecuta solo después de que el servidor haya recibido la carga completa de la solicitud. Para prevenir ataques de denegación de servicio (DoS), limite el tamaño del cuerpo de la solicitud en la configuración de su servidor web, como `client_max_body_size` en NGINX o el ajuste equivalente en su balanceador de carga.

!!! warning "Las extensiones de archivo y las cabeceras Content-Type pueden ser falsificadas"
    El atributo `accept` se basa en la extensión del nombre de archivo y en la cabecera `Content-Type` proporcionada por el navegador, y un atacante puede falsificar ambas. Un archivo que parece `invoice.pdf` puede contener una carga ejecutable.

    Para archivos que no sean imágenes, combine `accept` con un validador personalizado que inspeccione los magic bytes del archivo. Bibliotecas como [`filetype`](https://github.com/h2non/filetype.py) y [`python-magic`](https://github.com/ahupp/python-magic) verifican el formato real del archivo:

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
| `max_rows` | `100_000` | Número máximo de filas por solicitud de exportación. Al superar el límite se muestra un mensaje de error y se devuelve al usuario a la vista de lista. Establezca `None` para eliminar el límite. |
| `restrict_url_download` | `True` | Se aplica a referencias de archivo exclusivamente URL. Restringe el ZIP de exportación a archivos cuyo origen coincide con el `base_url` del panel de administración. |
| `max_download_size` | `20 MB` | Tamaño máximo para una descarga exclusivamente URL empaquetada en un ZIP de exportación. Los archivos mayores se omiten y se registran con una advertencia. |
| `safe_download_url` | `None` | Una función callback personalizada con la firma `(url, request) -> str`. |

Para saber cómo se construye el paquete ZIP, consulte [Exportación e importación](export-import.md).

### Inyección de fórmulas {#formula-injection}

El software de hojas de cálculo trata un valor de celda que empieza por `=`, `+`, `-` o `@` como una fórmula. Si un usuario no confiable guarda una carga útil como `=HYPERLINK(...)` en un campo exportado, la aplicación de hoja de cálculo la ejecuta cuando un administrador abre el archivo. Esto se conoce como inyección CSV o inyección de fórmulas.

Como los valores exportados se escriben exactamente como están almacenados en la base de datos, el escape de fórmulas está **desactivado de forma predeterminada**. El exportador CSV y los exportadores de hojas de cálculo de Tablib (`xlsx`, `xls` y `ods`) aceptan todos un parámetro `escape_formulas`. Cuando lo activa, cualquier cadena que empiece por un carácter disparador recibe una comilla simple inicial (`'`), lo que obliga a la aplicación a renderizar el valor como texto plano.

!!! warning "Active el escape de fórmulas para datos suministrados por usuarios"
    Si alguna cuenta que no sea de administrador puede escribir datos en un campo exportado, establezca `escape_formulas=True`. Sin ello, los valores controlados por atacantes pueden ejecutar comandos del sistema o exfiltrar datos cuando alguien abra el archivo localmente.

Para activar el escape, reemplace la cadena de formato por una instancia de exportador explícita:

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
| `max_upload_size` | `10 MB` | Se comprueba tan pronto como llega la solicitud, antes de cualquier análisis sintáctico. |
| `max_rows` | `100_000` | Número máximo de filas por solicitud de importación. El panel de administración cuenta la carga en una pasada previa y rechaza un archivo mayor con una respuesta HTTP 400 antes de crear ningún registro en la base de datos. Establezca `None` para eliminar el límite. |

La importación rechaza directamente los archivos ZIP, lo que elimina el riesgo de ataques de bomba ZIP en este endpoint. `FileField` e `ImageField` también quedan excluidos de las importaciones masivas, porque tienen `exclude_from_import=True` de forma predeterminada, de modo que los usuarios adjuntan archivos uno a uno a través de los formularios de creación o edición.

## Lo que esta página no cubre

Las protecciones integradas abordan riesgos dentro del código base del panel de administración. No aseguran su arquitectura en su conjunto. Estas medidas operativas están fuera del alcance de `starlette-admin` y siguen siendo responsabilidad suya:

* **Seguridad del transporte:** Sirva el panel de administración mediante HTTPS. Las cookies CSRF y flash están firmadas, pero no cifradas, de modo que cualquiera que intercepte tráfico HTTP plano puede leerlas.
* **Autenticación y autorización:** La instancia `Admin` es pública hasta que usted adjunte un `AuthProvider`. Sin uno, todos los endpoints y rutas están abiertos. Consulte [Autenticación](auth.md).
* **Exposición en red:** Si el panel de administración no necesita acceso público, colóquelo detrás de un firewall, una VPN o una lista blanca de direcciones IP.
* **Higiene de dependencias:** Vigile los avisos de seguridad y mantenga `starlette-admin`, Starlette, su driver de ORM y el resto de sus dependencias actualizados.
* **Acciones posteriores a la autenticación:** La protección CSRF y la validación de subidas no limitan lo que un usuario autenticado puede hacer. El control de acceso granular proviene enteramente de las comprobaciones de permisos que usted escriba en `is_accessible`, `can_create`, `can_edit` y `can_delete`. Consulte [Autenticación](auth.md).

Considere esta página como una guía para configurar el paquete de administración, no como una lista de verificación para proteger todo su despliegue de producción.

---

## Qué viene después

* **[Exportación e importación](export-import.md):** El diálogo de exportación, el ciclo de vida de la vista previa de importación y la estructura del paquete ZIP.
* **[Almacenamiento de archivos](file-storage.md):** Patrones para configurar backends de almacenamiento para `FileField` e `ImageField`.
* **[Autenticación](auth.md):** Cómo `secret_key` gobierna las sesiones de inicio de sesión y las comprobaciones CSRF una vez que añade un proveedor de autenticación.
