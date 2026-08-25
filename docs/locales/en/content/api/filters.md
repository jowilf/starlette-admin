---
title: Filters API Reference
description: API reference documentation for database query filters in starlette-admin.
---

# Filters

Full attribute and method reference for the filter system, generated from docstrings. For a
task-oriented walkthrough, see [Filters](../user-guide/filters.md) and
[Custom Filters](../advanced/custom-filters.md).

The classes below are backend-agnostic: they declare a filter's `name`, `label`, and
`data_type`, but not its query logic. Each ORM backend (`contrib.sqla`, `contrib.beanie`,
`contrib.mongoengine`, `contrib.tortoise`) subclasses them to add the actual `apply()` implementation for that
backend. See the relevant [integration page](../integrations/sqlalchemy.md) for the concrete,
importable filter classes.

## Core types

::: starlette_admin.filters.base.FilterDataType

::: starlette_admin.filters.base.BaseFilter

::: starlette_admin.filters.base.FilterApplyContext

::: starlette_admin.filters.base.FilterValidationError

::: starlette_admin.filters.base.FilterRule

::: starlette_admin.filters.base.FilterGroup

::: starlette_admin.filters.registry.FilterRegistry

::: starlette_admin.filters.registry.filters

## Generic

::: starlette_admin.filters.generic.EqualFilter

::: starlette_admin.filters.generic.NotEqualFilter

::: starlette_admin.filters.generic.IsNullFilter

::: starlette_admin.filters.generic.IsNotNullFilter

## Numeric

::: starlette_admin.filters.numeric.EqualFilter

::: starlette_admin.filters.numeric.NotEqualFilter

::: starlette_admin.filters.numeric.GreaterThanFilter

::: starlette_admin.filters.numeric.LessThanFilter

::: starlette_admin.filters.numeric.GreaterThanOrEqualFilter

::: starlette_admin.filters.numeric.LessThanOrEqualFilter

::: starlette_admin.filters.numeric.BetweenFilter

## String

::: starlette_admin.filters.string.ContainsFilter

::: starlette_admin.filters.string.NotContainsFilter

::: starlette_admin.filters.string.StartsWithFilter

::: starlette_admin.filters.string.EndsWithFilter

## Boolean

::: starlette_admin.filters.boolean.IsTrueFilter

::: starlette_admin.filters.boolean.IsFalseFilter

## Date and time

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

## Array

::: starlette_admin.filters.array.InFilter

::: starlette_admin.filters.array.NotInFilter
