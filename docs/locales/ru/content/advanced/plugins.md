---
title: Плагины
description: Упаковывайте переиспользуемые функции и расширения администрирования
  в виде подключаемых плагинов для starlette-admin.
source_hash: c9ecd9e51a7426d12b628b06c9c664579e5f269d456e93e9d985c4d2853ac758
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/plugins/)
<!-- translation-notice:end -->

# Плагины

Плагин — это Python-пакет, который расширяет `starlette-admin` через один аргумент конструктора. Плагин может объединять в себе любые комбинации полей, шаблонов, статических ресурсов, конвертеров моделей, фильтров, форматов импорта/экспорта, storage backend'ов, подписчиков событий, представлений, маршрутов, middleware, ресурсов темы и каталогов переводов.

## Использование плагина

Передавайте плагины через аргумент `plugins` при создании экземпляра `Admin`:

```python
from starlette_admin_geospatial import GeospatialPlugin
from starlette_admin.contrib.sqla import Admin

admin = Admin(engine, plugins=[GeospatialPlugin(default_zoom=13)])
```

Конструктор плагина принимает опции, а список передаётся напрямую в `Admin`. Больше ничего настраивать или регистрировать не нужно. Опции передаются от конструктора вниз по цепочке: в Python backend, шаблоны Jinja и frontend JavaScript.

## Создание плагина

Чтобы написать плагин, начните с официального cookiecutter-шаблона. Он генерирует готовый к публикации пакет с правильной структурой каталогов и конфигурацией.

### Предварительные требования

Установите `cookiecutter` с помощью вашего пакетного менеджера. Подробности см. в [официальном руководстве по установке](https://cookiecutter.readthedocs.io/en/stable/README.html#installation):

```bash
pip install cookiecutter
```

### Скаффолдинг

Запустите cookiecutter-шаблон из любого каталога:

```bash
cookiecutter gh:jowilf/starlette-admin --directory plugins/cookiecutter-starlette-admin-plugin
```

Шаблон запросит у вас имя плагина, slug пакета, версию и несколько других переменных. По завершении вы получите самодостаточный пакет со следующим содержимым:

* Каталог `src/`, в котором находятся класс вашего плагина и поля.
* Правильно именованные каталоги `templates/`, `static/` и `translations/`.
* Полный набор тестов.
* Запускаемое примерное приложение.

## API плагина

В основе каждого плагина лежит подкласс `BasePlugin` (`starlette_admin.plugins.BasePlugin`), который предоставляет hook'и для регистрации ваших функций во время инициализации `Admin`.

```python
from starlette_admin.plugins import BasePlugin


class MyPlugin(BasePlugin):
    name = "my-plugin"
```

Атрибут `name` — это уникальный идентификатор в kebab-case, который одновременно служит пространством имён для ваших шаблонов и статических ресурсов. Каждый шаблон и каждый статический файл, поставляемые вашим плагином, должны находиться внутри `plugins/<name>/`.

### Каталоги ресурсов

Плагин может содержать ровно три каталога в корне своего пакета. Регистрировать их не нужно, поскольку admin находит их по соглашению:

* `templates/`: шаблоны Jinja, которые должны располагаться внутри `templates/plugins/<name>/`.
* `static/`: статические ресурсы, такие как CSS- и JS-файлы, которые должны располагаться внутри `static/plugins/<name>/`.
* `translations/`: каталоги переводов Babel.

Соблюдение пространства имён `plugins/<name>/` защищает ваши ресурсы от конфликтов с файлами ядра или другими плагинами, оставляя их переопределяемыми через собственные `templates_dir` или `static_dir` пользователя.

### Декларативные hook'и

Переопределяйте декларативные hook'и, чтобы добавлять ресурсы, регистрировать представления или монтировать маршруты.

* `css_links(self, request: Request) -> Sequence[str]`: добавляет таблицы стилей в макет каждой страницы admin.
* `js_links(self, request: Request) -> Sequence[str]`: добавляет скрипты в макет каждой страницы admin.
* `views(self) -> Sequence[BaseView]`: возвращает представления для регистрации в боковой панели admin. Верните `DropDown`, чтобы сгруппировать их.
* `routes(self) -> Sequence[Route | Mount]`: возвращает endpoint'ы без интерфейса, монтируемые по пути `/plugins/<name>/` — это удобно для webhook'ов и proxy endpoint'ов.
* `middlewares(self) -> Sequence[Middleware]`: добавляет Starlette middlewares.
* `template_globals(self) -> dict[str, Any]`: предоставляет глобальные переменные Jinja с префиксом `<name>_`, чтобы исключить коллизии.
* `template_filters(self) -> dict[str, Callable]`: предоставляет фильтры Jinja с таким же префиксом `<name>_`.

### Hook setup

`setup(self, admin: BaseAdmin) -> None` интегрирует ваш плагин с основными реестрами ядра. Используйте его для регистрации конвертеров моделей, фильтров, форматов импорта и экспорта, storage backend'ов и подписчиков событий. Он выполняется после применения декларативных hook'ов.

```python
def setup(self, admin: "BaseAdmin") -> None:
    admin.events.subscribe(MyEventSubscriber(self.config))
```

### Lifecycle hook

`on_mount(self, admin: BaseAdmin) -> None` выполняется ровно один раз, после того как Starlette sub-application собран и смонтирован. Собранное приложение доступно как `admin.app`.

## Шаблоны и переопределения

Шаблоны плагина автоматически включаются в цепочку загрузчиков. Пользователь может переопределить шаблон, разместив файл по соответствующему пути внутри собственного `templates_dir`, который всегда имеет приоритет. Например, чтобы переопределить `plugins/geospatial/fields/form/point.html`, пользователь создаёт файл `templates_dir/plugins/geospatial/fields/form/point.html`.

Чтобы пользовательское переопределение могло безопасно расширять оригинал, каждому плагину назначается префикс `@<name>`, работающий аналогично префиксу `@core`. Переопределение начинается с `{% extends "@geospatial/fields/form/point.html" %}` и расширяет базовый шаблон плагина без рекурсивного включения самого себя.

## Интеграция frontend JavaScript

Плагин, поставляющий кастомные поля, должен упаковывать свои frontend-скрипты в соответствии с контрактом инициализатора полей. Это гарантирует их работу как при полной загрузке страницы, так и при динамической вставке фрагментов.

* **Работайте локально:** выполняйте поиск внутри переданного вам элемента `container`, а не глобального `document`.
* **Будьте идемпотентны:** ядро запускает инициализатор при готовности DOM и повторно всякий раз, когда вставляет inline-строки или фрагменты.
* **Используйте data-атрибуты:** читайте конфигурацию из атрибутов `data-*`, отрендеренных на элементе поля.

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

## Точки расширения через hook setup

Плагины используют существующие публичные реестры, а не отдельный собственный механизм расширений.

* **Конвертеры**: вызывайте `register_converter` из того contrib backend'а, который вы поддерживаете, чтобы сопоставить типы колонок ORM с вашими классами полей. Само поле определите как обычный подкласс `StringField`, хранящий и отображающий геометрии в виде WKT-текста:

  ```python
  from dataclasses import dataclass
  from typing import Any

  from starlette_admin.contrib.sqla.converters import register_converter
  from starlette_admin.fields import StringField


  @dataclass
  class MyGeoField(StringField):
    ...


  @register_converter("Geometry")
  def convert_geometry(*args: Any, **kwargs: Any) -> MyGeoField:
      return MyGeoField(*args, **kwargs)
  ```

* **Фильтры**: вызывайте `register_filters`, чтобы привязать классы фильтров к типу поля.

  ```python
  from starlette_admin.contrib.sqla.filters import register_filters

  register_filters(MyGeoField, WithinBoundingBoxFilter)
  ```

* **Storage**: вызывайте `register_storage`, чтобы предоставить новый backend, например Azure или GCS.

  ```python
  from starlette_admin.storage import register_storage

  register_storage(AzureBlobStorage())
  ```

* **Импортёры и экспортёры**: используйте `register_import_format` и `register_export_format`.

  ```python
  from starlette_admin.export import register_export_format

  register_export_format("pdf", PDFExporter())
  ```

Плагин может поддерживать несколько ORM backend'ов, поэтому импортируйте их условно внутри `setup()`. Благодаря этому плагин продолжит загружаться, даже если пользователь установил только один из них:

```python
def setup(self, admin: "BaseAdmin") -> None:
    try:
        from starlette_admin_geospatial.contrib.sqla import register_sqla_converters

        register_sqla_converters()
    except ImportError:
        pass  # geoalchemy2 or sqlalchemy not installed
```

---

## Что дальше

* **[Кастомные темы](custom-themes.md):** упаковывайте и делитесь полноценными визуальными системами, используя тот же workflow на основе cookiecutter.
* **[События](events.md):** subscriber API, который плагин регистрирует из своего hook'а `setup()`.
* **[Точки расширения](extension-points.md):** все реестры и базовые классы, которые может использовать плагин.
