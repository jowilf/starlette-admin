---
title: 部件 API 参考
description: starlette-admin 中仪表盘和表单布局部件的完整 API 参考。
source_hash: da6469e2d30b13afb7827dac861073c091225333cce9307a41dc3c1ff24913e5
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/api/widgets/)
<!-- translation-notice:end -->

# 部件

部件系统的完整属性与方法参考，内容由 docstring 生成。如需面向任务式讲解，请参阅[自定义视图与部件](../user-guide/custom-views.md)和[表单布局](../advanced/form-layout.md)。

部件是可组合、可渲染的构建块，用于动态构建 UI 元素。下列每个部件类都可以直接从 `starlette_admin` 导入。

根据上下文不同，部件系统主要承担两种角色：

* **仪表盘与自定义页面：**用作 [`CustomView`](views.md#starlette_admin.views.CustomView) 的 `widget` 属性，构建独立界面和指标看板。
* **表单布局：**用作 [`BaseModelView`](views.md#starlette_admin.views.BaseModelView) 的 `form_layout` 属性，在创建/编辑表单上排列和分组输入项。

---

## 基类

所有部件均继承自一个公共基类，该基类定义了标准的渲染与资源收集接口。

::: starlette_admin.widgets.BaseWidget

---

## 内容部件

内容部件充当 UI 树的叶节点。它们不包含其他部件，而是展示实时数据。每个内容部件都接受一个异步回调，该回调在每个请求中调用一次，确保渲染出的值始终是最新的。

::: starlette_admin.widgets.StatWidget
::: starlette_admin.widgets.ChartWidget
::: starlette_admin.widgets.TableWidget
::: starlette_admin.widgets.TextWidget
::: starlette_admin.widgets.HtmlWidget
::: starlette_admin.widgets.DividerWidget

---

## 布局部件

布局部件是容器，用于排列其 `children`（可以是内容部件、表单字段或其他布局部件）。

**自动资源管理：**布局部件会递归遍历自身的树结构，从子节点收集 `additional_css_links` 和 `additional_js_links`。这确保深层嵌套的组件无需任何手动接线即可自动加载所需的 CSS/JS 资源。

::: starlette_admin.widgets.RowWidget
::: starlette_admin.widgets.CardRowWidget
::: starlette_admin.widgets.ColumnWidget
::: starlette_admin.widgets.GridWidget
::: starlette_admin.widgets.PanelWidget
::: starlette_admin.widgets.FieldsetWidget
::: starlette_admin.widgets.TabsWidget

---

## 响应式尺寸

专用于管理不同屏幕尺寸下的响应式网格行为、列宽和断点的工具类。

::: starlette_admin.widgets.Breakpoints
::: starlette_admin.widgets.Col

---

## 表单布局引用

专用于模型表单场景的特殊部件，用于引用特定的数据库字段。

::: starlette_admin.widgets.FieldRef

---

## 简写与规范化

为了让布局代码整洁且易于阅读，容器部件接受普通 Python 类型来代替显式的部件类实例化。在初始化期间（`__post_init__`），容器会自动将这些简写值解析为对应的部件对象。

**支持的简写形式：**

* `str`：解析为字段引用（`FieldRef`）。
* `tuple`：解析为并排行（`RowWidget`）。
* `list`：解析为垂直堆叠（`ColumnWidget`）。

::: starlette_admin.widgets.WidgetShorthand
::: starlette_admin.widgets.normalize_widget

---

## 辅助函数

用于在 Jinja2 模板或自定义上下文中渲染部件的工具函数。

::: starlette_admin.widgets.render_widget
