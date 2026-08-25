---
title: Развёртывание
description: Лучшие практики безопасного и эффективного развёртывания приложения FastAPI
  и starlette-admin в production-окружении.
source_hash: def246bd4a7147614b7e4c4d87700c12e6e3d520c2d13ef9f06250aec691f355
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/deployment/)
<!-- translation-notice:end -->

# Развёртывание

Работа панели администрирования за reverse proxy меняет два момента, которые в локальной разработке можно игнорировать: секретный ключ должен быть одинаковым во всех worker-процессах, а генерируемые URL должны отражать HTTPS, даже если ваше приложение получает от прокси только обычный HTTP.

!!! note "Руководства по развёртыванию для конкретных framework"
    На этой странице описано только то, что специфично для `Admin`. О базовом приложении и ASGI-сервере читайте здесь:

    * **FastAPI:** [Документация по развёртыванию FastAPI](https://fastapi.tiangolo.com/deployment/)
    * **Uvicorn:** [Документация по развёртыванию Uvicorn](https://www.uvicorn.org/deployment/)

```python
import os

from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Post

engine = create_engine(os.environ["DATABASE_URL"])
app = Starlette()

admin = Admin(
    engine,
    title="My Admin",
    base_url="/admin",
    secret_key=os.environ["ADMIN_SECRET_KEY"],
)
admin.add_view(ModelView(Post))
admin.mount_to(app)
```

```shell title="Запуск за reverse proxy"
uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
```

## Секретный ключ

Если не передать `secret_key` явно, `Admin` сгенерирует случайный ключ при запуске. Для одного локального процесса это допустимо, но каждый worker-процесс генерирует собственный ключ независимо, поэтому CSRF-токен, подписанный одним worker'ом, не пройдёт проверку на другом. Устанавливайте `secret_key` из переменной окружения до того, как запустите более одного процесса. Полное описание проблемы при работе с несколькими worker'ами и о том, как используется ключ, см. в разделе [Безопасность](../user-guide/security.md).

## Reverse proxy и HTTPS

`Admin` строит все внутренние ссылки (страницы списков, формы редактирования, экспорт, монтирование `/static`, загруженные файлы, отдаваемые через `/_files/...`) вызовом `request.url_for(...)`, который определяет схему по входящему запросу. Когда прокси — например Nginx, Caddy или Traefik — терминирует TLS и пересылает приложению обычный HTTP, Starlette не может узнать, что исходный запрос был HTTPS, если только прокси не отправляет `X-Forwarded-Proto`, а ваш ASGI-сервер ему доверяет. Если оставить это ненастроенным, сгенерированные ссылки получат схему `http://`, которую браузеры блокируют или перезаписывают, когда сама страница загружена по HTTPS.

Исправить это нужно в двух местах:

1. **Прокси** пересылает заголовок:

    ```nginx title="nginx"
    location /admin/ {
        proxy_pass http://127.0.0.1:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    ```

2. **Uvicorn** доверяет ему: через `--proxy-headers` вместе с `--forwarded-allow-ips`, где указывается IP прокси (или `'*'`, если прокси доступен только из вашей внутренней сети):

    ```shell
    uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
    ```

Gunicorn-воркер `uvicorn.workers.UvicornWorker` читает те же две настройки из `--forwarded-allow-ips`. Полный набор опций для менеджеров процессов см. в [документации по развёртыванию Uvicorn](https://www.uvicorn.org/deployment/).

!!! warning
    Значение `--forwarded-allow-ips='*'` означает доверие пересылаемым заголовкам из **любого** источника. Используйте его только тогда, когда приложение недоступно иначе как через ваш прокси — например, когда оно привязано к частной сети или Unix-сокету. Если приложение доступно напрямую, ограничьте настройку фактическим IP прокси. Иначе клиент сможет подделать `X-Forwarded-Proto` и `X-Forwarded-For` напрямую.

## Статические ресурсы

CSS и JS панели администрирования поставляются внутри пакета `starlette_admin`, и `Admin` раздаёт их сам через монтирование `/static` под `base_url`, а не с отдельного статического хоста. Параметр `static_dir` позволяет лишь переопределить отдельные файлы (см. [Шаблоны](templates.md)), но не переносит раздачу ресурсов за пределы процесса вашего приложения. Встроенной возможности раздавать их с CDN нет. Если она вам нужна, добавьте на уровне прокси правило кэширования `Cache-Control` для `{base_url}/static/*`.

С загруженными файлами ситуация иная: `LocalStorage` тоже раздаёт их через приложение (`/_files/{storage}/{path}`, поэтому auth middleware продолжает действовать), а вот `S3Storage` и другие удалённые backend'и могут отдавать файлы напрямую от провайдера. См. [Файловое хранилище](../user-guide/file-storage.md).

---

## Что дальше

* **[Безопасность](../user-guide/security.md):** Подробно о проблеме `secret_key` при нескольких worker'ах, а также обо всём остальном, что покрывают и не покрывают встроенные механизмы защиты.
* **[Аутентификация](../user-guide/auth.md):** Ограничьте доступ к панели администрирования до того, как она станет доступна в production.
* **[Файловое хранилище](../user-guide/file-storage.md):** Настройка `S3Storage` и других удалённых backend'ов.
