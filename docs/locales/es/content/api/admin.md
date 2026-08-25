---
title: Referencia de la API de Admin
description: Documentación de referencia de la API para la clase Admin en starlette-admin.
source_hash: 1c016173cc04603ea66bc0c67d4b34273b13d06baea3238d0ca3cd0c5f09c994
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/api/admin/)
<!-- translation-notice:end -->

# Admin

Referencia completa de atributos y métodos de `BaseAdmin`, generada a partir de sus docstrings. Para una guía orientada a tareas sobre las opciones de su constructor, consulte
[Configuring Admin](../user-guide/admin.md).

`starlette_admin` no exporta ninguna clase `Admin` concreta propia. Cada backend en
`starlette_admin.contrib` (`sqla`, `sqlmodel`, `beanie`, `mongoengine`, `tortoise`) incluye su propia subclase de `Admin`
con la misma firma de constructor documentada a continuación.

::: starlette_admin.base.BaseAdmin
