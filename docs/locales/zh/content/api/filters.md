---
title: 过滤器 API 参考
description: starlette-admin 数据库查询过滤器的 API 参考文档。
source_hash: c26f3e6379afdc4268934bf0f05b895ebb00f0517dd9834b6fbc337c4f192231
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/api/filters/)
<!-- translation-notice:end -->

# 过滤器

过滤器系统的完整属性和方法参考，由 docstring 生成。如需面向任务的指引，请参阅[过滤器](../user-guide/filters.md)和[自定义过滤器](../advanced/custom-filters.md)。

以下类与后端无关：它们只声明过滤器的 `name`、`label` 和 `data_type`，而不包含查询逻辑。每个 ORM 后端（`contrib.sqla`、`contrib.beanie`、`contrib.mongoengine`、`contrib.tortoise`）都会继承这些类，为该后端添加实际的 `apply()` 实现。具体的、可导入的过滤器类请参见相应的[集成页面](../integrations/sqlalchemy.md)。

## 核心类型

::: starlette_admin.filters.base.FilterDataType

::: starlette_admin.filters.base.BaseFilter

::: starlette_admin.filters.base.FilterApplyContext

::: starlette_admin.filters.base.FilterValidationError

::: starlette_admin.filters.base.FilterRule

::: starlette_admin.filters.base.FilterGroup

::: starlette_admin.filters.registry.FilterRegistry

::: starlette_admin.filters.registry.filters

## 通用

::: starlette_admin.filters.generic.EqualFilter

::: starlette_admin.filters.generic.NotEqualFilter

::: starlette_admin.filters.generic.IsNullFilter

::: starlette_admin.filters.generic.IsNotNullFilter

## 数值

::: starlette_admin.filters.numeric.EqualFilter

::: starlette_admin.filters.numeric.NotEqualFilter

::: starlette_admin.filters.numeric.GreaterThanFilter

::: starlette_admin.filters.numeric.LessThanFilter

::: starlette_admin.filters.numeric.GreaterThanOrEqualFilter

::: starlette_admin.filters.numeric.LessThanOrEqualFilter

::: starlette_admin.filters.numeric.BetweenFilter

## 字符串

::: starlette_admin.filters.string.ContainsFilter

::: starlette_admin.filters.string.NotContainsFilter

::: starlette_admin.filters.string.StartsWithFilter

::: starlette_admin.filters.string.EndsWithFilter

## 布尔

::: starlette_admin.filters.boolean.IsTrueFilter

::: starlette_admin.filters.boolean.IsFalseFilter

## 日期与时间

::: starlette_admin.filters.date.DateEqualFilter

::: starlette_admin.filters.date.DateTimeEqualFilter

::: starlette_admin.filters.date.TimeEqualFilter

::: starlette_admin.filters.date.DateBetweenFilter

::: starlette_admin.filters.date.DateTimeBetweenFilter

::: starlette_admin.filters.date.TimeBetweenFilter

::: starlette_admin.filters.date.DateInPastFilter

::: starlette_admin.filters.date.DateInFutureFilter

## 枚举

::: starlette_admin.filters.enum.InFilter

::: starlette_admin.filters.enum.NotInFilter

## 数组

::: starlette_admin.filters.array.InFilter

::: starlette_admin.filters.array.NotInFilter
