---
title: 扩展点
description: 概述 starlette-admin 中所有可定制的钩子方法、基类和配置点。
source_hash: d9fad2e9fd41b2f2ccc685090f07423b0ee2b96bf0a00b08ef0fbf2b4027ebf2
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/advanced/extension-points/)
<!-- translation-notice:end -->

# 扩展点

本页集中列出 `starlette-admin` 的每一个可插拔接口。找到与要修改的内容相匹配的类、钩子或装饰器，然后点击链接查看完整指南。

| 扩展点 | API 接口或钩子 | 文档 |
| --- | --- | --- |
| **自定义过滤器** | 子类化 `BaseFilter` 并在 `ModelView` 上重写 `get_filter_registry()`。 | [自定义过滤器](custom-filters.md) |
| **自定义导出器** | 子类化 `BaseExporter`。 | [导出与导入](../user-guide/export-import.md) |
| **自定义导入器** | 子类化 `BaseImporter`。 | [导出与导入](../user-guide/export-import.md) |
| **自定义主题** | 子类化 `BaseTheme`。 | [自定义主题](custom-themes.md) |
| **自定义认证后端** | 子类化 `BaseAuthProvider`。 | [认证](../user-guide/auth.md) |
| **自定义文件存储** | 子类化 `BaseStorage`，它会通过自身的 `name` 属性完成注册。 | [文件存储](../user-guide/file-storage.md) |
| **自定义部件** | 子类化 `BaseWidget`。 | [自定义视图](../user-guide/custom-views.md) |
| **自定义视图上的额外路由** | 将 `@route("/path", methods=["GET"])` 装饰器应用于 `CustomView` 方法。 | [自定义视图](../user-guide/custom-views.md) |
| **插件** | 子类化 `BasePlugin`，将字段、视图、资源等打包在一起。 | [插件](plugins.md) |

!!! tip
    要修改默认 Tabler 主题的颜色，无需创建自定义主题，只需将一个 `TablerSettings` 对象传入 `DefaultTheme` 实例即可。

---

## 下一步

* **[核心概念](../getting-started/concepts.md)：** 了解这些可插拔组件如何融入框架的架构。
* **[视图](../user-guide/views.md)：** 探索大多数扩展点所依附的核心视图。
