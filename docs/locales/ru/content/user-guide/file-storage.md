---
title: Файловое хранилище
description: Управляйте загрузкой файлов и изображений в starlette-admin с помощью
  LocalStorage или S3-совместимого бэкенда хранилища.
source_hash: 6f3d18d6107bfa818c48507b0807fb14bf6fcbe8825d9e5c824ed02e0ff2dd5c
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/file-storage/)
<!-- translation-notice:end -->

# Файловое хранилище

`FileField` и `ImageField` сохраняют загруженные файлы через бэкенд хранилища, который вы задаёте параметром `storage` поля.

Создайте бэкенд хранилища один раз и используйте его повторно во всех полях, которые хранят файлы в одном и том же месте.


## Минимальный пример

```python hl_lines="8 12 31"
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import JSON, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///admin.sqlite")

local = LocalStorage(base_dir="uploads", name="local")


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    cover: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class BookView(ModelView):
    fields = [
        "id",
        "title",
        ImageField("cover", storage=local, upload_folder="covers"),
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Bookstore", secret_key="change-me")
admin.add_view(BookView(Book))
admin.mount_to(app)
```

Когда пользователь загружает обложку через панель администрирования, панель:

* сохраняет файл в `uploads/covers/`
* записывает JSON-объект с метаданными в столбец `cover`

База данных никогда не хранит сам файл, путь к нему в файловой системе или двоичные данные.


## Что записывается в базу данных

Панель администрирования представляет загруженный файл как сериализованный объект [`FileInfo`](../api/storage.md#starlette_admin.storage.base.FileInfo) в поле модели.

```json
{
  "filename": "product-photo.jpg",
  "content_type": "image/jpeg",
  "size": 204800,
  "storage": "s3",
  "key": "uploads/products/a1b2c3_product-photo.jpg",
  "url": "https://..."
}
```

* `filename`: очищенное исходное имя файла, используется для отображения
* `content_type`: MIME-тип, определённый при загрузке
* `size`: размер файла в байтах
* `storage`: зарегистрированное имя бэкенда, по которому определяется расположение файла для генерации URL и удаления
* `key`: путь относительно хранилища или ключ объекта
* `url`: кэшированный публичный URL

`LocalStorage` сохраняет пустое значение `url`, потому что URL зависят от текущего запроса. `S3Storage` сохраняет публичный или подписанный URL — в зависимости от вашей конфигурации.

Независимо от бэкенда, `FileField` заново генерирует URL во время отображения с помощью `storage.url()`, а не доверяет сохранённому значению.

`ImageField` дополнительно добавляет `width` и `height`.

Перед сохранением панель администрирования очищает каждое имя файла с помощью `secure_filename`: она удаляет компоненты пути и заменяет символы вне диапазона `[A-Za-z0-9_.-]` на `_`. Подробнее см. [Безопасность](security.md).


## Бэкенды хранилища

### Локальное хранилище

```python
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads", name="local")
```

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `base_dir` | `str | Path` | обязательный | Корневой каталог для хранения файлов. Создаётся автоматически, если не существует. |
| `name` | `str | None` | `"local"` | Имя в реестре, идентифицирующее бэкенд. Должно быть уникальным при использовании нескольких экземпляров. |

Панель администрирования отдаёт файлы через этот маршрут:

```
/_files/{storage}/{path}
```

Дополнительная настройка статических файлов не требуется.

`LocalStorage.url()` строит URL на основе контекста текущего запроса, поэтому сохранённое поле `url` остаётся пустым и вычисляется по мере необходимости.

!!! note
    Пример кода см. в [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage).

### Хранилище Amazon S3

```python
from starlette_admin.storage import S3Storage

s3 = S3Storage(
    bucket="my-bucket",
    prefix="admin/",
    region="eu-west-1",
    public=False,
)
```

Установите необязательные зависимости:

```bash
pip install starlette-admin[s3]
```

Это установит пакет `aiobotocore`.

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `bucket` | `str` | обязательный | Имя S3-бакета. |
| `prefix` | `str` | `"uploads/"` | Префикс ключа, применяемый к каждому сохраняемому объекту. |
| `region` | `str` | `"us-east-1"` | Регион AWS, используемый для подписи запросов и генерации URL. |
| `access_key` и `secret_key` | `str | None` | `None` | Необязательные учётные данные. При отсутствии используется стандартная цепочка учётных данных AWS. |
| `public` | `bool` | `True` | Если `True`, возвращается публичный URL. Если `False`, генерируются подписанные (presigned) URL. |
| `expires` | `int` | `3600` | Срок действия подписанных URL в секундах. |
| `endpoint_url` | `str | None` | `None` | Собственный S3-совместимый эндпоинт, например MinIO, R2 или B2. |
| `name` | `str | None` | `"s3"` | Имя в реестре, идентифицирующее бэкенд. |

Если вы указали `endpoint_url`, панель администрирования строит URL как:

```
{endpoint_url}/{bucket}/{key}
```

вместо виртуального формата AWS (virtual-hosted style).


!!! important
    Поля файлов должны соответствовать столбцу базы данных с поддержкой JSON. В базе данных хранятся только метаданные, а сам файл — в бэкенде хранилища.


## Несколько файлов (`multiple=True`)

Установите `multiple=True` у `FileField` или `ImageField`, чтобы принимать несколько загрузок в одном поле.

```python
from starlette_admin import FileField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/attachments", name="attachments")


class TicketView(ModelView):
    fields = [
        "id",
        "subject",
        FileField(
            "attachments",
            storage=local,
            upload_folder="tickets/",
            multiple=True,
        ),
    ]
```

В базе данных сохраняется JSON-список объектов `FileInfo`, и панель администрирования обрабатывает каждый файл независимо — через валидацию и сохранение.


!!! warning
    Сохранение формы полностью заменяет список файлов на отправленные файлы. Добавить или удалить один файл невозможно. Для управления жизненным циклом каждого файла используйте инлайн-модель со своим `FileField`.

!!! important
    `ListField(FileField(...))` не поддерживается. Используйте `multiple=True` для простых коллекций, а инлайн-модели — для структурированных данных о файлах.

## Валидация

Валидация выполняется в следующем порядке:

1. `accept`
2. `max_size`
3. пользовательские `validators`

Пользовательский валидатор — это вызываемый объект, который получает запрос, поле, объект `UploadFile` и все отправленные значения формы. Он должен вернуть `None` или вызвать исключение `ValueError`.

Следующий пример проверяет фактическое содержимое файла с помощью библиотеки `filetype`:

```python
import filetype
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette_admin.fields import BaseField

ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_document_type(
    request: Request, field: BaseField, upload: UploadFile, form_values: dict
) -> None:
    upload.file.seek(0)
    try:
        header = upload.file.read(2048)
        kind = filetype.guess(header)
        detected = kind.mime if kind else "application/octet-stream"
    finally:
        upload.file.seek(0)

    if detected not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise ValueError(
            f"Invalid file type '{detected}'. Only PDF, DOC, and DOCX are allowed."
        )
```

!!! important "Сбросьте указатель файла"
    Всегда сбрасывайте указатель файла с помощью `seek(0)` до и после проверки содержимого, чтобы слой хранилища мог прочитать файл целиком.

!!! note
    Валидаторы выполняются для каждого файла отдельно, поэтому при `multiple=True` каждый файл проходит валидацию независимо. `ImageField` применяет собственную проверку изображений до любого пользовательского валидатора.


!!! tip "Рекомендации"
    Используйте `accept` и `max_size` для лёгкой проверки.

    Используйте пользовательские валидаторы, когда нужно проверить содержимое файла или применить правила, специфичные для приложения.

    Не полагайтесь на расширения файлов или заголовки `Content-Type` при проверках, критичных для безопасности. Вместо этого проверяйте содержимое с помощью библиотеки вроде `filetype` или `python-magic`.


## Ограничения очистки файлов

`starlette-admin` загружает файлы в бэкенд хранилища и записывает метаданные `FileInfo` в базу данных, но не удаляет файлы после сбоя или удаления. Из этого следуют два поведения:

* **Неудачные транзакции:** если транзакция базы данных откатывается после завершения загрузки, файл остаётся в бэкенде хранилища. У записи в хранилище нет механизма отката.
* **Удаления и обновления:** удаление строки или замена файла удаляет ссылку `FileInfo` из базы данных, но старый файл остаётся в `LocalStorage` или `S3Storage`.

Такая архитектура упрощает слой хранилища и не позволяет ошибкам уровня приложения запускать разрушительные операции. Обратная сторона — накопление «осиротевших» файлов. Чтобы хранилище не росло бесконтрольно, выполняйте их сверку самостоятельно. Распространённый подход — периодическая фоновая задача, которая сравнивает ключи в бэкенде хранилища с активными ссылками `FileInfo` в базе данных.

### Транзакционная альтернатива

Если вашему приложению нужны транзакционные операции с файловым хранилищем, согласованные с записью в базу данных, используйте библиотеку, связывающую файловое хранилище с unit of work в SQLAlchemy.

Вместо параметра `storage=` у поля используйте [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file). Она сохраняет файлы как часть цикла flush и rollback ORM, поэтому неудачная транзакция или удаление строки отменяют соответствующую запись файла. Рабочий пример см. в [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file).

---

## Что дальше

* **[Поля](fields.md):** справочник по `FileField` и `ImageField`.
* **[Экспорт и импорт](export-import.md):** как файлы включаются в экспортные пакеты.
* **[Безопасность](security.md):** автоматическая очистка имён файлов и поведение валидации.
