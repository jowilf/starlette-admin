---
title: 自定义主题
description: 覆盖 Tabler CSS 变量、注入自定义样式表，调整 starlette-admin 仪表盘的整体外观。
source_hash: 385a0c0718253e051a98f4f310990ad32d3e3babcae40ccddf75e59b931fe937
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/advanced/custom-themes/)
<!-- translation-notice:end -->

# 自定义主题

你可以通过主题设置、自定义模板和静态文件来重新定制管理后台的样式。`DefaultTheme` 通过将来自 `TablerSettings` 对象的 data 属性写入 `<html>` 标签来控制默认外观。如需更深入的修改，可以继承 `BaseTheme` 来打包自己的模板、静态资源和图标集，或将自定义的模板目录和静态目录传给 `Admin`。

## 应用主题

使用 `TablerSettings` 设置调色板、圆角半径和颜色模式。将其传给 `DefaultTheme`，再把后者传给 `Admin` 实例的 `theme` 参数。

```python
from myapp.models import Post
from sqlalchemy import create_engine
from starlette_admin.theme import DefaultTheme, TablerSettings
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///admin.sqlite")

admin = Admin(
    engine,
    title="My Admin",
    theme=DefaultTheme(
        settings=TablerSettings(base="slate", primary="blue", radius=2, mode="dark")
    ),
)
admin.add_view(ModelView(Post))
```

参见 [examples/08-themes](https://github.com/jowilf/starlette-admin/tree/main/examples/08-themes)，这是一个每次启动都随机选择主题的可运行应用。

此配置直接向根 `<html>` 元素应用 `data-bs-theme*` 属性：

```html
<html data-bs-theme="dark"
      data-bs-theme-base="slate"
      data-bs-theme-primary="blue"
      data-bs-theme-radius="2">

```

## `TablerSettings` 参考

| 属性 | 类型 | 默认值 | 有效取值 |
| --- | --- | --- | --- |
| `mode` | `str` | `"light"` | `"light"`, `"dark"` |
| `base` | `str | None` | `"stone"` | `"slate"`, `"gray"`, `"zinc"`, `"neutral"`, `"stone"`, `"pink"` |
| `primary` | `str | None` | `"blue"` | `"blue"`, `"azure"`, `"indigo"`, `"purple"`, `"pink"`, `"red"`, `"orange"`, `"yellow"`, `"lime"`, `"green"`, `"teal"`, `"cyan"`, `"inverted"` |
| `radius` | `float | None` | `1` | `0`, `0.5`, `1`, `1.5`, `2` |

## 使用类名映射重新定制组件样式 {#restyling-components-with-a-class-map}

核心模板不会硬编码组件样式。它们通过 Jinja 辅助函数 `cls('role.name')` 渲染 class 属性，该函数将语义角色（如 `form.save_button` 或 `list.table`）解析为 CSS 类名字符串。每个角色的默认值定义在 `starlette_admin.theme.CoreClasses` 中。

要重新定制某个角色的样式，需编写一个 `ClassMap` 子类。未映射的角色会回退到 `CoreClasses`，因此部分覆盖是安全的。请注意，按钮角色会设置元素的整个 class 属性，包括变体、尺寸和间距，因此映射一个角色会完全替换按钮的外观。

类名映射并不要求完整的自定义主题。要调整默认主题，可继承 `DefaultTheme` 并从 `get_class_map()` 返回你的映射：

```python
from starlette_admin.theme import ClassMap, DefaultTheme


class MyClasses(ClassMap):
    classes = {
        # Rounded success save button instead of the default primary one
        "form.save_button": "btn btn-success rounded-pill",
        # Outline create button on the list toolbar
        "list.create_button": "btn btn-outline-primary ms-2",
        # Pill-shaped filter chips
        "filter.chip": "badge rounded-pill bg-primary-subtle",
    }


class MyTheme(DefaultTheme):
    def get_class_map(self) -> ClassMap:
        return MyClasses()


admin = Admin(engine, title="My Admin", theme=MyTheme())
```

完整的角色词汇表请阅读 `starlette_admin/theme.py` 中的 `CoreClasses.classes`。角色涵盖三类样式：

* **按钮：** 每个按钮位置对应一个角色，涵盖表单页脚、列表工具栏、过滤器栏、动作模态框和行内编辑。你设置的值会成为按钮的整个 class 属性。
* **组件类：** 更换其他 CSS 框架时必须替换的框架特定类名，例如 `list.table`、`modal.base` 或 `filter.chip`。
* **运行时类：** 由核心 JavaScript 动态应用的类名，例如 `alert.success` 或 `import.status_badge`。

## 构建并分享自定义主题

你可以将主题打包并发布到 PyPI，就像插件一样。继承 `BaseTheme` 可以构建一个可复用的 Python 包，用于在多个项目中替换管理后台的布局和样式，或与他人共享一套视觉体系。

### 使用 Cookiecutter 生成脚手架

从官方 cookiecutter 模板开始。它会生成一个具有正确目录结构和配置文件的可发布包。

使用你的包管理器安装 `cookiecutter`。详情参见[官方安装指南](https://cookiecutter.readthedocs.io/en/stable/README.html#installation)：

```bash
pip install cookiecutter

```

然后在任意目录下运行该模板：

```bash
cookiecutter gh:jowilf/starlette-admin --directory themes/cookiecutter-starlette-admin-theme

```

模板会提示你输入主题名称、包 slug、版本以及其他几个变量。完成后，你将得到一个自包含的包，其中包含：

* 一个 `src/` 目录，包含主题类、图标集和类名映射。
* 预先配置好的 `templates/`、`static/` 和翻译文件夹。
* 一套测试和一个可运行的示例应用。

### `BaseTheme` 架构

主题位于渲染链的根部，每个 `Admin` 实例恰好有一个活动主题。`BaseTheme` 子类可配置以下部分：

* **模板：** 包内 `templates/` 文件夹中的替换模板，使用纯相对路径，如 `base.html`、`layout.html` 或 `list.html`。活动主题位于 Jinja 加载器链中插件之上，因此可以同时重新定制核心模板和插件模板的样式。
* **静态资源：** 包内 `static/` 目录中的样式表、脚本和图片。
* **图标集：** 由 `get_icon_set()` 返回的自定义 `IconSet` 子类，将语义键（如 `list.new` 或 `auth.logout`）映射到 CSS 类名。
* **类名映射：** 由 `get_class_map()` 返回的 `ClassMap` 子类，详见[使用类名映射重新定制组件样式](#restyling-components-with-a-class-map)。
* **模板全局变量：** 通过重写 `template_globals()` 向 Jinja 暴露的全局变量。

### 主题包示例

```python
from typing import Any
from starlette_admin.theme import BaseTheme, ClassMap, IconSet


class CustomIconSet(IconSet):
    icons = {
        "list.new": "hi hi-plus",
        "default_actions.view": "hi hi-eye",
        # Map remaining semantic icon keys
    }


class CorporateClasses(ClassMap):
    classes = {
        "form.save_button": "btn btn-corporate",
        # Map remaining roles to restyle; unmapped roles keep core defaults
    }


class CorporateTheme(BaseTheme):
    name = "corporate"
    package = "corporate_theme_package"  # Auto-detected from class module if omitted

    def get_icon_set(self) -> IconSet:
        return CustomIconSet()

    def get_class_map(self) -> ClassMap:
        return CorporateClasses()

    def template_globals(self) -> dict[str, Any]:
        return {"company_name": "Acme Corp"}
```

### 模板加载器层级

模板引擎按以下顺序解析文件：

1. 你的 `templates_dir`，它覆盖其下的一切。
2. 活动主题的 `templates/`，用于重新定制核心和插件模板的样式。
3. 带命名空间的插件 `templates/`。
4. 核心 `starlette_admin` 默认模板。

要从用户覆盖或主题子类扩展主题模板，请使用 `@theme` Jinja 前缀，例如 `{% extends "@theme/layout.html" %}`。

## 自定义模板目录

要在不构建完整主题的情况下覆盖默认 HTML，请将目录路径传给 `templates_dir`。

```python
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

放入该目录的任何文件都会遮蔽相对路径相同的内置模板，内置目录树的其余部分照常渲染。可覆盖模板的完整列表参见[模板](templates.md)。

## 自定义静态目录

要在不构建完整主题的情况下添加自己的 CSS、JavaScript 或图片，请将目录路径传给 `static_dir`。

```python
admin = Admin(engine, title="My Admin", static_dir="my_static/")
```

此目录中的文件与 `/admin/static/` 下的内置资源一同提供服务。例如，`my_static/custom.css` 处的文件可通过 `/admin/static/custom.css` 访问。

在模板中这样引用样式表：

```html
<link rel="stylesheet" href="{{ url_for('admin:static', path='custom.css') }}">

```

---

## 下一步

* **[模板](templates.md)：** 覆盖单个页面、单元格或部件，而无需分叉整个模板树。
* **[扩展点](extension-points.md)：** 探索基础主题之外的钩子和自定义点。
* **[快速上手](../getting-started/quickstart.md)：** 从零构建一个可用的管理界面。
