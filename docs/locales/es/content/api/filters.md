---
title: Referencia de la API de filtros
description: Documentación de referencia de la API para los filtros de consultas de
  base de datos en starlette-admin.
source_hash: c26f3e6379afdc4268934bf0f05b895ebb00f0517dd9834b6fbc337c4f192231
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/api/filters/)
<!-- translation-notice:end -->

# Filtros

Referencia completa de atributos y métodos del sistema de filtros, generada a partir de las docstrings. Para un recorrido orientado a tareas, consulte [Filtros](../user-guide/filters.md) y
[Filtros personalizados](../advanced/custom-filters.md).

Las clases siguientes son independientes del backend: declaran el `name`, la `label` y el
`data_type` de un filtro, pero no su lógica de consulta. Cada backend ORM (`contrib.sqla`, `contrib.beanie`,
`contrib.mongoengine`, `contrib.tortoise`) crea subclases de ellas para añadir la implementación real de `apply()` para ese
backend. Consulte la [página de integración](../integrations/sqlalchemy.md) correspondiente para conocer las clases de filtros concretas que puede importar.

## Tipos principales

::: starlette_admin.filters.base.FilterDataType

::: starlette_admin.filters.base.BaseFilter

::: starlette_admin.filters.base.FilterApplyContext

::: starlette_admin.filters.base.FilterValidationError

::: starlette_admin.filters.base.FilterRule

::: starlette_admin.filters.base.FilterGroup

::: starlette_admin.filters.registry.FilterRegistry

::: starlette_admin.filters.registry.filters

## Genéricos

::: starlette_admin.filters.generic.EqualFilter

::: starlette_admin.filters.generic.NotEqualFilter

::: starlette_admin.filters.generic.IsNullFilter

::: starlette_admin.filters.generic.IsNotNullFilter

## Numéricos

::: starlette_admin.filters.numeric.EqualFilter

::: starlette_admin.filters.numeric.NotEqualFilter

::: starlette_admin.filters.numeric.GreaterThanFilter

::: starlette_admin.filters.numeric.LessThanFilter

::: starlette_admin.filters.numeric.GreaterThanOrEqualFilter

::: starlette_admin.filters.numeric.LessThanOrEqualFilter

::: starlette_admin.filters.numeric.BetweenFilter

## Cadenas de texto

::: starlette_admin.filters.string.ContainsFilter

::: starlette_admin.filters.string.NotContainsFilter

::: starlette_admin.filters.string.StartsWithFilter

::: starlette_admin.filters.string.EndsWithFilter

## Booleanos

::: starlette_admin.filters.boolean.IsTrueFilter

::: starlette_admin.filters.boolean.IsFalseFilter

## Fecha y hora

::: starlette_admin.filters.date.DateEqualFilter

::: starlette_admin.filters.date.DateTimeEqualFilter

::: starlette_admin.filters.date.TimeEqualFilter

::: starlette_admin.filters.date.DateBetweenFilter

::: starlette_admin.filters.date.DateTimeBetweenFilter

::: starlette_admin.filters.date.TimeBetweenFilter

::: starlette_admin.filters.date.DateInPastFilter

::: starlette_admin.filters.date.DateInFutureFilter

## Enum

::: starlette_admin.filters.enum.InFilter

::: starlette_admin.filters.enum.NotInFilter

## Arrays

::: starlette_admin.filters.array.InFilter

::: starlette_admin.filters.array.NotInFilter
