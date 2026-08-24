---
title: Экспорт и импорт
description: Включите экспорт в CSV, JSON и PDF и массовый импорт данных с валидацией
  в starlette-admin.
source_hash: 90cb474355c091c80bb8d0e65e3b1aefa9a94e31738fb71b4e28e71590b29ce1
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Машинный перевод под контролем человека"

    Этот контент переведён с помощью машинной генерации, направляемой
    составленными людьми глоссариями и руководствами по стилю. Поскольку
    текст не проверяется вручную построчно, возможны отдельные ошибки или
    неестественные формулировки.

    В случае любых расхождений авторитетным источником считается
    оригинальная версия на английском языке.

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/export-import/)
<!-- translation-notice:end -->

# Экспорт и импорт

Каждая страница списка позволяет пользователям выгружать данные в файл и загружать данные из файла, поэтому вам не нужно писать собственные маршруты.

## Обзор

* **Экспорт:** пользователь нажимает кнопку на панели инструментов, затем задаёт область, поля, формат и имя файла.
* **Импорт:** пользователь нажимает кнопку на панели инструментов, чтобы открыть мастер из трёх шагов: загрузка, предпросмотр и результаты.
* **Форматы:** CSV, JSON, XLSX, ODS, YAML, PDF и пользовательские форматы поддерживаются «из коробки».
* **Upsert:** импорт может дополнительно обновлять существующие записи, найденные по первичному ключу.
* **Интеграция:** обе функции работают с фильтрацией, сортировкой, выбором строк и полями с файловым хранилищем.
* **Без дополнительных endpoint'ов:** всё поставляется вместе с view.

## Минимальный пример

```python hl_lines="23 24"
from sqlalchemy import Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///store.sqlite")

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column()

class ProductView(ModelView):
    fields = ["id", "name", "description", "price"]
    exporters = ["csv", "xlsx", "json"]
    importers = ["csv", "xlsx"]

Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))

```

Теперь `ProductView` показывает кнопку **Экспорт** и кнопку **Импорт** на панели инструментов списка. Каждый диалог предлагает ровно те форматы, которые вы указали в `exporters` и `importers`.

---

## Включение экспорта

Атрибут `exporters` содержит список форматов в виде простых строк с расширениями:

```python hl_lines="2"
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]

```

По умолчанию используется `["csv", "json"]`. Таблица ниже перечисляет все встроенные форматы и пакеты, которые им требуются. Форматам `csv`, `tsv` и `json` дополнительные зависимости не нужны. Все остальные табличные форматы используют `tablib`, а `pdf` — `reportlab`. Неизвестная строка формата или формат, пакет которого не установлен, вызывает ошибку при запуске.

| Формат | Что нужно установить |
| --- | --- |
| `csv`, `tsv`, `json` | Входит в ядро |
| `xlsx` | `pip install tablib[xlsx]` |
| `xls` | `pip install tablib[xls]` |
| `ods` | `pip install tablib[ods]` |
| `yaml` | `pip install tablib[yaml]` |
| `dbf`, `html`, `latex`, `jira`, `rst` | `pip install tablib` |
| `pdf` | `pip install starlette-admin[pdf]` |

### Переопределение параметров формата

Каждая строка формата соответствует заранее настроенному экземпляру exporter'а с разумными значениями по умолчанию. Если формату нужны другие настройки, передайте вместо строки экземпляр exporter'а. В одном списке можно смешивать строки и экземпляры:

```python hl_lines="5"
from starlette_admin.export import CsvExporter

class ProductView(ModelView):
    exporters = [CsvExporter(delimiter=";"), "xlsx", "json"]

```

`CsvExporter` передаёт именованные аргументы в `csv.writer` и принимает параметр `escape_formulas`. `TablibExporter(format, **kwargs)` покрывает все форматы tablib и передаёт именованные аргументы в `tablib.Dataset.export()`.

!!! warning
    Экранирование формул по умолчанию отключено. Если экспортируемые поля могут содержать строки, введённые пользователем, установите `escape_formulas=True` у `CsvExporter`, `TsvExporter` или `TablibExporter`, чтобы предотвратить инъекцию формул при открытии файла в табличном редакторе. Подробнее см. [Инъекция формул](security.md#formula-injection).

Экспорт включён по умолчанию. Кнопка **Экспорт** появляется на панели инструментов всякий раз, когда список `exporters` не пуст. Чтобы ограничить круг тех, кто может выполнять экспорт, переопределите метод `can_export(request)`:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### Диалог экспорта

Экспорт — это встроенное глобальное действие. При выборе пункта **Экспорт** открывается диалог, в котором пользователь настраивает экспорт перед скачиванием.

* **Область:** что экспортировать. Доступны варианты «Выбранные строки» (по умолчанию, когда отмечены строки), «Все подходящие строки» (доступен из баннера выбора всех строк) и «Текущая страница» (по умолчанию, когда ничего не выбрано).
* **Поля:** по одному чекбоксу на каждое экспортируемое поле. Снятие чекбокса убирает соответствующий столбец. Поля с атрибутом `exclude_from_export=True` здесь никогда не отображаются.
* **Формат:** по одному пункту для каждого формата из `exporters`.
* **Имя файла:** по умолчанию используется ключ view. Сервер добавляет расширение файла.

Любая область учитывает текущий поиск, фильтры и порядок сортировки страницы списка, поэтому пользователь экспортирует именно то, что видит.

### Ограничение количества строк

```python
from starlette_admin.export import ExportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    export_config=ExportConfig(max_rows=50_000),
)

```

Значение `ExportConfig.max_rows` по умолчанию равно 100 000. Ограничение применяется к количеству строк, которое фактически выдаст выбранная область, и admin проверяет это количество до загрузки какой-либо строки. Когда количество превышает лимит, admin выводит сообщение об ошибке и перенаправляет обратно на страницу списка вместо генерации файла. Это защищает от зависания запроса при широком нефильтрованном экспорте большой таблицы. Установите `max_rows=None`, чтобы снять ограничение.

---

## Включение импорта

Атрибут `importers` работает точно так же, как `exporters`, и принимает строки форматов:

```python hl_lines="2"
class ProductView(ModelView):
    importers = ["csv", "xlsx"]

```

Встроенные форматы импорта — `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` и `html` — требуют те же зависимости, что и их аналоги для экспорта. Чтобы переопределить параметры формата по умолчанию, передайте экземпляр importer'а, например `CsvImporter(delimiter=";")` из `starlette_admin.importers`.

Импорт включён по умолчанию со значением `["csv", "json"]`. Кнопка **Импорт** появляется на панели инструментов всякий раз, когда список `importers` не пуст. Чтобы ограничить круг тех, кто может выполнять импорт, переопределите метод `can_import(request)`:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### Мастер импорта

При выборе пункта **Импорт** открывается мастер из трёх шагов. Ничего не записывается в базу данных до финального подтверждения, и файл не хранится на сервере между шагами: браузер удерживает файл и повторно отправляет его на каждом шаге.

1. **Загрузка:** выберите формат, укажите файл и при необходимости отметьте пункт **Обновлять существующие записи по первичному ключу**. Если этот пункт выбран, строка, первичный ключ которой совпадает с существующей записью, обновит эту запись вместо создания новой. Иначе каждая строка создаётся заново.
2. **Предпросмотр:** отправка формы загрузки запускает полную проверку без записи каких-либо данных. Мастер показывает сводку, сопоставление столбцов, образцы строк и подробную таблицу ошибок.
3. **Результат:** мастер фиксирует импорт и сообщает итоговые количества созданных, обновлённых и пропущенных записей. Строки, не прошедшие валидацию на этапе предпросмотра, пропускаются.

!!! tip
    Чтобы позволить backend'у генерировать первичные ключи, снимите столбец первичного ключа в сопоставлении предпросмотра. Тогда импортируемые строки не будут содержать значение ключа, и повторный импорт ранее экспортированного файла создаст новые записи вместо ошибки из-за устаревших ID.

### Ограничения загрузки и количества строк

```python
from starlette_admin.importers import ImportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    import_config=ImportConfig(max_rows=50_000),
)
```

Endpoint импорта зеркально повторяет ограничение количества строк экспорта. Значение `ImportConfig.max_rows` по умолчанию равно 100 000 и применяется до создания какой-либо записи. Admin подсчитывает строки загруженного файла на предварительном проходе и отклоняет файл с количеством строк больше лимита ошибкой HTTP 400. Установите `max_rows=None`, чтобы снять ограничение. Параметр `ImportConfig.max_upload_size` также ограничивает размер загрузки 10 МБ по умолчанию.

### Сопоставление заголовков

Мастер сопоставляет каждый заголовок файла сначала с `label` вашего поля, затем с его `name`. Файл со столбцом `Name` и файл со столбцом `name` оба сопоставляются с полем с именем `name`. Несопоставленные столбцы игнорируются, а поля без соответствующего столбца получают значение `None`.

## Файловые поля

View с полем `FileField` или `ImageField`, привязанным к хранилищу, экспортируется как ZIP-архив, чтобы содержимое файлов перемещалось вместе с данными строк:

```python
from sqlalchemy import Integer, JSON, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///catalog.sqlite")
covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    photo: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class ProductView(ModelView):
    fields = [
        "id",
        "name",
        ImageField("photo", storage=covers_storage, upload_folder="products"),
    ]

Base.metadata.create_all(engine)
admin = Admin(engine, title="Catalog Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

Экспорт `ProductView` в CSV создаёт архив `export.zip` следующей структуры:

```text
export.zip
├── export.csv              ← photo column holds "assets/covers/products/a1b2_photo.jpg"
└── assets/
    └── covers/
        └── products/
            └── a1b2_photo.jpg


```

Столбец `photo` в `export.csv` содержит путь к файлу относительно ZIP-архива, `assets/<storage-name>/<key>`, благодаря чему CSV остаётся читаемым в табличном редакторе. Admin извлекает каждый упомянутый файл из его storage backend и упаковывает его в каталоге `assets/`.

Импорт не принимает ZIP-архивы. `FileField` и `ImageField` всегда исключаются из импорта, поскольку по умолчанию имеют атрибут `exclude_from_import=True`, поэтому мастер игнорирует столбец `photo` при загрузке. Повторно импортируйте обычный файл с данными, а затем прикрепите файлы через формы создания или редактирования.


## Написание собственного exporter'а

Чтобы написать собственный exporter, создайте подкласс `BaseExporter` и реализуйте метод `generate`. Базовый класс берёт на себя обёртку в ZIP, скачивание файлов и заголовки ответа:

```python
from typing import Any
from starlette_admin.export import BaseExporter
from starlette_admin.fields import BaseField

class MarkdownExporter(BaseExporter):
    content_type = "text/markdown"
    extension = "md"

    async def generate(
        self, fields: list[BaseField], rows: list[dict[str, Any]]
    ) -> bytes:
        lines = [
            " | ".join(f.label or f.name for f in fields),
            " | ".join("---" for _ in fields),
        ]
        for row in rows:
            lines.append(" | ".join(str(row.get(f.name, "")) for f in fields))
        return "\n".join(lines).encode("utf-8")
```

Данные `rows` приходят уже очищенными: admin сначала заменяет каждое значение `FileField` и `ImageField` строкой пути относительно ZIP-архива, поэтому ваш метод `generate` никогда не работает со словарями файлов. Зарегистрируйте `MarkdownExporter()` в списке `exporters`, чтобы он появился в выпадающем списке форматов.

## Написание собственного importer'а

Чтобы написать собственный importer, создайте подкласс `BaseImporter` и реализуйте `parse` как async generator, возвращающий по одному словарю на каждую строку:

```python
import json
from collections.abc import AsyncGenerator
from typing import Any
from starlette_admin.importers import BaseImporter, ImportContext

class NdjsonImporter(BaseImporter):
    extension = "ndjson"

    async def parse(self, ctx: ImportContext) -> AsyncGenerator[dict[str, Any], None]:
        for line in ctx.content.decode("utf-8").splitlines():
            if line.strip():
                yield json.loads(line)
```

---

## Что дальше

* **[File Storage](file-storage.md):** настройте storage backend'и, упоминаемые в ZIP-архиве экспорта.
* **[Security](security.md):** ограничения количества строк экспорта и размера загрузки импорта.
* **[Actions](actions.md):** добавьте массовые действия и действия над строками вместе с экспортом и импортом.
