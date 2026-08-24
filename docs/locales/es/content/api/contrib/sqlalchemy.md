---
title: Referencia de la API de Contrib para SQLAlchemy
description: Documentación de referencia de la API para la integración del backend
  SQLAlchemy en starlette-admin.
source_hash: c966b22ba523b8451e3c0168394e068bf412475140a3d5427bc0c70d2c6d971d
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/api/contrib/sqlalchemy/)
<!-- translation-notice:end -->

# Contrib: SQLAlchemy

Referencia completa de atributos y métodos para el backend de SQLAlchemy (`starlette_admin.contrib.sqla`),
generada a partir de las docstrings. Para una guía orientada a tareas, consulte
[SQLAlchemy](../../integrations/sqlalchemy.md).

::: starlette_admin.contrib.sqla.admin.Admin

::: starlette_admin.contrib.sqla.view.ModelView

::: starlette_admin.contrib.sqla.view.InlineModelView

## Validación con Pydantic

La extensión `ext.pydantic` valida los datos del formulario contra un modelo de Pydantic antes de
escribir el registro. Consulte [Validación con Pydantic](../../integrations/sqlalchemy.md#pydantic-validation) para
obtener la guía completa.

::: starlette_admin.contrib.sqla.ext.pydantic.ModelView

## Campos

::: starlette_admin.contrib.sqla.fields.MultiplePKField

::: starlette_admin.contrib.sqla.fields.FileField

::: starlette_admin.contrib.sqla.fields.ImageField

## Convertidores

::: starlette_admin.contrib.sqla.converters.BaseSQLAModelConverter

::: starlette_admin.contrib.sqla.converters.ModelConverter

## Excepciones

::: starlette_admin.contrib.sqla.exceptions.InvalidModelError

::: starlette_admin.contrib.sqla.exceptions.InvalidQuery

::: starlette_admin.contrib.sqla.exceptions.NotSupportedColumn

::: starlette_admin.contrib.sqla.exceptions.NotSupportedValue

!!! note
    Las clases de filtros concretas (`EqualFilter`, `ContainsFilter`, `BetweenFilter`, etc.) no se
    enumeran aquí. Reflejan uno a uno los filtros independientes del backend documentados en
    [Filtros](../filters.md); el comportamiento específico de SQLAlchemy que conviene conocer está
    cubierto en [SQLAlchemy](../../integrations/sqlalchemy.md#filter-registry).
