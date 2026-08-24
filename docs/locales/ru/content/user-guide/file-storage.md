---
title: Файловое хранилище
description: Управление загрузкой файлов и изображений в starlette-admin с помощью
  LocalStorage или S3-совместимого backend-хранилища.
source_hash: 6f3d18d6107bfa818c48507b0807fb14bf6fcbe8825d9e5c824ed02e0ff2dd5c
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/file-storage/)
<!-- translation-notice:end -->

# Файловое хранилище

`FileField` и `ImageField` сохраняют загруженные файлы через storage backend, который вы задаёте с помощью параметра `storage` поля.

Создайте storage backend один раз и используйте его повторно во всех полях, которые хранят файлы в одном и том же месте.


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

Когда пользователь загружает обложку через админку, она:

* сохраняет файл в `uploads/covers/`
* записывает JSON-объект метаданных в столбец `cover`

База данных никогда не хранит сам файл, путь к нему в файловой системе или бинарные данные.


## Что записывается в базу данных

Админка представляет загруженный файл как сериализованный объект [`FileInfo`](../api/storage.md#starlette_admin.storage.base.FileInfo) в поле модели.

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
* `content_type`: MIME-тип, определённый в момент загрузки
* `size`: размер файла в байтах
* `storage`: зарегистрированное имя backend'а, по которому определяется расположение файла для генерации URL и удаления
* `key`: путь относительно хранилища или ключ объекта
* `url`: кэшированный публичный URL

`LocalStorage` сохраняет пустое значение `url`, поскольку URL зависит от текущего запроса. `S3Storage` сохраняет публичный или presigned URL в зависимости от вашей конфигурации.

Независимо от backend'а, `FileField` заново генерирует URL при отрисовке с помощью `storage.url()`, а не доверяет сохранённому значению.

`ImageField` дополнительно добавляет `width` и `height`.

Админка очищает каждое имя файла с помощью `secure_filename` перед сохранением: она удаляет компоненты пути и заменяет символы вне диапазона `[A-Za-z0-9_.-]` на `_`. Подробнее см. раздел [Безопасность](security.md).


## Storage backends

### Локальное хранилище

```python
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads", name="local")
```

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `base_dir` | `str | Path` | обязательный | Корневой каталог для хранения файлов. Создаётся автоматически, если не существует. |
| `name` | `str | None` | `"local"` | Имя в реестре, идентифицирующее backend. Должно быть уникальным при использовании нескольких экземпляров. |

Админка отдаёт файлы через этот маршрут:

```
/_files/{storage}/{path}
```

Дополнительная настройка статических файлов не требуется.

`LocalStorage.url()` формирует URL на основе контекста текущего запроса, поэтому сохранённое поле `url` остаётся пустым и вычисляется по мере необходимости.

!!! note
    Пример кода см. в [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage).

### Amazon S3 storage

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
| `prefix` | `str` | `"uploads/"` | Префикс ключа, применяемый ко всем сохраняемым объектам. |
| `region` | `str` | `"us-east-1"` | Регион AWS, используемый для подписи запросов и генерации URL. |
| `access_key` и `secret_key` | `str | None` | `None` | Необязательные учётные данные. При отсутствии используется стандартная цепочка учётных данных AWS. |
| `public` | `bool` | `True` | Если `True`, возвращается публичный URL. Если `False`, генерируются presigned URL. |
| `expires` | `int` | `3600` | Время жизни presigned URL в секундах. |
| `endpoint_url` | `str | None` | `None` | Кастомный S3-совместимый endpoint, например MinIO, R2 или B2. |
| `name` | `str | None` | `"s3"` | Имя в реестре, идентифицирующее backend. |

Если указан `endpoint_url`, админка строит URL в формате:

```
{endpoint_url}/{bucket}/{key}
```

вместо виртуального хостинга AWS (virtual-hosted style).


!!! important
    Поля файлов должны быть сопоставлены со столбцом базы данных, поддерживающим JSON. База данных хранит только метаданные, а сам файл — storage backend.


## Несколько файлов (`multiple=True`)

Установите `multiple=True` для `FileField` или `ImageField`, чтобы принимать несколько загрузок в одном поле.

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

В базе данных сохраняется JSON-список объектов `FileInfo`, и админка обрабатывает каждый файл независимо — сначала валидацию, затем сохранение.


!!! warning
    Сохранение формы полностью заменяет весь список файлов на отправленные. Добавить или удалить отдельный файл невозможно. Для управления жизненным циклом каждого файла используйте inline-модель со своим `FileField`.

!!! important
    `ListField(FileField(...))` не поддерживается. Используйте `multiple=True` для простых коллекций, а inline-модели — для структурированных данных о файлах.

## Валидация

Валидация выполняется в следующем порядке:

1. `accept`
2. `max_size`
3. пользовательские `validators`

Пользовательский валидатор — это вызываемый объект, который получает запрос, поле, объект `UploadFile` и все значения отправленной формы. Он должен вернуть `None` или выбросить исключение `ValueError`.

В следующем примере проверяется фактическое содержимое файла с помощью библиотеки `filetype`:

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
    Всегда сбрасывайте указатель файла с помощью `seek(0)` до и после проверки содержимого, чтобы слой хранения мог прочитать файл целиком.

!!! note
    Валидаторы выполняются для каждого файла отдельно, поэтому при `multiple=True` каждый файл проверяется независимо. `ImageField` применяет собственную проверку изображений до любого пользовательского валидатора.


!!! tip "Рекомендации"
    Используйте `accept` и `max_size` для быстрой базовой проверки.

    Используйте пользовательские валидаторы, когда нужно проверить содержимое файла или применить специфичные для приложения правила.

    Не полагайтесь на расширения файлов или заголовки `Content-Type` при проверках, критичных для безопасности. Вместо этого проверяйте содержимое с помощью библиотеки вроде `filetype` или `python-magic`.


## Ограничения очистки файлов

`starlette-admin` загружает файлы в storage backend и записывает метаданные `FileInfo` в базу данных, но не удаляет файлы после сбоя или удаления записи. Из этого следуют два поведения:

* **Неудачные транзакции:** если транзакция базы данных откатывается после завершения загрузки, файл остаётся в storage backend. У операций записи в хранилище нет механизма отката.
* **Удаление и обновление:** удаление строки или замена файла удаляет ссылку `FileInfo` из базы данных, однако старый файл остаётся в `LocalStorage` или `S3Storage`.

Такая архитектура упрощает слой хранения и предотвращает запуск деструктивных операций из-за ошибок уровня приложения. Обратная сторона — накопление «осиротевших» файлов. Чтобы хранилище не росло бесконтрольно, сверьте их самостоятельно. Распространённый подход — периодическая фоновая задача, которая сравнивает ключи в storage backend с активными ссылками `FileInfo` в вашей базе данных.

### Транзакционная альтернатива

Если вашему приложению нужны транзакционные операции с файловым хранилищем, согласованные с записями в базу данных, используйте библиотеку, связывающую файловое хранилище с unit of work в SQLAlchemy.

Вместо параметра `storage=` поля используйте [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file). Она сохраняет файлы как часть цикла flush и rollback ORM, поэтому неудачная транзакция или удаление строки отменяет соответствующую запись файла. Рабочий пример см. в [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file).

---

## Что дальше

* **[Поля](fields.md):** справочник по `FileField` и `ImageField`.
* **[Экспорт и импорт](export-import.md):** как файлы включаются в экспортируемые пакеты.
* **[Безопасность](security.md):** автоматическая очистка имён файлов и поведение валидации.
