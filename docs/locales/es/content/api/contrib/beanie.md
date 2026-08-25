---
title: Referencia de la API de Contrib para Beanie
description: Documentación de referencia de la API para la integración del backend
  Beanie en starlette-admin.
source_hash: 6a89593e9010ec12dd664910d2bbb407467441efa960bc4a6fefd818a7d71b36
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/api/contrib/beanie/)
<!-- translation-notice:end -->

# Contrib: Beanie

Referencia completa de atributos y métodos para el backend Beanie (`starlette_admin.contrib.beanie`),
generada a partir de las docstrings. Para una guía orientada a tareas, consulte
[Beanie](../../integrations/beanie.md).

::: starlette_admin.contrib.beanie.admin.Admin

::: starlette_admin.contrib.beanie.view.ModelView

::: starlette_admin.contrib.beanie.view.InlineModelView

## Fields

::: starlette_admin.contrib.beanie.fields.BeanieObjectIdField

## Converters

::: starlette_admin.contrib.beanie.converters.BeanieModelConverter

!!! note
    Las clases de filtros concretas (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter`, etc.) no
    se enumeran aquí. Reflejan los filtros independientes del backend documentados en
    [Filters](../filters.md); el comportamiento específico de Beanie (coincidencia de cadenas con regex ancladas,
    búsqueda de texto completo) se cubre en [Beanie](../../integrations/beanie.md#filter-registry).
