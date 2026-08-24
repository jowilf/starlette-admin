---
source_hash: d0594ec094733ff9a9b13d38f4b41a9088a8fd35e54d762f918681da30ddbd29
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/blog/)
<!-- translation-notice:end -->

# Blog para desarrolladores

Esta sección ofrece patrones avanzados y técnicas prácticas para construir interfaces de administración con `starlette-admin`. Estos artículos se centran en implementaciones del mundo real que amplían la documentación de referencia estándar.

## Publicar una nueva entrada

La plataforma Zensical depende actualmente de un índice estático mantenido manualmente para el contenido del blog. Para publicar un nuevo artículo, complete los siguientes pasos:

1. **Cree el contenido:** Escriba su entrada y guarde el archivo Markdown dentro del directorio `blog/posts/`.
2. **Actualice el índice:** Añada una nueva fila a la tabla **Artículos publicados** que aparece abajo, incluyendo la fecha de publicación y un enlace relativo a su archivo.
3. **Actualice la configuración:** Registre la ruta de la nueva entrada en el archivo `zensical.toml`.

## Artículos publicados

| Fecha | Título del artículo |
| --- | --- |
| 2026-07-13 | [Add an Admin Panel to FastAPI in 5 Minutes with starlette-admin](posts/add-admin-panel-to-fastapi-in-5-minutes.md) |
| 2026-07-10 | [Soft Deletes and a Trash View with FastAPI & starlette-admin](posts/soft-deletes-trash-view.md) |
