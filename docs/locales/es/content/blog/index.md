---
source_hash: d0594ec094733ff9a9b13d38f4b41a9088a8fd35e54d762f918681da30ddbd29
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/blog/)
<!-- translation-notice:end -->

# Blog para desarrolladores

Esta sección proporciona patrones avanzados y técnicas prácticas para construir interfaces de administración con `starlette-admin`. Estos artículos se centran en implementaciones reales que amplían la documentación de referencia estándar.

## Publicar una nueva entrada

La plataforma Zensical actualmente depende de un índice estático mantenido manualmente para el contenido del blog. Para publicar un nuevo artículo, complete los siguientes pasos:

1. **Cree el contenido:** escriba su publicación y guarde el archivo Markdown dentro del directorio `blog/posts/`.
2. **Actualice el índice:** añada una nueva fila a la tabla **Artículos publicados** que se encuentra a continuación, incluyendo la fecha de publicación y un enlace relativo a su archivo.
3. **Actualice la configuración:** registre la ruta de la nueva entrada en el archivo `zensical.toml`.

## Artículos publicados

| Fecha | Título del artículo |
| --- | --- |
| 2026-07-13 | [Añadir un panel de administración a FastAPI en 5 minutos con starlette-admin](posts/add-admin-panel-to-fastapi-in-5-minutes.md) |
| 2026-07-10 | [Eliminación lógica y una vista de papelera con FastAPI y starlette-admin](posts/soft-deletes-trash-view.md) |
