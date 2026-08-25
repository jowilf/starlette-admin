---
title: 字段
description: starlette-admin 全部内置字段的完整参考，用于将数据库列映射到 UI 组件。
source_hash: 3c9c4a5f2b25717d80f8f6130fa12fdb5e0ae0ff8ef86c4c692b63f3a6f4bada
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/fields/)
<!-- translation-notice:end -->

# 字段

字段是视图的基本构建单元。其底层是普通的 Python 数据类（dataclass）：传给字段构造器的每个属性都会成为数据类字段，并且每种字段类型都是 `BaseField` 的子类，因此你可以检查、继承或直接实例化它们。

## 通用属性

每种字段类型都从 `BaseField` 继承这组配置属性。

| 属性 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `name` | `str` | **必填** | 模型上的属性名。 |
| `label` | `str | None` | 首字母大写的 `name` | 表格列标题和表单标签。 |
| `help_text` | `str | None` | `None` | 显示在表单输入框下方的提示文本。 |
| `required` | `bool` | `False` | 在客户端和服务器端的表单中都要求提供值。 |
| `validators` | `list[Validator]` | `[]` | 针对提交值运行的服务器端校验器。参见[校验](#validation)。 |
| `disabled` | `bool` | `False` | 在表单中将输入框置灰并锁定。 |
| `read_only` | `bool` | `False` | 显示该字段但禁止编辑。 |
| `default` | `Any | Callable` | `None` | 创建表单上的预填值。 |
| `getter` | `Callable | None` | `None` | 在读取值时替代模型属性查找。参见[计算、格式化与解析值](#computing-formatting-and-parsing-values)。 |
| `formatter` | `dict[RequestAction, Callable] | None` | `None` | 针对特定动作的显示格式化，会替代该动作的序列化。参见[计算、格式化与解析值](#computing-formatting-and-parsing-values)。 |
| `parser` | `dict[RequestAction, Callable] | None` | `None` | 针对特定动作的输入解析，会替代字段的默认解析。参见[计算、格式化与解析值](#computing-formatting-and-parsing-values)。 |
| `searchable` | `bool` | `True` | 当 `q` 搜索参数匹配时包含该字段。 |
| `orderable` | `bool` | `True` | 在列表表头中添加排序链接。 |
| `copy_to_clipboard` | `bool` | `False` | 在详情页的值旁边添加复制按钮。 |
| `filters` | `list | None` | `None` | 对列表页过滤器的显式覆盖。 |
| `extra` | `dict[str, Any]` | `{}` | 用于存放自定义元数据的字典。 |

### 可见性控制

使用这些布尔标志（默认均为 `False`）来控制字段出现的位置：

* `exclude_from_list`
* `exclude_from_detail`
* `exclude_from_create`
* `exclude_from_edit`
* `exclude_from_export`
* `exclude_from_import`

### 定义默认值

`default` 属性接受静态值、无参可调用对象，或感知请求的函数：

```python
from datetime import datetime
from starlette_admin import DateTimeField, StringField

StringField("status", default="draft")  # Static value
DateTimeField("created_at", default=datetime.utcnow)  # Zero-arg callable
StringField(
    "locale", default=lambda request: request.state.admin_user.locale
)  # Request-aware
```

### 计算、格式化与解析值 {#computing-formatting-and-parsing-values}

每个字段都接受三个可调用钩子：`getter`、`formatter` 和 `parser`，它们会在数据于模型与 UI 之间流转时拦截并转换数据。每个钩子都可以接受同步或异步函数。

#### `getter`：读取自定义值

当字段读取模型实例时，`getter` 钩子会取代默认的 `getattr()` 查找。字段会调用 `getter(request, obj)` 并显示返回值。

```python
from starlette_admin import StringField

# Displays a related author's email instead of a direct column value
StringField("author_email", getter=lambda request, obj: obj.author.email)
```

由于 `getter` 返回的值很少对应物理数据库列，因此最适合与只读展示搭配使用。[`ComputedField`](#computedfield) 正是为这种组合提供的内置捷径。

#### `formatter`：转换显示输出

`formatter` 钩子设定已存储的值在特定页面上的渲染方式。它将一个 `RequestAction`（如 `LIST`、`DETAIL` 或 `EXPORT`）映射到一个 `(request, value) -> value` 可调用对象。

```python
from starlette_admin import RequestAction, StringField

StringField(
    "api_key",
    formatter={
        # Mask the key on list views; show the full key on detail/export views
        RequestAction.LIST: lambda request, value: (
            f"{value[:4]}..." if value else "unset"
        ),
    },
)
```

**需要牢记的格式化行为：**

* **空值也会传入 formatter：** 与默认序列化不同，formatter 会接收到 `None` 值，因此你可以提供回退文本，例如上例中的 `"unset"`。
* **跳过序列化：** 匹配到的 formatter 会替代字段的 `serialize_value` 和 `serialize_none_value` 方法。返回值会被原样使用，因此最终输出完全由 formatter 负责。
* **JSON 要求：** 针对 `LIST` 和 `RELATION_LOOKUP` 动作返回的值必须保持 JSON 可序列化。

#### `parser`：处理传入数据

`parser` 钩子会覆盖字段对提交或导入数据的默认解析。它将一个 `RequestAction` 映射到一个 `(request, raw) -> value` 可调用对象。

* **表单（`CREATE`、`EDIT`、`INLINE_EDIT`）：** `raw` 是提交的表单输入；当 `multiple=True` 时则为列表。
* **导入（`IMPORT`）：** `raw` 是文件中未经处理的单元格值。

```python
from starlette_admin import IntegerField, RequestAction

IntegerField(
    "price",
    parser={
        # Strip currency symbols during import and convert to integer cents
        RequestAction.IMPORT: lambda request, raw: int(
            float(str(raw).strip("$")) * 100
        ),
    },
)
```

解析完成后，返回值会经过标准校验链：先检查 `required`，再执行 `validators`，与字段自行解析数据时的流程完全一致。

!!! tip "用钩子还是子类？"
    对单个字段进行一次性定制时，通常无需创建子类。将这些钩子作为构造器参数传入即可处理读取、显示格式化和输入解析。当逻辑需要在多个视图中复用，或者需要修改 HTML 渲染模板时，再[继承字段类](../advanced/custom-fields.md)。

### 校验 {#validation}

提交创建或编辑表单时，服务器端校验会对每个字段执行，从而确保错误数据不会进入数据库。

校验流程固定如下：

1. **空值：** 当提交值为空时（例如 `None`、`""` 或空集合），仅检查 `required` 标志，校验器将被跳过。
2. **非空值：** 当数据存在时，`validators` 列表中的每个可调用对象会按顺序针对解析后的值依次执行。

#### 校验器签名

校验器接收四个参数：`(request, field, value, form_values)`。

* **`request`：** 当前的 Starlette 请求对象。
* **`field`：** 正在被校验的字段实例。
* **`value`：** 该字段提交并解析后的值。
* **`form_values`：** 以字段名为键、包含所有已解析表单数据的字典，可用于检查其他字段。

要拒绝某个值，抛出 `ValueError` 即可。管理后台会捕获字段的第一个错误，跳过该字段剩余的校验器，并收集全部错误，显示在各自对应的输入框旁边。

#### 内置校验器

[`starlette_admin.validators`](../api/validators.md) 模块提供了标准规则：

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.validators import length, number_range

StringField("title", validators=[length(min=3, max=100)])
IntegerField("price", validators=[number_range(min=0)])
```

#### 自定义与异步校验

自定义校验器可以写成同步或异步函数。由于能接收 `request`，它们可以查询数据库以检查复杂约束。

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")


StringField("slug", validators=[unique_slug])
```

借助 `form_values` 参数，字段级校验器还可以强制执行依赖另一个提交字段的规则。

```python
def not_before_start(request, field, value, form_values):
    start = form_values.get("start_date")
    if start is not None and value < start:
        raise ValueError("End date cannot precede the start date")


DateField("end_date", validators=[not_before_start])
```

#### 特定上下文的校验规则

* **关联关系字段：** `HasOne` 和 `HasMany` 在校验期间会接收到关联记录的主键。
* **文件字段：** 对负载中的每个 `UploadFile` 各执行一次校验。参见[文件与媒体字段](#file-media-fields)。
* **跨字段校验：** 简单的依赖关系可用 `form_values` 处理。若规则覆盖整个表单，请改为在视图中重写 `validate()` 方法。视图级校验只在所有字段都通过各自的校验链之后才会执行。

### 存储自定义元数据

`extra` 是一个普通的 `dict`，`starlette-admin` 从不读写它。可以用它把自定义数据附加到字段实例上，供自定义模板、[BaseAdmin](../api/admin.md#starlette_admin.base.BaseAdmin) 子类中的钩子或其他任何集成点使用，而无需继承字段类：

```python
from starlette_admin import StringField

StringField("sku", extra={"barcode_format": "code128"})
```

---

## 文本字段

### StringField 与 TextAreaField

`StringField` 渲染单行文本输入框，适用于短内容。`TextAreaField` 在此基础上扩展了 `<textarea>` 元素，适用于较长的多行文本。

```python
from starlette_admin import StringField, TextAreaField
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = [
        StringField("title", maxlength=200, placeholder="Post title"),
        TextAreaField("content", rows=10),
    ]
```

| 额外属性 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `maxlength` 和 `minlength` | `int | None` | `None` | HTML 长度约束。 |
| `placeholder` | `str | None` | `None` | 输入框占位符文本。 |
| `rows` *(仅 TextArea)* | `int` | `6` | 可见文本行数。 |

### TinyMCEEditorField

在 `TextAreaField` 的基础上集成 TinyMCE 库提供的所见即所得编辑器。需要安装 `tinymce` 扩展包。

```python
from starlette_admin import TinyMCEEditorField

TinyMCEEditorField("content", height=400, toolbar="undo redo | bold italic")
```

!!! note
    `height`、`menubar`、`statusbar` 和 `toolbar` 属性控制编辑器的界面。其他原生 TinyMCE 配置项可通过 `extra_options` 传入。

### 格式化文本字段

这些 `StringField` 变体渲染对应的 HTML 输入类型，并在记录展示时对值进行格式化。

* `EmailField` (`type="email"`)
* `URLField` (`type="url"`)
* `PhoneField` (`type="tel"`)
* `ColorField` (`type="color"`)
* `UUIDField` (`type="text"`)
* `IPAddressField` (`type="text"`)

!!! note
    当 `validators` 为空时，`EmailField`、`URLField`、`UUIDField` 和 `IPAddressField` 会各自添加匹配的校验器（来自 [`starlette_admin.validators`](../api/validators.md) 的 `email`、`url`、`uuid` 和 `ip_address`）。传入自己的 `validators` 即可覆盖默认行为。

    `UUIDField` 默认设置 `copy_to_clipboard=True`。`IPAddressField` 接受 `ipv4`（默认 `True`）和 `ipv6`（默认 `False`）参数，用于控制其默认校验器接受的地址族。

### PasswordField

在表单中渲染 `<input type="password">` 元素，以隐藏用户输入的内容。

!!! danger
    `PasswordField` 仅在创建和编辑表单中对输入进行掩码处理。它不会覆盖显示模板，因此在列表页和详情页上值仍以**明文**呈现，并且它会以 `DEBUG` 级别记录原始提交值。

    请在密码字段上设置 `exclude_from_list = True` 和 `exclude_from_detail = True`，并在生产环境中关闭 `DEBUG` 日志。

## 数值字段

数值字段处理整数、浮点数和十进制数。

```python
from starlette_admin import DecimalField, FloatField, IntegerField
from starlette_admin.contrib.sqla import ModelView


class ProductView(ModelView):
    fields = [
        IntegerField("stock", min=0, max=10_000),
        FloatField("rating"),
        DecimalField("price", min=0, step="0.01"),
    ]
```

| 额外属性 | 适用范围 | 描述 |
| --- | --- | --- |
| `min` 和 `max` | 整数、十进制 | 允许的最小值和最大值。 |
| `step` | 整数、十进制 | 步长增量约束。 |

!!! note
    `FloatField` 的工作方式不同：它渲染为普通文本输入框，将提交内容转换为 `float`，且不支持 `min`、`max` 或 `step`。

## 日期与时间字段

这些字段使用浏览器原生的日期和时间选择器，底层由对应的标准库类型（`datetime.date`、`datetime.datetime` 和 `datetime.time`）支撑。

```python
from starlette_admin import DateField, DateTimeField, TimeField
from starlette_admin.contrib.sqla import ModelView


class EventView(ModelView):
    fields = [
        DateField("event_date"),
        DateTimeField("starts_at", output_format="medium"),
        TimeField("daily_reminder"),
    ]
```

| 额外属性 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `output_format` | `str | None` | `None` | Babel 显示格式：`"short"`、`"medium"`、`"long"`、`"full"` 或自定义模式。 |
| `search_format` | `str | None` | 取决于所用 ORM | 用于构建数据库搜索查询的格式。 |

!!! note
    启用时区支持后，`DateTimeField` 会在显示时区与数据库时区之间自动进行转换。

### ArrowField

基于 `Arrow` 对象的 `DateTimeField` 变体。在编辑表单之外，它以人性化的相对时间显示，例如“3 小时前”。需要安装 `arrow` 包。

## 选择与集合字段

### EnumField {#enumfield}

通用的选择字段。它渲染 `<select>` 下拉框；当 `multiple=True` 时渲染 `select2` 多选框。其选项来源可以是 Python `Enum` 子类、元组列表，或在请求时加载的选项。

```python
import enum
from starlette_admin import EnumField
from starlette_admin.contrib.sqla import ModelView


class Status(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class PostView(ModelView):
    fields = [
        EnumField("status", enum=Status),
        EnumField("language", choices=[("en", "English"), ("fr", "French")]),
    ]
```

| 额外属性 | 类型 | 描述 |
| --- | --- | --- |
| `enum` | `type[Enum] | None` | 由 Python `Enum` 类生成选项。 |
| `choices` | `Sequence | None` | 静态的 `(value, label)` 对，或纯值。 |
| `choices_loader` | `Callable | None` | 按请求动态计算选项。 |
| `multiple` | `bool` | 启用多选，并将值存储为列表。 |

!!! important
    必须且仅能提供 `enum`、`choices` 或 `choices_loader` 三者之一。

`TimeZoneField`、`CountryField` 和 `CurrencyField` 是基于 Babel 本地化数据的 `EnumField` 子类，需要 `i18n` 扩展包。它们的标签会根据当前请求进行本地化。

### TagsField

基于 `select2` 构建的自由文本标签输入组件。它存储 `list[str]`，无需预定义选项。

### ListField

包装另一个字段，以存储该类型值的有序列表。它渲染为带有添加和删除控件的可重复行。被包装字段的名称会成为 `ListField` 的名称。

```python
from starlette_admin import ListField, StringField

# Renders a repeatable list of string inputs
fields = [ListField(StringField("gallery_urls"))]
```

### CollectionField

将多个子字段组合成一个嵌套对象。适用于内嵌或结构体式的数据，例如 MongoDB 嵌入文档。

```python
from starlette_admin import CollectionField, IntegerField, StringField

fields = [
    CollectionField(
        "shipping_address",
        fields=[
            StringField("street"),
            StringField("city"),
            IntegerField("floor", required=False),
        ],
    ),
]
```

## 专用字段

### JSONField

渲染 JSON 树形结构和代码编辑器，并存储 Python `dict`。可将标准 JSON Schema 字典传给 `validation_schema` 以获得客户端反馈。

### SlugField {#slugfield}

`StringField` 的变体，在客户端根据另一个字段的输入自动填充自身。一旦手动编辑，自动填充即停止。

```python
from starlette_admin import SlugField, StringField

fields = [
    StringField("title"),
    SlugField("slug", populate_from="title"),
]
```

!!! important
    `populate_from` 是必填项，且必须指向同一表单中的另一个字段。生成的 slug 会像其他字符串一样被提交和存储。

### ComputedField {#computedfield}

一种只读的虚拟字段，在展示时由模型实例派生而来，背后没有对应的数据库列。它建立在每个字段都具备的 [`getter` 钩子](#computing-formatting-and-parsing-values)之上，并添加了虚拟列所需的默认配置：不出现在创建表单中、只读、不可搜索且不可排序。

```python
from starlette_admin import ComputedField

fields = [
    "first_name",
    "last_name",
    ComputedField(
        "full_name", getter=lambda request, obj: f"{obj.first_name} {obj.last_name}"
    ),
]
```

对于复杂或需复用的逻辑，请继承 `ComputedField` 并重写 `parse_obj()`，而不是传入内联的 `getter`：

```python
class FullNameField(ComputedField):
    async def parse_obj(self, request, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"
```

`getter` 和 `parse_obj` 的作用相同：表达式简短时使用 `getter`；逻辑跨越多行或需要在多个视图中复用时，则继承 `ComputedField`。在编辑表单上，该字段仍以纯文本形式展示，用户看到的是当前的计算值。

每个 `ComputedField` 子类都保留 `StringField` 的渲染方式。如果计算的值应以其他类型呈现（例如日期、徽章或图片），请直接在该字段类型上设置 `getter=`，并同时设置相应的 `read_only` 和 `exclude_from_*` 标志。

## 文件与媒体字段 {#file-media-fields}

`FileField` 渲染文件上传输入框，`ImageField` 在此基础上增加图片预览和有效性检查。附加 `storage=` 存储后端即可自动保存上传的文件，并将 JSON 格式的 `FileInfo` 字典存入数据库。完整配置参见[文件存储指南](file-storage.md)。

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")
documents_storage = LocalStorage(base_dir="uploads/documents", name="documents")


class ArticleView(ModelView):
    fields = [
        "id",
        "title",
        ImageField(
            "cover",
            storage=covers_storage,
            upload_folder="covers",
            max_size=5 * 1024 * 1024,
            thumbnail_size=(50, 50),
        ),
        FileField(
            "document",
            storage=documents_storage,
            upload_folder="documents",
            accept=".pdf,.doc,.docx",
        ),
    ]
```

| 额外属性 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `accept` | `str | None` | `None` | 接受的文件扩展名或 MIME 类型的逗号分隔列表，传递给 HTML `accept` 属性。 |
| `multiple` | `bool` | `False` | 允许在一个字段中接受多个文件。 |
| `storage` | `BaseStorage | None` | `None` | 保存上传文件的存储后端。若未设置，字段会将原始上传内容交给你的后端处理。 |
| `upload_folder` | `str` | `""` | 已保存文件相对于存储的文件夹路径。 |
| `max_size` | `int | None` | `None` | 允许的最大上传大小，单位为字节。 |
| `validators` | `list[Validator]` | `[]` | 自定义校验器，在 `accept` 和 `max_size` 检查之后，针对每个上传的文件各调用一次 `(request, field, upload)`。抛出 `ValueError` 表示拒绝。 |
| `thumbnail_size` | `tuple[int, int] | None` | `None` | 仅限 `ImageField`。设置后，Pillow 会在保存时生成限定尺寸的缩略图，列表页会用它代替完整图片。 |

!!! note
    `ImageField` 会在 `validators` 列表的最前面插入一个基于 Pillow 的图片有效性检查。当 Pillow 已安装且已配置存储时，还会在生成的 `FileInfo` 中记录 `width` 和 `height`。

设置 `thumbnail_size` 后，后台会在保存完整图片的同时生成一张保持宽高比、绝不放大的缩略图，并以独立的键存储。例如，`covers/cat.jpg` 会得到一个 `covers/cat.thumb.jpg` 副本。列表页会自动使用缩略图；没有缩略图的行（无论是已有数据还是因为未设置 `thumbnail_size` 所致）都会回退到完整图片。缩略图生成失败只会记录日志，绝不会导致上传失败。

详情页会在灯箱中打开每张 `ImageField` 图片，查看者可以翻阅全分辨率图片。属于同一字段的图片（`multiple=True`）会归入同一个画廊。

完整可运行的示例应用（包括自定义 MIME 类型校验器）参见 [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage)。

### 不使用存储

未附加 `storage=` 时，字段会将上传内容原样交给你的后端，而不进行保存：

* **在创建和编辑表单中**，解析后的值是一个元组 `(UploadFile | list[UploadFile] | None, bool)`。第一个元素是原始的 Starlette `UploadFile`（当 `multiple=True` 时为列表），用户未选择任何文件时为 `None`。第二个元素在用户勾选编辑表单上的删除复选框时为 `True`，表示希望移除现有文件且不用新文件替换。你的后端 `create()` 和 `edit()` 逻辑负责保存上传内容并遵循删除标志。
* **在列表页和详情页上**，字段期望该值以 `dict` 形式暴露三个键，或以对象形式暴露三个属性：`url`（必填，即链接目标）、`filename`（显示标签）以及 `content_type`（用于决定显示哪种文件类型图标）。

下方的 ORM 集成正是通过这一约定，将各自的文件处理逻辑接入同一字段。

### ORM 原生文件列

**MongoEngine** 开箱即用地支持 `mongoengine.FileField` 和 `mongoengine.ImageField`，并以 **GridFS** 作为存储。管理后台会替你完成 GridFS 中文件的上传、读取与删除操作。你无需任何 `storage=` 配置，只需按名称列出字段即可。

**SQLAlchemy** 通过 [sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/) 获得同样的支持。在模型上声明其 `FileField` 或 `ImageField` 列类型后，`starlette-admin` 会检测到它们，渲染对应的管理字段，并注册一条路由来提供已存储文件的访问。存储通过 sqlalchemy-file 自身的 `StorageManager` 配置，底层由 Apache Libcloud 容器支撑；上传操作会加入会话事务，因此回滚的会话会丢弃已存储的文件。

```python
import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy_file import ImageField
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.validators import SizeValidator
from starlette_admin.contrib.sqla import ModelView


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    avatar = mapped_column(
        ImageField(
            upload_storage="avatar",
            thumbnail_size=(50, 50),
            validators=[SizeValidator("200k")],
        )
    )


# sqlalchemy-file storage setup, independent of starlette-admin's BaseStorage
os.makedirs("upload/avatars", exist_ok=True)
StorageManager.add_storage(
    "avatar", LocalStorageDriver("upload").get_container("avatars")
)


class AuthorView(ModelView):
    fields = ["id", "name", "avatar"]
```

包含多个存储、内容类型校验和 `multiple=True` 字段的完整应用参见 [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file)。

## HasOne 与 HasMany {#hasone-hasmany}

关联关系字段，渲染为 `select2` 输入框，背后由关联视图的搜索端点支持。

```python
from starlette_admin import HasMany, HasOne, IntegerField, StringField
from starlette_admin.contrib.sqla import Admin, ModelView


class AuthorView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("name"),
        HasMany("books", key="book"),
    ]


class BookView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        HasOne("author", key="author"),
    ]
```

`key` 参数指向匹配的 `ModelView`。请在同一个 `Admin` 实例上注册这两个视图，以便正确解析键。

---

## 后续步骤

* [过滤器](filters.md)：自定义列表页上的过滤器构建器。
* [文件存储](file-storage.md)：为 `FileField` 和 `ImageField` 配置存储后端。
* [自定义字段](../advanced/custom-fields.md)：构建自定义字段。
