---
title: Экспорт и импорт
description: Включите экспорт в CSV, JSON и PDF и массовый импорт данных с валидацией
  в starlette-admin.
source_hash: 90cb474355c091c80bb8d0e65e3b1aefa9a94e31738fb71b4e28e71590b29ce1
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/export-import/)
<!-- translation-notice:end -->

# Экспорт и импорт

На каждой странице списка пользователи могут экспортировать данные в файл и импортировать данные из файла, поэтому вам не нужно писать собственные маршруты.

## Обзор

* **Экспорт:** пользователи нажимают кнопку на панели инструментов, затем задают область, поля, формат и имя файла.
* **Импорт:** пользователи нажимают кнопку на панели инструментов, чтобы открыть мастер из трёх шагов: загрузка, предпросмотр и результаты.
* **Форматы:** CSV, JSON, XLSX, ODS, YAML, PDF и пользовательские форматы поддерживаются из коробки.
* **Upsert:** при импорте можно дополнительно обновлять существующие записи, найденные по первичному ключу.
* **Интеграция:** обе функции работают с фильтрацией, сортировкой, выбором строк и полями с файловым хранилищем.
* **Без дополнительных эндпоинтов:** всё уже входит в состав представления.

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

Теперь в `ProductView` на панели инструментов страницы списка появляются кнопки **Экспорт** и **Импорт**. Каждое диалоговое окно предлагает ровно те форматы, которые вы указали в `exporters` и `importers`.

---

## Включение экспорта

Атрибут `exporters` содержит список доступных форматов в виде строк с расширениями:

```python hl_lines="2"
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]

```

По умолчанию используется `["csv", "json"]`. В таблице ниже перечислены все встроенные форматы и пакеты, которые им требуются. Форматам `csv`, `tsv` и `json` дополнительные зависимости не нужны. Все остальные табличные форматы используют `tablib`, а `pdf` — `reportlab`. Неизвестная строка формата или формат, пакет которого не установлен, вызывают ошибку при запуске.

| Формат | Требуется установить |
| --- | --- |
| `csv`, `tsv`, `json` | Входит в ядро |
| `xlsx` | `pip install tablib[xlsx]` |
| `xls` | `pip install tablib[xls]` |
| `ods` | `pip install tablib[ods]` |
| `yaml` | `pip install tablib[yaml]` |
| `dbf`, `html`, `latex`, `jira`, `rst` | `pip install tablib` |
| `pdf` | `pip install starlette-admin[pdf]` |

### Переопределение параметров формата

Каждая строка формата соответствует заранее настроенному экземпляру экспортера с разумными значениями по умолчанию. Если формату нужны другие настройки, передайте вместо строки экземпляр экспортера. Строки и экземпляры можно смешивать в одном списке:

```python hl_lines="5"
from starlette_admin.export import CsvExporter

class ProductView(ModelView):
    exporters = [CsvExporter(delimiter=";"), "xlsx", "json"]

```

`CsvExporter` передаёт именованные аргументы в `csv.writer` и принимает параметр `escape_formulas`. `TablibExporter(format, **kwargs)` покрывает все форматы tablib и передаёт именованные аргументы в `tablib.Dataset.export()`.

!!! warning
    Экранирование формул по умолчанию отключено. Если экспортируемые поля могут содержать строки, введённые пользователями, установите `escape_formulas=True` у `CsvExporter`, `TsvExporter` или `TablibExporter`, чтобы предотвратить инъекцию формул при открытии файла в табличном редакторе. См. [Инъекция формул](security.md#formula-injection).

Экспорт включён по умолчанию. Кнопка **Экспорт** появляется на панели инструментов всегда, когда список `exporters` не пуст. Чтобы ограничить круг тех, кто может экспортировать данные, переопределите метод `can_export(request)`:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### Диалоговое окно экспорта

Экспорт — это встроенное глобальное действие. При нажатии кнопки **Экспорт** открывается диалоговое окно, где пользователь настраивает экспорт перед скачиванием.

* **Область:** что экспортировать. Доступны варианты «Выбранные строки» (по умолчанию, если отмечены строки), «Все подходящие строки» (доступен из баннера выбора всех строк) и «Текущая страница» (по умолчанию, если ничего не выбрано).
* **Поля:** по одному флажку на каждое экспортируемое поле. Снятие флажка убирает соответствующий столбец. Поля с флагом `exclude_from_export=True` здесь никогда не отображаются.
* **Формат:** по одному пункту для каждого формата из `exporters`.
* **Имя файла:** по умолчанию используется ключ представления. Сервер добавляет расширение файла.

Каждая область учитывает текущий поиск, фильтры и порядок сортировки страницы списка, поэтому пользователь экспортирует именно то, что видит.

### Ограничение на количество строк

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

По умолчанию `ExportConfig.max_rows` равен 100 000. Ограничение применяется к количеству строк, которое фактически выдаст выбранная область, и панель администрирования проверяет это количество до выборки какой-либо строки. Если количество превышает лимит, панель показывает флеш-сообщение об ошибке и перенаправляет обратно на страницу списка вместо генерации файла. Это защищает от зависания запроса при широком экспорте без фильтров из большой таблицы. Установите `max_rows=None`, чтобы снять ограничение.

---

## Включение импорта

Атрибут `importers` работает точно так же, как `exporters`, и принимает строки форматов:

```python hl_lines="2"
class ProductView(ModelView):
    importers = ["csv", "xlsx"]

```

Встроенные форматы импорта — `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` и `html` — требуют те же зависимости, что и их аналоги для экспорта. Чтобы переопределить параметры формата по умолчанию, передайте экземпляр импортера, например `CsvImporter(delimiter=";")` из `starlette_admin.importers`.

Импорт включён по умолчанию со значением `["csv", "json"]`. Кнопка **Импорт** появляется на панели инструментов всегда, когда список `importers` не пуст. Чтобы ограничить круг тех, кто может импортировать данные, переопределите метод `can_import(request)`:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### Мастер импорта

При нажатии кнопки **Импорт** открывается мастер из трёх шагов. До окончательного подтверждения в базу данных ничего не записывается, и между шагами файл не хранится на сервере: браузер удерживает файл и повторно отправляет его на каждом шаге.

1. **Загрузка:** выберите формат и файл, при необходимости отметьте флажок **Обновлять существующие записи по первичному ключу**. Если он отмечен, строка, первичный ключ которой совпадает с существующей записью, обновляет эту запись вместо создания новой. Иначе создаётся каждая строка.
2. **Предпросмотр:** отправка загрузки запускает полную проверку без записи каких-либо данных. Мастер показывает сводку, сопоставление столбцов, примеры строк и подробную таблицу ошибок.
3. **Результат:** мастер фиксирует импорт и сообщает итоговые количества созданных, обновлённых и пропущенных записей. Строки, не прошедшие валидацию на этапе предпросмотра, пропускаются.

!!! tip
    Чтобы позволить бэкенду генерировать первичные ключи, снимите сопоставление столбца первичного ключа на этапе предпросмотра. Тогда импортированные строки не будут содержать значения ключа, и повторный импорт ранее экспортированного файла создаст новые записи вместо ошибки из-за устаревших идентификаторов.

### Ограничения на загрузку и количество строк

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

Эндпоинт импорта зеркально повторяет ограничение на количество строк при экспорте. По умолчанию `ImportConfig.max_rows` равен 100 000 и применяется до создания какой-либо записи. Панель администрирования подсчитывает строки загруженного файла на предварительном проходе и отклоняет файл с количеством строк больше лимита ошибкой HTTP 400. Установите `max_rows=None`, чтобы снять ограничение. Кроме того, `ImportConfig.max_upload_size` по умолчанию ограничивает размер загрузки 10 МБ.

### Сопоставление заголовков

Мастер сначала сопоставляет каждый заголовок столбца файла с меткой (`label`) вашего поля, затем с его именем (`name`). Файл со столбцом `Name` и файл со столбцом `name` оба сопоставляются с полем `name`. Несопоставленные столбцы игнорируются, а поля без соответствующего столбца получают значение `None`.

## Файловые поля

Представление с полем `FileField` или `ImageField`, привязанным к хранилищу, экспортируется как ZIP-архив, поэтому содержимое файлов передаётся вместе с данными строк:

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

Столбец `photo` в `export.csv` содержит путь к файлу относительно ZIP-архива — `assets/<storage-name>/<key>`, — благодаря чему CSV остаётся читаемым в табличном редакторе. Панель администрирования извлекает каждый упомянутый файл из его бэкенда хранилища и упаковывает его в `assets/`.

Импорт не принимает ZIP-архивы. Поля `FileField` и `ImageField` всегда исключаются из импорта, поскольку по умолчанию у них установлен `exclude_from_import=True`, поэтому мастер игнорирует столбец `photo` при загрузке. Повторно импортируйте обычный файл с данными, а затем прикрепите файлы через формы создания или редактирования.


## Написание пользовательского экспортера

Чтобы написать пользовательский экспортер, создайте подкласс `BaseExporter` и реализуйте метод `generate`. Базовый класс обрабатывает упаковку в ZIP, скачивание файлов и заголовки ответа:

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

Данные в `rows` приходят предварительно очищенными: панель администрирования сначала заменяет каждое значение `FileField` и `ImageField` строкой пути относительно ZIP-архива, поэтому ваш метод `generate` никогда не работает со словарями файлов. Зарегистрируйте `MarkdownExporter()` в списке `exporters`, чтобы он появился в выпадающем списке форматов.

## Написание пользовательского импортера

Чтобы написать пользовательский импортер, создайте подкласс `BaseImporter` и реализуйте `parse` как асинхронный генератор, который выдаёт один словарь на каждую строку:

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

* **[Файловое хранилище](file-storage.md):** настройте бэкенды хранилища, на которые ссылается ZIP-архив экспорта.
* **[Безопасность](security.md):** ограничения на количество строк при экспорте и размер загрузки при импорте.
* **[Действия](actions.md):** добавьте групповые действия и действия над строками вместе с экспортом и импортом.
