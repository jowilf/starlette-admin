---
title: Поля
description: Подробный справочник по всем встроенным полям starlette-admin для сопоставления
  столбцов базы данных с компонентами интерфейса.
source_hash: 3c9c4a5f2b25717d80f8f6130fa12fdb5e0ae0ff8ef86c4c692b63f3a6f4bada
prompt_hash: efac6b04187c7def41059e1c72e46a95b2ca178220b0cb995f0594e001f3f1a5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
---

<!-- translation-notice:start -->
??? info "Машинный перевод под контролем человека"

    Этот контент переведён с помощью машинной генерации, направляемой
    составленными людьми глоссариями и руководствами по стилю. Поскольку
    текст не проверяется вручную построчно, возможны отдельные ошибки или
    неестественные формулировки.

    В случае любых расхождений авторитетным источником считается
    оригинальная версия на английском языке.

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/fields/)
<!-- translation-notice:end -->

# Поля

Поля — это строительные блоки ваших представлений. Внутри они представляют собой обычные дата-классы Python: каждый атрибут, который вы передаёте в конструктор поля, становится полем дата-класса, а каждый тип поля наследуется от `BaseField`, поэтому его можно инспектировать, наследовать или создавать напрямую.

## Общие атрибуты

Каждый тип поля наследует этот набор атрибутов конфигурации от `BaseField`.

| Атрибут | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `name` | `str` | **Обязательный** | Имя атрибута в вашей модели. |
| `label` | `str | None` | `name` с заглавной буквы | Заголовок столбца и метка формы. |
| `help_text` | `str | None` | `None` | Подсказка под полем ввода формы. |
| `required` | `bool` | `False` | Требует значение в формах как на клиенте, так и на сервере. |
| `validators` | `list[Validator]` | `[]` | Серверные валидаторы, применяемые к отправленному значению. См. [Валидация](#validation). |
| `disabled` | `bool` | `False` | Делает поле ввода неактивным и заблокированным в формах. |
| `read_only` | `bool` | `False` | Показывает поле, но запрещает редактирование. |
| `default` | `Any | Callable` | `None` | Предзаполненное значение на форме создания. |
| `getter` | `Callable | None` | `None` | Заменяет обращение к атрибуту модели при чтении значения. См. [Вычисление, форматирование и разбор значений](#computing-formatting-and-parsing-values). |
| `formatter` | `dict[RequestAction, Callable] | None` | `None` | Форматирование отображения для конкретного действия, заменяющее сериализацию для этого действия. См. [Вычисление, форматирование и разбор значений](#computing-formatting-and-parsing-values). |
| `parser` | `dict[RequestAction, Callable] | None` | `None` | Разбор входных данных для конкретного действия, заменяющий стандартный разбор поля. См. [Вычисление, форматирование и разбор значений](#computing-formatting-and-parsing-values). |
| `searchable` | `bool` | `True` | Поле участвует в поиске по параметру `q`. |
| `orderable` | `bool` | `True` | Добавляет ссылку сортировки в заголовок страницы списка. |
| `copy_to_clipboard` | `bool` | `False` | Добавляет кнопку копирования рядом со значением на странице деталей. |
| `filters` | `list | None` | `None` | Явное переопределение фильтров страницы списка. |
| `extra` | `dict[str, Any]` | `{}` | Словарь для вашей собственной метаданной информации. |

### Управление видимостью

Используйте эти логические флаги (все по умолчанию равны `False`), чтобы управлять тем, где появляется поле:

* `exclude_from_list`
* `exclude_from_detail`
* `exclude_from_create`
* `exclude_from_edit`
* `exclude_from_export`
* `exclude_from_import`

### Задание значений по умолчанию

Атрибут `default` принимает статическое значение, функцию без аргументов или функцию, учитывающую запрос:

```python
from datetime import datetime
from starlette_admin import DateTimeField, StringField

StringField("status", default="draft")  # Статическое значение
DateTimeField("created_at", default=datetime.utcnow)  # Функция без аргументов
StringField(
    "locale", default=lambda request: request.state.admin_user.locale
)  # С учётом запроса
```

### Вычисление, форматирование и разбор значений {#computing-formatting-and-parsing-values}

Каждое поле принимает три вызываемых хука — `getter`, `formatter` и `parser`, — которые перехватывают и преобразуют данные при их передаче между моделью и интерфейсом. Каждый из них принимает синхронную или асинхронную функцию.

#### `getter`: чтение пользовательских значений

Хук `getter` заменяет стандартный поиск через `getattr()`, когда поле читает экземпляр модели. Поле вызывает `getter(request, obj)` и отображает возвращённое значение.

```python
from starlette_admin import StringField

# Отображает email связанного автора вместо прямого значения столбца
StringField("author_email", getter=lambda request, obj: obj.author.email)
```

Поскольку значения `getter` редко соответствуют физическому столбцу базы данных, лучше всего сочетать их с отображением только для чтения. [`ComputedField`](#computedfield) — это встроенное сокращение для такой комбинации.

#### `formatter`: преобразование вывода

Хук `formatter` задаёт способ отображения сохранённого значения на определённых страницах. Он сопоставляет `RequestAction`, например `LIST`, `DETAIL` или `EXPORT`, с функцией вида `(request, value) -> value`.

```python
from starlette_admin import RequestAction, StringField

StringField(
    "api_key",
    formatter={
        # Маскирует ключ на представлениях списка; показывает полный ключ на страницах деталей/экспорта
        RequestAction.LIST: lambda request, value: (
            f"{value[:4]}..." if value else "unset"
        ),
    },
)
```

**Особенности форматирования, о которых стоит помнить:**

* **Значения `None` доходят до форматтера:** В отличие от стандартной сериализации, форматтеры получают значения `None`, поэтому вы можете подставить резервный текст, например `"unset"` выше.
* **Сериализация обходится:** Найденный форматтер заменяет методы `serialize_value` и `serialize_none_value` поля. Возвращаемое значение используется как есть, поэтому форматтер полностью отвечает за итоговый результат.
* **Требование JSON:** Значения, возвращаемые для действий `LIST` и `RELATION_LOOKUP`, должны оставаться сериализуемыми в JSON.

#### `parser`: обработка входных данных

Хук `parser` переопределяет стандартный разбор отправленных или импортированных данных полем. Он сопоставляет `RequestAction` с функцией вида `(request, raw) -> value`.

* **Формы (`CREATE`, `EDIT`, `INLINE_EDIT`):** `raw` — это отправленные данные формы или список, если `multiple=True`.
* **Импорт (`IMPORT`):** `raw` — это необработанное значение ячейки из файла.

```python
from starlette_admin import IntegerField, RequestAction

IntegerField(
    "price",
    parser={
        # Убирает символы валюты при импорте и преобразует в целые центы
        RequestAction.IMPORT: lambda request, raw: int(
            float(str(raw).strip("$")) * 100
        ),
    },
)
```

После разбора возвращённое значение проходит стандартную цепочку валидации — сначала `required`, затем `validators`, — точно так же, как если бы поле разобрало данные само.

!!! tip "Хуки или подкласс?"
    Для разовой настройки отдельного поля подкласс обычно не нужен. Передайте эти хуки как аргументы конструктора, чтобы управлять чтением, форматированием отображения и разбором входных данных. [Наследуйте поле](../advanced/custom-fields.md), когда переиспользуете логику в нескольких представлениях или когда нужно изменить шаблоны HTML-рендеринга.

### Валидация {#validation}

Серверная валидация выполняется для каждого поля при отправке формы создания или редактирования, поэтому некорректные данные никогда не попадают в базу данных.

Жизненный цикл фиксирован:

1. **Пустые значения:** Если отправленное значение пустое, например `None`, `""` или пустая коллекция, проверяется только флаг `required`. Валидаторы пропускаются.
2. **Заполненные значения:** Если данные присутствуют, каждая функция из списка `validators` выполняется по порядку над разобранным значением.

#### Сигнатура валидатора

Валидатор получает четыре аргумента: `(request, field, value, form_values)`.

* **`request`:** Текущий объект запроса Starlette.
* **`field`:** Экземпляр проверяемого поля.
* **`value`:** Разобранное значение, отправленное для этого поля.
* **`form_values`:** Словарь всех разобранных данных формы, где ключами являются имена полей, что позволяет проверить другие поля.

Чтобы отклонить значение, возбудите исключение `ValueError`. Панель администрирования перехватывает первую ошибку для поля, пропускает остальные его валидаторы и собирает все ошибки, чтобы отобразить их рядом с соответствующими полями ввода.

#### Встроенные валидаторы

Модуль [`starlette_admin.validators`](../api/validators.md) предоставляет стандартные правила:

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.validators import length, number_range

StringField("title", validators=[length(min=3, max=100)])
IntegerField("price", validators=[number_range(min=0)])
```

#### Пользовательская и асинхронная валидация

Пишите пользовательские валидаторы как синхронные или асинхронные функции. Они получают `request`, поэтому могут обращаться к базе данных для проверки сложных ограничений.

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")


StringField("slug", validators=[unique_slug])
```

С помощью аргумента `form_values` валидатор уровня поля также может применять правило, зависящее от другого отправленного поля.

```python
def not_before_start(request, field, value, form_values):
    start = form_values.get("start_date")
    if start is not None and value < start:
        raise ValueError("End date cannot precede the start date")


DateField("end_date", validators=[not_before_start])
```

#### Правила валидации для конкретных контекстов

* **Поля связей:** `HasOne` и `HasMany` получают первичные ключи связанных записей во время валидации.
* **Файловые поля:** Валидация выполняется один раз для каждого `UploadFile` в полезной нагрузке. См. [Файловые и медиаполя](#file-media-fields).
* **Межполевая валидация:** Используйте `form_values` для простой зависимости. Для правила, охватывающего всю форму, переопределите метод `validate()` в вашем представлении. Валидация уровня представления выполняется только после того, как каждое поле пройдёт собственную цепочку валидации.

### Хранение пользовательских метаданных

`extra` — это обычный `dict`, который `starlette-admin` никогда не читает и не изменяет. Используйте его, чтобы прикрепить свои данные к экземпляру поля — для пользовательского шаблона, хука в подклассе [BaseAdmin](../api/admin.md#starlette_admin.base.BaseAdmin) или любой другой точки интеграции — без создания подкласса поля:

```python
from starlette_admin import StringField

StringField("sku", extra={"barcode_format": "code128"})
```

---

## Текстовые поля

### StringField & TextAreaField

`StringField` отображает однострочное текстовое поле ввода для короткого содержимого. `TextAreaField` расширяет его элементом `<textarea>` для длинного многострочного текста.

```python
from starlette_admin import StringField, TextAreaField
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = [
        StringField("title", maxlength=200, placeholder="Post title"),
        TextAreaField("content", rows=10),
    ]
```

| Дополнительный атрибут | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `maxlength` и `minlength` | `int | None` | `None` | Ограничения длины HTML. |
| `placeholder` | `str | None` | `None` | Текст-заполнитель поля ввода. |
| `rows` *(только TextArea)* | `int` | `6` | Количество видимых строк текста. |

### TinyMCEEditorField

Расширяет `TextAreaField` WYSIWYG-редактором из библиотеки TinyMCE. Требует дополнительный пакет `tinymce`.

```python
from starlette_admin import TinyMCEEditorField

TinyMCEEditorField("content", height=400, toolbar="undo redo | bold italic")
```

!!! note
    Атрибуты `height`, `menubar`, `statusbar` и `toolbar` управляют интерфейсом редактора. Любую другую нативную конфигурацию TinyMCE передавайте через `extra_options`.

### Форматированные текстовые поля

Эти варианты `StringField` отображают соответствующий тип HTML-поля ввода и форматируют значение при показе записи.

* `EmailField` (`type="email"`)
* `URLField` (`type="url"`)
* `PhoneField` (`type="tel"`)
* `ColorField` (`type="color"`)
* `UUIDField` (`type="text"`)
* `IPAddressField` (`type="text"`)

!!! note
    `EmailField`, `URLField`, `UUIDField` и `IPAddressField` каждый добавляют соответствующий валидатор (`email`, `url`, `uuid` и `ip_address` из [`starlette_admin.validators`](../api/validators.md)), если оставить `validators` пустым. Передайте свой `validators`, чтобы переопределить его.

    `UUIDField` по умолчанию устанавливает `copy_to_clipboard=True`. `IPAddressField` принимает `ipv4` (по умолчанию `True`) и `ipv6` (по умолчанию `False`), которые определяют семейства адресов, принимаемые его стандартным валидатором.

### PasswordField

Отображает элемент `<input type="password">` в формах, скрывая то, что вводит пользователь.

!!! danger
    `PasswordField` маскирует ввод только в формах создания и редактирования. Он не переопределяет шаблоны отображения, поэтому значения показываются **обычным текстом** на страницах списка и деталей, а также записывает сырые отправленные значения в журнал на уровне `DEBUG`.

    Установите `exclude_from_list = True` и `exclude_from_detail = True` для полей паролей и отключите журналирование `DEBUG` в рабочем окружении.

## Числовые поля

Числовые поля работают с целыми числами, числами с плавающей точкой и десятичными дробями.

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

| Дополнительный атрибут | Применяется к | Описание |
| --- | --- | --- |
| `min` и `max` | Integer, Decimal | Минимально и максимально допустимые значения. |
| `step` | Integer, Decimal | Ограничение шага приращения. |

!!! note
    `FloatField` работает иначе: он отображается как обычное текстовое поле ввода, приводит отправленное значение к `float` и не поддерживает `min`, `max` или `step`.

## Поля даты и времени

Эти поля используют нативные средства браузера для выбора даты и времени и опираются на соответствующие типы стандартной библиотеки (`datetime.date`, `datetime.datetime` и `datetime.time`).

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

| Дополнительный атрибут | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `output_format` | `str | None` | `None` | Формат отображения Babel: `"short"`, `"medium"`, `"long"`, `"full"` или пользовательский шаблон. |
| `search_format` | `str | None` | Зависит от ORM | Формат, используемый для построения поисковых запросов к базе данных. |

!!! note
    Когда включена поддержка часовых поясов, `DateTimeField` сам преобразует значения между часовым поясом отображения и часовым поясом базы данных.

### ArrowField

Вариант `DateTimeField`, основанный на объекте `Arrow`. За пределами форм редактирования он отображает человекочитаемое относительное время, например «3 часа назад». Требует пакет `arrow`.

## Поля выбора и коллекций

### EnumField

Универсальное поле выбора. Оно отображает выпадающий список `<select>` или мультивыбор `select2`, если `multiple=True`. Его основой может быть подкласс Python `Enum`, список кортежей или варианты, загружаемые во время запроса.

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

| Дополнительный атрибут | Тип | Описание |
| --- | --- | --- |
| `enum` | `type[Enum] | None` | Строит варианты выбора из класса Python `Enum`. |
| `choices` | `Sequence | None` | Статические пары `(value, label)` или просто значения. |
| `choices_loader` | `Callable | None` | Вычисляет варианты выбора для каждого запроса. |
| `multiple` | `bool` | Включает мультивыбор и сохраняет значения списком. |

!!! important
    Укажите ровно один из параметров: `enum`, `choices` или `choices_loader`.

`TimeZoneField`, `CountryField` и `CurrencyField` — это подклассы `EnumField`, основанные на данных локалей Babel, для которых требуется дополнение `i18n`. Они локализуют свои метки согласно текущему запросу.

### TagsField

Поле ввода свободных тегов, построенное на `select2`. Оно хранит `list[str]` и не требует предопределённых вариантов.

### ListField

Оборачивает другое поле, чтобы хранить упорядоченный список значений этого типа. Оно отображается как повторяемые строки с элементами управления добавления и удаления. Имя обёрнутого поля становится именем `ListField`.

```python
from starlette_admin import ListField, StringField

# Отображает повторяемый список текстовых полей ввода
fields = [ListField(StringField("gallery_urls"))]
```

### CollectionField

Группирует несколько вложенных полей в один вложенный объект. Используйте его для встроенных или структурных данных, например встроенного документа MongoDB.

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

## Специализированные поля

### JSONField

Отображает JSON-дерево и редактор кода, а также хранит Python `dict`. Передайте стандартный словарь JSON Schema в `validation_schema` для обратной связи на стороне клиента.

### SlugField

Вариант `StringField`, который автоматически заполняется на клиенте на основе ввода другого поля. Ручное редактирование отключает автозаполнение.

```python
from starlette_admin import SlugField, StringField

fields = [
    StringField("title"),
    SlugField("slug", populate_from="title"),
]
```

!!! important
    `populate_from` обязателен и должен указывать на другое поле той же формы. Сгенерированный slug отправляется и сохраняется как любая другая строка.

### ComputedField

Виртуальное поле только для чтения, вычисляемое из экземпляра модели во время отображения, без столбца базы данных за ним. Оно строится на хуке [`getter`](#computing-formatting-and-parsing-values), который есть у каждого поля, и добавляет настройки по умолчанию, необходимые виртуальному столбцу: исключено из форм создания, доступно только для чтения, не участвует в поиске и сортировке.

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

Для сложной или переиспользуемой логики создайте подкласс `ComputedField` и переопределите `parse_obj()` вместо передачи инлайн-функции `getter`:

```python
class FullNameField(ComputedField):
    async def parse_obj(self, request, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"
```

`getter` и `parse_obj` выполняют одну и ту же задачу: используйте `getter` для коротких выражений, а создавайте подкласс `ComputedField`, когда логика занимает несколько строк или переиспользуется в разных представлениях. На формах редактирования поле по-прежнему отображается как простой текст, поэтому пользователь видит текущее вычисленное значение.

Каждый подкласс `ComputedField` сохраняет рендеринг `StringField`. Чтобы вычислить значение, которое должно отображаться как другой тип — например дата, бейдж или изображение, — установите `getter=` непосредственно на этом типе поля вместе с соответствующими флагами `read_only` и `exclude_from_*`.

## Файловые и медиаполя {#file-media-fields}

`FileField` отображает поле загрузки файла, а `ImageField` добавляет предварительный просмотр изображения и проверку корректности. Прикрепите бэкенд `storage=`, чтобы автоматически сохранять загрузки и хранить JSON-словарь `FileInfo` в базе данных. Полная конфигурация описана в руководстве [Файловое хранилище](file-storage.md).

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

| Дополнительный атрибут | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `accept` | `str | None` | `None` | Разделённый запятыми список допустимых расширений файлов или MIME-типов, передаваемый в HTML-атрибут `accept`. |
| `multiple` | `bool` | `False` | Принимает несколько файлов в одном поле. |
| `storage` | `BaseStorage | None` | `None` | Бэкенд хранилища, сохраняющий загрузки. Без него поле передаёт сырые загрузки вашему бэкенду. |
| `upload_folder` | `str` | `""` | Папка относительно хранилища для сохранённых файлов. |
| `max_size` | `int | None` | `None` | Максимальный размер загрузки в байтах. |
| `validators` | `list[Validator]` | `[]` | Пользовательские валидаторы; каждый вызывается как `(request, field, upload)` один раз для каждого загруженного файла после проверок `accept` и `max_size`. Возбудите `ValueError`, чтобы отклонить файл. |
| `thumbnail_size` | `tuple[int, int] | None` | `None` | Только `ImageField`. Если задано, Pillow генерирует миниатюру ограниченного размера при сохранении, а страница списка использует её вместо полного изображения. |

!!! note
    `ImageField` добавляет проверку корректности изображения на основе Pillow в начало списка `validators`. Когда Pillow установлен и хранилище настроено, он также записывает `width` и `height` в результирующий `FileInfo`.

При заданном `thumbnail_size` панель администрирования генерирует миниатюру вместе с полным изображением, сохраняя соотношение сторон и никогда не увеличивая масштаб, и сохраняет её под собственным ключом. Например, для `covers/cat.jpg` создаётся соседний файл `covers/cat.thumb.jpg`. Страница списка автоматически использует миниатюру. Строки без неё — из ранее существовавших данных или потому, что `thumbnail_size` не задан, — используют полное изображение. Ошибка генерации миниатюры записывается в журнал и никогда не приводит к сбою загрузки.

Страница деталей открывает каждое изображение `ImageField` в лайтбоксе, позволяя просматривать изображения в полном разрешении. Изображения одного поля (`multiple=True`) группируются в одну галерею.

См. [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) — там приведено полностью работающее приложение, включая пользовательский валидатор MIME-типов.

### Без хранилища

Если `storage=` не прикреплён, поле передаёт загрузки вашему бэкенду в сыром виде вместо их сохранения:

* **В формах создания и редактирования** разобранное значение представляет собой кортеж `(UploadFile | list[UploadFile] | None, bool)`. Первый элемент — это сырой объект Starlette `UploadFile`, список, если `multiple=True`, или `None`, если пользователь ничего не выбрал. Второй элемент равен `True`, когда пользователь отмечает флажок удаления на форме редактирования, что означает желание удалить существующий файл без замены. Логика `create()` и `edit()` вашего бэкенда сохраняет загрузку и учитывает флаг удаления.
* **На страницах списка и деталей** поле ожидает, что значение предоставит три ключа — в виде `dict` — или три атрибута — в виде объекта: `url` (обязательный), цель ссылки; `filename`, отображаемую метку; и `content_type`, который выбирает иконку типа файла.

Этот контракт позволяет ORM-интеграциям ниже подключать собственную обработку файлов к тому же полю.

### Нативные файловые столбцы ORM

**MongoEngine** поддерживает `mongoengine.FileField` и `mongoengine.ImageField` из коробки, используя **GridFS** в качестве хранилища. Панель администрирования сама загружает файлы в GridFS, раздаёт их оттуда и удаляет. Конфигурация `storage=` не нужна: просто укажите поле по имени.

**SQLAlchemy** получает такую же поддержку через [sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/). Объявите его типы столбцов `FileField` или `ImageField` в своих моделях, и `starlette-admin` обнаружит их, отобразит соответствующее поле администрирования и зарегистрирует маршрут для раздачи сохранённых файлов. Хранилище настраивается через собственный `StorageManager` sqlalchemy-file, основанный на контейнерах Apache Libcloud, а загрузки присоединяются к транзакции сессии, поэтому откат сессии отменяет сохранение файла.

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


# Настройка хранилища sqlalchemy-file, независимая от BaseStorage в starlette-admin
os.makedirs("upload/avatars", exist_ok=True)
StorageManager.add_storage(
    "avatar", LocalStorageDriver("upload").get_container("avatars")
)


class AuthorView(ModelView):
    fields = ["id", "name", "avatar"]
```

См. [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file) — там приведено полноценное приложение с несколькими хранилищами, валидацией типов содержимого и полями с `multiple=True`.

## HasOne & HasMany

Поля связей, которые отображаются как элементы ввода `select2` и опираются на эндпоинт поиска связанного представления.

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

Параметр `key` указывает на соответствующий `ModelView`. Зарегистрируйте оба представления на одном экземпляре `Admin`, чтобы ключи разрешались.

---

## Что дальше

* [Фильтры](filters.md): настройка конструктора фильтров на страницах списка.
* [Файловое хранилище](file-storage.md): настройка бэкендов хранилища для `FileField` и `ImageField`.
* [Пользовательские поля](../advanced/custom-fields.md): создание пользовательского поля.
