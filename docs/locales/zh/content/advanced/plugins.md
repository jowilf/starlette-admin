---
title: 插件
description: 将可复用的 admin 功能与扩展打包为 starlette-admin 的即插即用插件。
source_hash: c9ecd9e51a7426d12b628b06c9c664579e5f269d456e93e9d985c4d2853ac758
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/advanced/plugins/)
<!-- translation-notice:end -->

# 插件

插件是一个通过单一构造函数参数扩展 `starlette-admin` 的 Python 包。插件可以将字段、模板、静态资源、模型转换器、过滤器、导入/导出格式、存储后端、事件订阅者、视图、路由、中间件、主题资源和翻译目录按任意组合打包在一起。

## 使用插件

构造 `Admin` 实例时，通过 `plugins` 参数传入插件：

```python
from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[GeospatialPlugin(default_zoom=13)])
```

选项由插件的构造函数接收，列表则直接传给 `Admin`，无需任何额外的设置或注册。选项会从构造函数一路传递到 Python 后端、Jinja 模板和前端 JavaScript。

## 构建插件

编写插件时，请从官方 Cookiecutter 模板开始。它会生成一个目录结构和配置正确、可直接发布的包。

### 前置要求

使用你的包管理器安装 `cookiecutter`。详情参见[官方安装指南](https://cookiecutter.readthedocs.io/en/stable/README.html#installation)：

```bash
pip install cookiecutter
```

### 脚手架

在任意位置运行该 Cookiecutter 模板：

```bash
cookiecutter gh:jowilf/starlette-admin --directory plugins/cookiecutter-starlette-admin-plugin
```

模板会提示你输入插件名称、包名（slug）、版本以及其他几个变量。完成后，你将得到一个自包含的包，其中包含：

* 一个存放插件类和字段的 `src/` 目录。
* 命名空间正确的 `templates/`、`static/` 和 `translations/` 文件夹。
* 一套完整的测试套件。
* 一个可运行的示例应用。

## 插件 API

每个插件的核心都是一个 `BasePlugin`（`starlette_admin.plugins.BasePlugin`）的子类，它提供的钩子让你能够在 `Admin` 初始化期间注册自己的功能。

```python
from starlette_admin.plugins import BasePlugin


class MyPlugin(BasePlugin):
    name = "my-plugin"
```

`name` 属性是一个唯一的 kebab-case 标识符，同时充当模板和静态资源的命名空间。插件附带的每一个模板和静态文件都必须位于 `plugins/<name>/` 之下。

### 资源文件夹

插件在其包的根目录下只允许携带三个文件夹。无需任何注册，因为 admin 会按约定找到它们：

* `templates/`：Jinja 模板，必须位于 `templates/plugins/<name>/` 之下。
* `static/`：CSS 和 JS 文件等静态资源，必须位于 `static/plugins/<name>/` 之下。
* `translations/`：Babel 翻译目录。

将资源保持在 `plugins/<name>/` 命名空间内，既能避免它们与核心文件或其他插件冲突，又能让用户可以通过自己的 `templates_dir` 或 `static_dir` 进行覆盖。

### 声明式钩子

重写声明式钩子即可注入资源、注册视图或挂载路由。

* `css_links(self, request: Request) -> Sequence[str]`：向每个 admin 页面布局添加样式表。
* `js_links(self, request: Request) -> Sequence[str]`：向每个 admin 页面布局添加脚本。
* `views(self) -> Sequence[BaseView]`：返回要在 admin 侧边栏中注册的视图。返回一个 `DropDown` 即可将它们分组。
* `routes(self) -> Sequence[Route | Mount]`：返回挂载在 `/plugins/<name>/` 下的无界面端点，非常适合 Webhook 和代理端点。
* `middlewares(self) -> Sequence[Middleware]`：添加 Starlette 中间件。
* `template_globals(self) -> dict[str, Any]`：暴露 Jinja 全局变量，带有 `<name>_` 前缀以避免冲突。
* `template_filters(self) -> dict[str, Callable]`：以同样的方式暴露带有 `<name>_` 前缀的 Jinja 过滤器。

### setup 钩子

`setup(self, admin: BaseAdmin) -> None` 将插件接入核心注册表。用它来注册模型转换器、过滤器、导入和导出格式、存储后端以及事件订阅者。它在声明式钩子应用之后运行。

```python
def setup(self, admin: "BaseAdmin") -> None:
    admin.events.subscribe(MyEventSubscriber(self.config))
```

### 生命周期钩子

`on_mount(self, admin: BaseAdmin) -> None` 只运行一次，时机是 Starlette 子应用构建并挂载之后。构建好的应用可通过 `admin.app` 访问。

## 模板与覆盖

插件模板会自动加入加载链。用户只需在自己的 `templates_dir` 中按匹配路径放置一个文件即可覆盖模板，用户文件始终优先。例如，要覆盖 `plugins/geospatial/fields/form/point.html`，用户需创建 `templates_dir/plugins/geospatial/fields/form/point.html`。

为了让用户的覆盖模板能够安全地扩展原始模板，每个插件都会获得一个 `@<name>` 前缀映射，其工作方式与 `@core` 前缀相同。覆盖模板以 `{% extends "@geospatial/fields/form/point.html" %}` 开头，从而扩展插件的基础模板而不会递归包含自身。

## 前端 JavaScript 集成

附带自定义字段的插件应按照字段初始化器契约打包其前端脚本。这能确保脚本在整页加载和动态插入的片段中都能正常工作。

* **局部定位：** 只在传入的 `container` 元素内进行查询，绝不查询全局 `document`。
* **保持幂等：** 核心代码会在 DOM 就绪时运行初始化器，并在每次插入行内行或片段时再次运行。
* **使用 data 属性：** 从渲染在字段元素上的 `data-*` 属性读取配置。

```javascript title="plugins/<name>/js/slider.js"
(function () {
  function initSlider(container) {
    var input = container.querySelector('input[type="range"]');
    var output = container.querySelector(".sa-slider-output");
    var suffix = container.dataset.suffix || "";

    input.addEventListener("input", function () {
      output.textContent = input.value + suffix;
    });
  }

  // Register the initializer so core runs it on the right lifecycle events
  window.StarletteAdmin.registerFieldInitializer(function (element) {
    element.querySelectorAll("[data-sa-slider]").forEach(initSlider);
  });
})();
```

## 通过 setup 钩子进行扩展

插件使用现有的公共注册表，而没有自己单独的扩展途径。

* **转换器**：从目标 contrib 后端调用 `register_converter`，将 ORM 列类型映射到你的字段类。将字段本身定义为普通的 `StringField` 子类，以 WKT 文本的形式存储和显示几何数据：

  ```python
  from dataclasses import dataclass
  from typing import Any

  from starlette_admin.contrib.sqla.converters import register_converter
  from starlette_admin.fields import StringField


  @dataclass
  class MyGeoField(StringField): ...


  @register_converter("Geometry")
  def convert_geometry(*args: Any, **kwargs: Any) -> MyGeoField:
      return MyGeoField(*args, **kwargs)
  ```

* **过滤器**：调用 `register_filters` 将过滤器类附加到字段类型上。

  ```python
  from starlette_admin.contrib.sqla.filters import register_filters

  register_filters(MyGeoField, WithinBoundingBoxFilter)
  ```

* **存储**：调用 `register_storage` 以提供新的后端，例如 Azure 或 GCS。

  ```python
  from starlette_admin.storage import register_storage

  register_storage(AzureBlobStorage())
  ```

* **导入器和导出器**：使用 `register_import_format` 和 `register_export_format`。

  ```python
  from starlette_admin.export import register_export_format

  register_export_format("pdf", PDFExporter())
  ```

一个插件可以支持多个 ORM 后端，因此应在 `setup()` 内部有条件地导入它们。这样，即使用户只安装了其中一个，插件也能正常加载：

```python
def setup(self, admin: "BaseAdmin") -> None:
    try:
        from starlette_admin_geospatial.contrib.sqla import register_sqla_converters

        register_sqla_converters()
    except ImportError:
        pass  # geoalchemy2 or sqlalchemy not installed
```

---

## 下一步

* **[自定义主题](custom-themes.md)：** 使用相同的 Cookiecutter 工作流打包并分享完整的视觉体系。
* **[事件](events.md)：** 插件在其 `setup()` 钩子中注册的订阅者 API。
* **[扩展点](extension-points.md)：** 插件可以挂接到的所有注册表和基类。
